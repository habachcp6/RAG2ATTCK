"""Behavior-level artifact load regressions, with real FAISS and offline vectors."""

import hashlib
import json
from pathlib import Path

import faiss
import pytest

from src.retrieval.retriever import FAISSRetriever, StubEmbedder


def write_json(path, value):
    path.write_text(json.dumps(value), encoding="utf-8")


@pytest.fixture
def artifacts(tmp_path):
    root = tmp_path / "repository"
    (root / "config").mkdir(parents=True)
    cfg = json.loads(Path("config/retrieval.json").read_text())
    corpus = root / "corpus.jsonl"
    corpus.write_text(json.dumps({"technique_id": "T1059.001", "retrieval_text": "PowerShell"}) + "\n")
    cfg["corpus_sha256"] = hashlib.sha256(corpus.read_bytes()).hexdigest()
    config = root / "config" / "retrieval.json"
    write_json(config, cfg)
    retriever = FAISSRetriever.from_corpus(corpus, config, embedder=StubEmbedder())
    paths = [root / cfg[key] for key in ("faiss_index_path", "document_mapping_path", "manifest_path")]
    retriever.save(*paths)
    return config, cfg, paths


@pytest.mark.parametrize("absolute", [False, True])
def test_saved_loader_ignores_unrelated_cwd(artifacts, tmp_path, monkeypatch, absolute):
    config, cfg, paths = artifacts
    if absolute:
        for key, path in zip(("faiss_index_path", "document_mapping_path", "manifest_path"), paths):
            cfg[key] = str(path)
        write_json(config, cfg)
    monkeypatch.chdir(tmp_path)
    retriever = FAISSRetriever.from_saved(config, embedder=StubEmbedder())
    assert retriever.retrieve("PowerShell", k=1)[0].technique_id == "T1059.001"
    assert Path.cwd() == tmp_path


def test_default_config_ignores_unrelated_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    retriever = FAISSRetriever.from_saved(embedder=StubEmbedder())
    assert retriever.index.ntotal == len(retriever.document_mapping) == 474


@pytest.mark.parametrize("field,value", [
    ("corpus_sha256", "a" * 64),
    ("embedding_model_revision", "a" * 40),
    ("embedding_model_id", "another-model"),
    ("embedding_dimension", 768),
    ("faiss_index_type", "IndexFlatL2"),
    ("normalization", "none"),
    ("similarity_metric", "euclidean"),
])
def test_config_manifest_mismatch_fails_before_embedding(artifacts, monkeypatch, field, value):
    config, cfg, paths = artifacts
    manifest = json.loads(paths[2].read_text())
    manifest[field] = value
    write_json(paths[2], manifest)
    def no_model(**kwargs):
        pytest.fail("Mismatch must be rejected before model initialization")
    monkeypatch.setattr("src.retrieval.retriever.SentenceTransformerEmbedder", no_model)
    with pytest.raises(ValueError, match=f"{field} mismatch"):
        FAISSRetriever.from_saved(config)


@pytest.mark.parametrize("case,message", [
    ("docmap", "index.ntotal/docmap count"),
    ("count", "document_count mismatch"),
    ("dimension", "embedding_dimension mismatch"),
    ("type", "faiss_index_type mismatch"),
])
def test_loaded_artifact_invariants_even_with_valid_hashes(artifacts, case, message):
    config, cfg, paths = artifacts
    index_path, docmap_path, manifest_path = paths
    manifest = json.loads(manifest_path.read_text())
    if case == "docmap":
        write_json(docmap_path, [])
        manifest["document_mapping_sha256"] = hashlib.sha256(docmap_path.read_bytes()).hexdigest()
    elif case == "count":
        manifest["document_count"] = 999
    elif case == "dimension":
        # Keep config and manifest consistent to reach the actual index check.
        cfg["embedding_dimension"] = manifest["embedding_dimension"] = 768
        write_json(config, cfg)
    elif case == "type":
        index = faiss.IndexFlatL2(384)
        index.add(StubEmbedder().encode(["PowerShell"]))
        faiss.write_index(index, str(index_path))
        manifest["index_sha256"] = hashlib.sha256(index_path.read_bytes()).hexdigest()
    write_json(manifest_path, manifest)
    with pytest.raises(ValueError, match=message):
        FAISSRetriever.from_saved(config, embedder=StubEmbedder())


@pytest.mark.parametrize("field", ["embedding_model_revision", "corpus_sha256"])
def test_missing_provenance_field_rejected(artifacts, field):
    config, cfg, paths = artifacts
    del cfg[field]
    write_json(config, cfg)
    with pytest.raises(ValueError, match=field):
        FAISSRetriever.from_saved(config, embedder=StubEmbedder())
