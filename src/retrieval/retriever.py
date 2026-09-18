"""
RAG2ATTCK - Deterministic FAISS Retriever with Pinned Embeddings (Task T18)
Provides deterministic vector indexing and retrieval over the Windows ATT&CK v19.2 corpus.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Protocol, Tuple, Union

import numpy as np

# Ensure HF symlink warnings are suppressed on Windows without Developer Mode
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[2] / "config" / "retrieval.json"
HEX_40_PATTERN = re.compile(r"^[0-9a-f]{40}$", re.IGNORECASE)


def validate_model_revision(revision: str) -> None:
    """Validates that the revision is an exact 40-character hex commit SHA."""
    if not isinstance(revision, str) or not HEX_40_PATTERN.match(revision.strip()):
        raise ValueError(
            f"Invalid model revision: {revision!r}. Must be a 40-character hex commit SHA, "
            "not null, 'main', or 'master'."
        )


class Embedder(Protocol):
    """Protocol for text embedding generation."""

    def encode(self, texts: List[str]) -> np.ndarray:
        ...


class SentenceTransformerEmbedder:
    """Wrapper around SentenceTransformer with revision pinning."""

    def __init__(self, model_id: str, revision: str) -> None:
        validate_model_revision(revision)
        from sentence_transformers import SentenceTransformer

        self.model_id = model_id
        self.revision = revision
        self._model = SentenceTransformer(model_id, revision=revision)

    def encode(self, texts: List[str]) -> np.ndarray:
        embeddings = self._model.encode(
            texts,
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=False,
        )
        return np.asarray(embeddings, dtype=np.float32)


class StubEmbedder:
    """
    Deterministic stub embedder for 100% offline unit tests.
    Generates deterministic pseudo-random unit vectors seeded by text SHA-256.
    """

    def __init__(self, dimension: int = 384) -> None:
        self.dimension = dimension

    def encode(self, texts: List[str]) -> np.ndarray:
        vectors = []
        for text in texts:
            seed = int(hashlib.sha256(text.encode("utf-8")).hexdigest()[:8], 16)
            rng = np.random.RandomState(seed)
            v = rng.randn(self.dimension).astype(np.float32)
            norm = float(np.linalg.norm(v))
            vectors.append(v / (norm if norm > 1e-12 else 1.0))
        return np.array(vectors, dtype=np.float32)


@dataclass(frozen=True)
class RetrievalResult:
    """Single retrieved technique candidate."""

    technique_id: str
    score: float
    document: Dict[str, Any]
    rank: int

    @property
    def name(self) -> str:
        return self.document.get("name", "")


def normalize_l2(vectors: np.ndarray) -> np.ndarray:
    """
    Applies L2 normalization to vectors.
    Guarantees unit norm: ||v||_2 = 1.0.
    """
    vecs = np.asarray(vectors, dtype=np.float32)
    if vecs.ndim == 1:
        vecs = vecs.reshape(1, -1)
    norms = np.linalg.norm(vecs, axis=1, keepdims=True)
    norms = np.where(norms < 1e-12, 1.0, norms)
    return (vecs / norms).astype(np.float32)


class FAISSRetriever:
    """
    Deterministic FAISS IndexFlatIP retriever over ATT&CK corpus.
    Uses L2 normalization to compute exact cosine similarity via inner product.
    """

    def __init__(
        self,
        index: Any,
        document_mapping: List[Dict[str, Any]],
        config: Dict[str, Any],
        embedder: Optional[Embedder] = None,
    ) -> None:
        self.index = index
        self.document_mapping = document_mapping
        self.config = config
        self.embedder = embedder

    @classmethod
    def from_corpus(
        cls,
        corpus_path: Union[str, Path],
        config_path: Union[str, Path] = DEFAULT_CONFIG_PATH,
        embedder: Optional[Embedder] = None,
    ) -> FAISSRetriever:
        """Builds an in-memory retriever directly from corpus JSONL."""
        import faiss

        c_path = Path(corpus_path)
        cfg_path = Path(config_path)

        with open(cfg_path, "r", encoding="utf-8") as f:
            config = json.load(f)

        corpus_bytes = c_path.read_bytes()
        actual_sha = hashlib.sha256(corpus_bytes).hexdigest()
        expected_sha = config.get("corpus_sha256")
        if expected_sha and actual_sha != expected_sha:
            raise ValueError(
                f"Corpus SHA256 mismatch! Expected {expected_sha}, got {actual_sha}"
            )

        documents: List[Dict[str, Any]] = []
        retrieval_texts: List[str] = []
        with open(c_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                doc = json.loads(line)
                documents.append(doc)
                retrieval_texts.append(doc["retrieval_text"])

        if embedder is None:
            model_id = config["embedding_model_id"]
            revision = config["embedding_model_revision"]
            embedder = SentenceTransformerEmbedder(
                model_id=model_id,
                revision=revision,
            )

        raw_vectors = embedder.encode(retrieval_texts)
        expected_dim = config.get("embedding_dimension", 384)
        if raw_vectors.shape[1] != expected_dim:
            raise ValueError(
                f"Embedding dimension mismatch: expected {expected_dim}, "
                f"got {raw_vectors.shape[1]}"
            )

        norm_vectors = normalize_l2(raw_vectors).astype(np.float32)

        index = faiss.IndexFlatIP(expected_dim)
        index.add(norm_vectors)

        return cls(
            index=index,
            document_mapping=documents,
            config=config,
            embedder=embedder,
        )

    def retrieve(self, query: str, k: int = 5) -> List[RetrievalResult]:
        """
        Executes deterministic top-k retrieval with secondary sort tie-breaking.
        1. Query -> embed -> L2 normalize
        2. FAISS IndexFlatIP.search(q, n=ntotal) -> score all documents
        3. Stable sort: (-score, technique_id)
        4. Slicing: [:k]
        """
        if k < 1:
            raise ValueError(f"k must be >= 1, got {k}")
        if self.embedder is None:
            raise RuntimeError("Retriever initialized without an embedder.")

        query_vec = self.embedder.encode([query])
        norm_query_vec = normalize_l2(query_vec).astype(np.float32)

        ntotal = self.index.ntotal
        if ntotal == 0:
            return []

        # FAISS search across all candidates for deterministic global tie-breaking
        distances, indices = self.index.search(norm_query_vec, ntotal)

        candidates = []
        for score, idx in zip(distances[0], indices[0]):
            if idx < 0 or idx >= len(self.document_mapping):
                continue
            doc = self.document_mapping[idx]
            candidates.append((float(score), doc["technique_id"], doc))

        # Stable sort: primary -score (descending), secondary technique_id (ascending)
        candidates.sort(key=lambda item: (-item[0], item[1]))

        top_k = candidates[:k]
        return [
            RetrievalResult(
                technique_id=item[1],
                score=item[0],
                document=item[2],
                rank=i + 1,
            )
            for i, item in enumerate(top_k)
        ]

    def format_retrieved_context(self, results: List[RetrievalResult]) -> str:
        """
        Deterministically formats retrieval results for prompt injection.
        Zero evaluation labels are included.
        """
        sections = []
        for res in results:
            doc = res.document
            technique_id = res.technique_id
            name = res.name
            score = res.score
            retrieval_text = doc.get("retrieval_text", "")
            header = f"Candidate {res.rank}: [{technique_id}] {name} (Similarity Score: {score:.4f})"
            sections.append(f"{header}\n{retrieval_text}")
        return "\n\n---\n\n".join(sections)

    def save(
        self,
        index_path: Union[str, Path],
        docmap_path: Union[str, Path],
        manifest_path: Union[str, Path],
    ) -> Tuple[str, str, str]:
        """
        Serializes index binary, document mapping, and manifest.
        Returns (index_sha256, docmap_sha256, manifest_sha256).
        """
        import faiss

        idx_p = Path(index_path)
        dmap_p = Path(docmap_path)
        man_p = Path(manifest_path)

        idx_p.parent.mkdir(parents=True, exist_ok=True)
        dmap_p.parent.mkdir(parents=True, exist_ok=True)
        man_p.parent.mkdir(parents=True, exist_ok=True)

        faiss.write_index(self.index, str(idx_p))
        idx_bytes = idx_p.read_bytes()
        idx_sha = hashlib.sha256(idx_bytes).hexdigest()

        with open(dmap_p, "w", encoding="utf-8", newline="\n") as f:
            json.dump(self.document_mapping, f, indent=2, sort_keys=True, ensure_ascii=False)
            f.write("\n")
        dmap_bytes = dmap_p.read_bytes()
        dmap_sha = hashlib.sha256(dmap_bytes).hexdigest()

        manifest_data = {
            "schema_version": "1.0.0",
            "corpus_sha256": self.config.get("corpus_sha256"),
            "document_count": len(self.document_mapping),
            "document_mapping_file": str(dmap_p.as_posix()),
            "document_mapping_sha256": dmap_sha,
            "embedding_dimension": self.config.get("embedding_dimension", 384),
            "embedding_model_id": self.config.get("embedding_model_id"),
            "embedding_model_revision": self.config.get("embedding_model_revision"),
            "faiss_index_file": str(idx_p.as_posix()),
            "faiss_index_type": "IndexFlatIP",
            "faiss_version": getattr(faiss, "__version__", "1.15.1"),
            "index_sha256": idx_sha,
            "normalization": "L2",
            "similarity_metric": "cosine",
        }

        with open(man_p, "w", encoding="utf-8", newline="\n") as f:
            json.dump(manifest_data, f, indent=2, sort_keys=True, ensure_ascii=False)
            f.write("\n")

        man_sha = hashlib.sha256(man_p.read_bytes()).hexdigest()
        return idx_sha, dmap_sha, man_sha

    @classmethod
    def load(
        cls,
        index_path: Union[str, Path],
        docmap_path: Union[str, Path],
        manifest_path: Union[str, Path],
        embedder: Optional[Embedder] = None,
        expected_config: Optional[Dict[str, Any]] = None,
    ) -> FAISSRetriever:
        """Loads serialized retriever after verifying SHA-256 integrity."""
        import faiss

        idx_p = Path(index_path)
        dmap_p = Path(docmap_path)
        man_p = Path(manifest_path)

        if not man_p.exists():
            raise FileNotFoundError(f"Manifest not found: {man_p}")
        with open(man_p, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        if expected_config is not None:
            for field in (
                "corpus_sha256", "embedding_model_id", "embedding_model_revision",
                "embedding_dimension", "faiss_index_type", "normalization",
                "similarity_metric", "faiss_version",
            ):
                if field not in expected_config or field not in manifest:
                    raise ValueError(f"Missing required config/manifest field: {field}")
                if expected_config[field] != manifest[field]:
                    raise ValueError(
                        f"{field} mismatch: config={expected_config[field]!r} "
                        f"manifest={manifest[field]!r}"
                    )

        if not idx_p.exists():
            raise FileNotFoundError(f"Index file not found: {idx_p}")
        idx_bytes = idx_p.read_bytes()
        idx_sha = hashlib.sha256(idx_bytes).hexdigest()
        if idx_sha != manifest["index_sha256"]:
            raise ValueError(
                f"Index hash mismatch! Expected {manifest['index_sha256']}, got {idx_sha}"
            )

        if not dmap_p.exists():
            raise FileNotFoundError(f"Docmap file not found: {dmap_p}")
        dmap_bytes = dmap_p.read_bytes()
        dmap_sha = hashlib.sha256(dmap_bytes).hexdigest()
        if dmap_sha != manifest["document_mapping_sha256"]:
            raise ValueError(
                f"Docmap hash mismatch! Expected {manifest['document_mapping_sha256']}, got {dmap_sha}"
            )

        index = faiss.read_index(str(idx_p))
        with open(dmap_p, "r", encoding="utf-8") as f:
            docmap = json.load(f)

        if not isinstance(docmap, list):
            raise ValueError("docmap must be a list of documents")
        if index.ntotal != len(docmap):
            raise ValueError(f"index.ntotal/docmap count mismatch: index={index.ntotal} docmap={len(docmap)}")
        if len(docmap) != manifest.get("document_count"):
            raise ValueError(f"document_count mismatch: docmap={len(docmap)} manifest={manifest.get('document_count')!r}")
        if index.d != manifest.get("embedding_dimension"):
            raise ValueError(f"embedding_dimension mismatch: index={index.d} manifest={manifest.get('embedding_dimension')!r}")
        if manifest.get("faiss_index_type") != "IndexFlatIP" or not isinstance(index, faiss.IndexFlatIP):
            raise ValueError(f"faiss_index_type mismatch: index={type(index).__name__} manifest={manifest.get('faiss_index_type')!r}; required IndexFlatIP")
        if index.metric_type != faiss.METRIC_INNER_PRODUCT:
            raise ValueError("FAISS metric mismatch: required inner product")
        if manifest.get("normalization") != "L2" or manifest.get("similarity_metric") != "cosine":
            raise ValueError("normalization/similarity_metric mismatch: required L2/cosine")

        if embedder is None and manifest.get("embedding_model_id") and manifest.get("embedding_model_revision"):
            embedder = SentenceTransformerEmbedder(
                model_id=manifest["embedding_model_id"],
                revision=manifest["embedding_model_revision"],
            )

        return cls(
            index=index,
            document_mapping=docmap,
            config=manifest,
            embedder=embedder,
        )

    @classmethod
    def from_saved(
        cls,
        config_path: Union[str, Path] = DEFAULT_CONFIG_PATH,
        embedder: Optional[Embedder] = None,
    ) -> FAISSRetriever:
        """Loads pre-built index and mapping using paths defined in configuration."""
        cfg_p = Path(config_path).resolve()
        with open(cfg_p, "r", encoding="utf-8") as f:
            cfg = json.load(f)

        # Canonical config/ entries are repository-relative; standalone configs
        # resolve against their own directory. Explicit absolute paths stay absolute.
        root = cfg_p.parent.parent if cfg_p.parent.name == "config" else cfg_p.parent

        def artifact_path(key: str) -> Path:
            path = Path(cfg[key])
            return (path if path.is_absolute() else root / path).resolve()

        return cls.load(
            index_path=artifact_path("faiss_index_path"),
            docmap_path=artifact_path("document_mapping_path"),
            manifest_path=artifact_path("manifest_path"),
            embedder=embedder,
            expected_config=cfg,
        )


def main():
    parser = argparse.ArgumentParser(description="Build and verify deterministic FAISS retrieval index.")
    parser.add_argument("--build-index", action="store_true", default=False, help="Build and serialize the FAISS index")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH, help="Path to retrieval configuration JSON")
    parser.add_argument("--corpus", type=Path, default=None, help="Path to corpus JSONL (overrides config)")
    parser.add_argument("--out-dir", type=Path, default=Path("attack/index"), help="Output directory for index artifacts")
    args = parser.parse_args()

    with open(args.config, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    corpus_path = args.corpus or Path(cfg.get("corpus_path", "attack/corpus/enterprise-windows-v19.2.jsonl"))
    out_dir = args.out_dir
    index_path = out_dir / "enterprise-windows-v19.2.index"
    docmap_path = out_dir / "enterprise-windows-v19.2.docmap.json"
    manifest_path = out_dir / "enterprise-windows-v19.2.manifest.json"

    print(f"[*] Building FAISS retriever from {corpus_path}...")
    retriever = FAISSRetriever.from_corpus(corpus_path, args.config)
    idx_sha, dmap_sha, man_sha = retriever.save(index_path, docmap_path, manifest_path)
    print(f"[+] Index built and saved successfully:")
    print(f"    Index:    {index_path} (SHA: {idx_sha})")
    print(f"    Docmap:   {docmap_path} (SHA: {dmap_sha})")
    print(f"    Manifest: {manifest_path} (SHA: {man_sha})")


if __name__ == "__main__":
    main()
