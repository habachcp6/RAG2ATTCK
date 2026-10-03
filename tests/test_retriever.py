"""
Unit and integration tests for Deterministic FAISS Retriever (Task T18).
Separates fast, 100% offline tests from live-model integration tests.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np
import pytest

from src.retrieval.retriever import (
    FAISSRetriever,
    RetrievalResult,
    SentenceTransformerEmbedder,
    StubEmbedder,
    normalize_l2,
    validate_model_revision,
)


class TestFAISSRetrieverOffline:
    """Offline unit tests requiring 0 internet and 0 external model downloads."""

    def test_config_structure_and_revision_pinning(self):
        config_path = Path("config/retrieval.json")
        assert config_path.exists(), "config/retrieval.json must exist"

        with open(config_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)

        required_keys = [
            "embedding_model_id",
            "embedding_model_revision",
            "embedding_dimension",
            "normalization",
            "faiss_version",
            "corpus_sha256",
            "similarity_metric",
            "faiss_index_type",
            "supported_k",
            "faiss_index_path",
            "document_mapping_path",
            "manifest_path",
        ]
        for key in required_keys:
            assert key in cfg, f"Missing required config key: {key}"

        assert cfg["embedding_model_id"] == "sentence-transformers/all-MiniLM-L6-v2"
        assert cfg["embedding_dimension"] == 384
        assert cfg["normalization"] == "L2"
        assert cfg["similarity_metric"] == "cosine"
        assert cfg["faiss_index_type"] == "IndexFlatIP"
        assert cfg["supported_k"] == [1, 3, 5, 10]
        assert (
            cfg["corpus_sha256"]
            == "b219341154ddf2f12e97d622158a04ab7d57641df6a865559258d365852c3c75"
        )

        revision = cfg["embedding_model_revision"]
        assert re.match(r"^[0-9a-f]{40}$", revision), f"Revision must be 40-char hex: {revision}"
        assert revision not in {"main", "master", "head", None}

        # Test revision validator function
        validate_model_revision(revision)
        for bad_rev in [
            "main",
            "master",
            "1110a24",
            "not-a-hash",
            "",
            "1110a243fdf4706b3f48f1d95db1a4f5529b4d4z",
        ]:
            with pytest.raises(ValueError):
                validate_model_revision(bad_rev)

    def test_stub_embedder_determinism(self):
        embedder = StubEmbedder(dimension=384)
        v1 = embedder.encode(["powershell execution"])
        v2 = embedder.encode(["powershell execution"])
        assert np.allclose(v1, v2)
        assert v1.shape == (1, 384)
        norm = np.linalg.norm(v1)
        assert np.isclose(norm, 1.0, atol=1e-5)

        # Different texts produce different vectors
        v3 = embedder.encode(["different query text"])
        assert not np.allclose(v1, v3)

    def test_l2_normalization_unit_length(self):
        vecs = np.array([[3.0, 4.0], [1.0, -1.0], [0.0, 0.0]], dtype=np.float32)
        normed = normalize_l2(vecs)
        norms = np.linalg.norm(normed, axis=1)
        assert np.isclose(norms[0], 1.0, atol=1e-5)
        assert np.isclose(norms[1], 1.0, atol=1e-5)
        assert np.isfinite(normed).all()

        # 1D vector normalization
        v_1d = np.array([3.0, 4.0], dtype=np.float32)
        normed_1d = normalize_l2(v_1d)
        assert normed_1d.shape == (1, 2)
        assert np.isclose(np.linalg.norm(normed_1d), 1.0, atol=1e-5)

    def test_index_flat_ip_cosine_equivalence(self):
        import faiss

        index = faiss.IndexFlatIP(2)
        doc_vecs = np.array([[1.0, 0.0], [0.0, 1.0]], dtype=np.float32)
        index.add(doc_vecs)

        # Query vector at 45 degrees
        q = np.array([[1.0, 1.0]], dtype=np.float32)
        q_norm = normalize_l2(q)
        distances, indices = index.search(q_norm, 2)

        expected_cos = 1.0 / np.sqrt(2.0)
        assert np.isclose(distances[0][0], expected_cos, atol=1e-5)
        assert np.isclose(distances[0][1], expected_cos, atol=1e-5)

    def test_deterministic_secondary_sort_tie_breaking(self):
        import faiss

        # Create three documents with identical vectors
        docs = [
            {"technique_id": "T1543.003", "name": "Windows Service", "retrieval_text": "text B"},
            {"technique_id": "T1059.001", "name": "PowerShell", "retrieval_text": "text A"},
            {"technique_id": "T1136.001", "name": "Local Account", "retrieval_text": "text C"},
        ]
        index = faiss.IndexFlatIP(4)
        identical_v = np.array(
            [
                [1.0, 0.0, 0.0, 0.0],
                [1.0, 0.0, 0.0, 0.0],
                [1.0, 0.0, 0.0, 0.0],
            ],
            dtype=np.float32,
        )
        index.add(identical_v)

        class FixedEmbedder:
            def encode(self, texts):
                return np.array([[1.0, 0.0, 0.0, 0.0]], dtype=np.float32)

        retriever = FAISSRetriever(
            index=index,
            document_mapping=docs,
            config={"embedding_dimension": 4},
            embedder=FixedEmbedder(),
        )

        results = retriever.retrieve("query", k=3)
        # All scores identical: ties must be broken by ascending technique_id
        # Expected order: T1059.001, T1136.001, T1543.003
        assert [r.technique_id for r in results] == ["T1059.001", "T1136.001", "T1543.003"]
        assert results[0].score == results[1].score == results[2].score

    def test_prefix_consistency_across_k(self):
        import faiss

        docs = [
            {"technique_id": f"T100{i}", "name": f"Name {i}", "retrieval_text": f"Text sample {i}"}
            for i in range(15)
        ]
        embedder = StubEmbedder(dimension=16)
        index = faiss.IndexFlatIP(16)
        vecs = embedder.encode([d["retrieval_text"] for d in docs])
        normed = normalize_l2(vecs)
        index.add(normed)

        retriever = FAISSRetriever(
            index=index,
            document_mapping=docs,
            config={"embedding_dimension": 16},
            embedder=embedder,
        )

        r1 = retriever.retrieve("test query for consistency", k=1)
        r3 = retriever.retrieve("test query for consistency", k=3)
        r5 = retriever.retrieve("test query for consistency", k=5)
        r10 = retriever.retrieve("test query for consistency", k=10)

        assert [r.technique_id for r in r1] == [r.technique_id for r in r3[:1]]
        assert [r.technique_id for r in r3] == [r.technique_id for r in r5[:3]]
        assert [r.technique_id for r in r5] == [r.technique_id for r in r10[:5]]

    def test_k_bounds_and_validation(self):
        docs = [{"technique_id": "T1001", "name": "A", "retrieval_text": "Sample text"}]
        retriever = FAISSRetriever(
            index=None, document_mapping=docs, config={}, embedder=StubEmbedder(4)
        )

        with pytest.raises(ValueError, match="k must be >= 1"):
            retriever.retrieve("query", k=0)

        with pytest.raises(ValueError, match="k must be >= 1"):
            retriever.retrieve("query", k=-5)

    def test_serialization_and_manifest_roundtrip(self, tmp_path):
        import faiss

        docs = [
            {
                "technique_id": "T1059.001",
                "name": "PowerShell",
                "retrieval_text": "PowerShell execution",
            },
            {
                "technique_id": "T1053.005",
                "name": "Scheduled Task",
                "retrieval_text": "Task scheduler",
            },
        ]
        embedder = StubEmbedder(dimension=8)
        vecs = normalize_l2(embedder.encode([d["retrieval_text"] for d in docs]))
        index = faiss.IndexFlatIP(8)
        index.add(vecs)

        config = {
            "corpus_sha256": "dummy_corpus_sha",
            "embedding_dimension": 8,
            "embedding_model_id": "stub-model",
            "embedding_model_revision": "0000000000000000000000000000000000000000",
        }
        retriever = FAISSRetriever(
            index=index, document_mapping=docs, config=config, embedder=embedder
        )

        idx_p = tmp_path / "test.index"
        dmap_p = tmp_path / "test.docmap.json"
        man_p = tmp_path / "test.manifest.json"

        idx_sha, dmap_sha, man_sha = retriever.save(idx_p, dmap_p, man_p)
        assert idx_p.exists()
        assert dmap_p.exists()
        assert man_p.exists()

        loaded = FAISSRetriever.load(idx_p, dmap_p, man_p, embedder=embedder)
        assert loaded.index.ntotal == 2
        assert len(loaded.document_mapping) == 2

        res_orig = retriever.retrieve("PowerShell", k=2)
        res_loaded = loaded.retrieve("PowerShell", k=2)
        assert [r.technique_id for r in res_orig] == [r.technique_id for r in res_loaded]
        assert [r.score for r in res_orig] == [r.score for r in res_loaded]

    def test_from_saved_rejects_corpus_hash_mismatch(self, tmp_path):
        repo_root = Path(__file__).resolve().parents[1]
        config = json.loads((repo_root / "config/retrieval.json").read_text(encoding="utf-8"))

        corpus_path = tmp_path / "enterprise-windows-v19.2.jsonl"
        source_corpus = repo_root / config["corpus_path"]
        corpus_path.write_bytes(source_corpus.read_bytes() + b"\n")
        config["corpus_path"] = str(corpus_path)

        for key in ("faiss_index_path", "document_mapping_path", "manifest_path"):
            config[key] = str((repo_root / config[key]).resolve())

        config_path = tmp_path / "retrieval.json"
        config_path.write_text(json.dumps(config), encoding="utf-8")

        with pytest.raises(ValueError, match="Corpus hash mismatch"):
            FAISSRetriever.from_saved(config_path=config_path, embedder=StubEmbedder(dimension=384))

    def test_manifest_tamper_rejection(self, tmp_path):
        import faiss

        docs = [{"technique_id": "T1001", "name": "A", "retrieval_text": "Sample text"}]
        embedder = StubEmbedder(4)
        index = faiss.IndexFlatIP(4)
        index.add(normalize_l2(embedder.encode(["Sample text"])))

        retriever = FAISSRetriever(
            index=index,
            document_mapping=docs,
            config={"corpus_sha256": "dummy", "embedding_dimension": 4},
            embedder=embedder,
        )

        idx_p = tmp_path / "test.index"
        dmap_p = tmp_path / "test.docmap.json"
        man_p = tmp_path / "test.manifest.json"
        retriever.save(idx_p, dmap_p, man_p)

        # 1. Tamper index file -> reject
        corrupted_idx = bytearray(idx_p.read_bytes())
        corrupted_idx[0] ^= 0xFF
        idx_p.write_bytes(bytes(corrupted_idx))
        with pytest.raises(ValueError, match="Index hash mismatch"):
            FAISSRetriever.load(idx_p, dmap_p, man_p, embedder=embedder)

        # Restore index, tamper docmap -> reject
        retriever.save(idx_p, dmap_p, man_p)
        corrupted_dmap = dmap_p.read_text(encoding="utf-8") + " "
        dmap_p.write_text(corrupted_dmap, encoding="utf-8")
        with pytest.raises(ValueError, match="Docmap hash mismatch"):
            FAISSRetriever.load(idx_p, dmap_p, man_p, embedder=embedder)

        # Missing manifest -> reject
        man_p.unlink()
        with pytest.raises(FileNotFoundError):
            FAISSRetriever.load(idx_p, dmap_p, man_p, embedder=embedder)

    def test_format_retrieved_context_no_leakage(self):
        doc = {
            "technique_id": "T1059.001",
            "name": "PowerShell",
            "retrieval_text": (
                "Technique ID: T1059.001\nName: PowerShell\n"
                "Description: Adversaries execute PowerShell commands."
            ),
        }
        res = [RetrievalResult(technique_id="T1059.001", score=0.8872, document=doc, rank=1)]
        retriever = FAISSRetriever(index=None, document_mapping=[doc], config={})
        formatted = retriever.format_retrieved_context(res)

        assert "Candidate 1: [T1059.001] PowerShell (Similarity Score: 0.8872)" in formatted
        assert "Adversaries execute PowerShell commands." in formatted
        # Strict isolation check: zero evaluation leakage keywords
        for forbidden in ["ground_truth", "technique_label", "expected_technique", "attack_label"]:
            assert forbidden not in formatted.lower()


@pytest.mark.integration
class TestFAISSRetrieverIntegration:
    """Integration tests requiring live model weights and pre-built artifacts."""

    def test_real_sentence_transformer_loads_pinned_revision(self):
        config_path = Path("config/retrieval.json")
        with open(config_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)

        embedder = SentenceTransformerEmbedder(
            model_id=cfg["embedding_model_id"],
            revision=cfg["embedding_model_revision"],
        )
        vec = embedder.encode(["powershell.exe -enc"])
        assert vec.shape == (1, 384)
        assert vec.dtype == np.float32
        norm = np.linalg.norm(vec)
        assert norm > 0.0

    def test_real_index_loading_and_manifest_verification(self):
        retriever = FAISSRetriever.from_saved()
        assert retriever.index.ntotal == 474
        assert len(retriever.document_mapping) == 474

        # Verify manifest recorded properties
        manifest = retriever.config
        assert manifest["embedding_dimension"] == 384
        assert manifest["embedding_model_id"] == "sentence-transformers/all-MiniLM-L6-v2"
        assert manifest["embedding_model_revision"] == "1110a243fdf4706b3f48f1d95db1a4f5529b4d41"
        assert manifest["normalization"] == "L2"
        assert manifest["similarity_metric"] == "cosine"
        assert manifest["faiss_index_type"] == "IndexFlatIP"
        assert manifest["document_count"] == 474

        # Prove real retrieval reaches the shared RAG request and serializable
        # provenance; model generation remains mocked and incurs no API charge.
        from src.rag.pipeline import RAGPipeline
        from tests.test_rag_pipeline import _create_mock_client

        client = _create_mock_client()
        pipeline = RAGPipeline(retriever=retriever, client=client)
        record = pipeline.run_sample("real-retrieval", "powershell.exe -enc SQBFAFgA", k=3)
        assert len(record.retrieval.technique_ids) == 3
        assert record.retrieval.index_sha256 == manifest["index_sha256"]
        prompt = client.client.responses.create.call_args.kwargs["input"]
        for technique_id in record.retrieval.technique_ids:
            assert technique_id in prompt
        assert json.loads(record.to_json())["execution"]["condition"] == "rag"

    def test_real_index_attribution_queries(self):
        retriever = FAISSRetriever.from_saved()

        # Query 1: PowerShell command invocation
        res_ps = retriever.retrieve("powershell.exe -ExecutionPolicy Bypass -enc SQBFAFgA", k=5)
        top_ids_ps = [r.technique_id for r in res_ps]
        assert "T1059.001" in top_ids_ps, (
            f"T1059.001 should be in top-5 for PowerShell, got: {top_ids_ps}"
        )

        # Query 2: Scheduled task creation
        res_sch = retriever.retrieve(
            "schtasks.exe /create /tn MyTask /tr C:\\evil.exe /sc onlogon", k=5
        )
        top_ids_sch = [r.technique_id for r in res_sch]
        assert "T1053.005" in top_ids_sch, (
            f"T1053.005 should be in top-5 for schtasks, got: {top_ids_sch}"
        )

        # Query 3: Account creation
        res_user = retriever.retrieve("net user /add create a local user account", k=5)
        top_ids_user = [r.technique_id for r in res_user]
        assert "T1136.001" in top_ids_user, (
            f"T1136.001 should be in top-5 for net user, got: {top_ids_user}"
        )

        # Query 4: Ingress tool transfer
        res_dl = retriever.retrieve(
            "download tool from remote server ingress tool transfer certutil", k=5
        )
        top_ids_dl = [r.technique_id for r in res_dl]
        assert "T1105" in top_ids_dl, (
            f"T1105 should be in top-5 for certutil download, got: {top_ids_dl}"
        )

    def test_supported_k_depths_on_real_index(self):
        retriever = FAISSRetriever.from_saved()
        query = "cmd.exe /c whoami /priv"

        for k in [1, 3, 5, 10]:
            results = retriever.retrieve(query, k=k)
            assert len(results) == k, f"Expected {k} candidates, got {len(results)}"
            ranks = [r.rank for r in results]
            assert ranks == list(range(1, k + 1))
            scores = [r.score for r in results]
            # Verify descending score order
            assert scores == sorted(scores, reverse=True)

        # Verify prefix consistency on real query
        r1 = retriever.retrieve(query, k=1)
        r3 = retriever.retrieve(query, k=3)
        r5 = retriever.retrieve(query, k=5)
        r10 = retriever.retrieve(query, k=10)

        assert [r.technique_id for r in r1] == [r.technique_id for r in r3[:1]]
        assert [r.technique_id for r in r3] == [r.technique_id for r in r5[:3]]
        assert [r.technique_id for r in r5] == [r.technique_id for r in r10[:5]]

    def test_live_rag_candidates_match_independent_real_retriever(self, tmp_path, monkeypatch):
        """
        Integration test verifying live experiment RAG candidates, ranks, and similarity scores
        equal an independently loaded pinned real retriever for identical endpoint_evidence.
        Verifies query isolation (retriever and embedder spy) and zero real provider calls.
        Runs against real git status on committed clean HEAD.
        """
        from src.experiment.authorization import (
            ExecutionAuthorization,
            ScientificProtocolApproval,
        )
        from src.experiment.config import load_plan
        from src.experiment.runner import MockProvider, MockReply, run_live_experiment

        proto_dict = json.loads(
            Path("config/experiment_protocol_v1.json").read_text(encoding="utf-8")
        )
        proto = ScientificProtocolApproval(**proto_dict)
        plan = load_plan("config/experiment_config.json")
        auth = ExecutionAuthorization(
            human_approval_token="TOKEN_REAL_RETRIEVAL_VERIFY",
            approved_protocol_sha256=proto.protocol_sha256,
            authorized_max_provider_attempts=25600,
            allow_live_dispatch=True,
        )

        sample = plan.samples[0]

        # Spy on retrieval and encoding queries to verify query isolation
        retrieval_queries: list[tuple[str, int]] = []
        orig_retrieve = FAISSRetriever.retrieve

        def spy_retrieve(self, query: str, k: int = 5):
            retrieval_queries.append((query, k))
            return orig_retrieve(self, query, k=k)

        monkeypatch.setattr(FAISSRetriever, "retrieve", spy_retrieve)

        encoded_texts: list[str] = []
        orig_encode = SentenceTransformerEmbedder.encode

        def spy_encode(self, texts: list[str]):
            encoded_texts.extend(texts)
            return orig_encode(self, texts)

        monkeypatch.setattr(SentenceTransformerEmbedder, "encode", spy_encode)

        # Intercepting MockProvider guarantees strictly ZERO real provider calls
        captured_calls = []

        class InterceptingMockProvider(MockProvider):
            def create(self, **kwargs):
                captured_calls.append((self.key, kwargs))
                return super().create(**kwargs)

        mock_responses = {
            (sample.sample_id, cond): [MockReply()]
            for cond in ("no_rag", "rag_k1", "rag_k3", "rag_k5", "rag_k10")
        }
        mock_provider = InterceptingMockProvider(mock_responses)

        out_dir = tmp_path / "live_real_retrieval_verification"

        # Execute run_live_experiment with embedder=None
        # (canonical defaults to real SentenceTransformerEmbedder)
        summary = run_live_experiment(
            plan,
            out_dir,
            authorization=auth,
            protocol=proto,
            provider_factory=lambda cfg, b: mock_provider,
            stop_after=5,
        )

        assert summary["record_count"] == 5
        assert len(captured_calls) == 5

        # Query Isolation verification:
        # 1. Exactly 4 retrieval queries executed (for conditions rag_k1, rag_k3, rag_k5, rag_k10)
        assert len(retrieval_queries) == 4
        for q, _ in retrieval_queries:
            assert q == sample.endpoint_evidence, (
                f"Query '{q}' does not equal endpoint_evidence exactly"
            )

        # 2. Encoded texts: first is canary probe, operational queries equal endpoint_evidence
        assert len(encoded_texts) >= 5
        assert encoded_texts[0] == "attribution canary probe"
        for operational_query in encoded_texts[1:]:
            assert operational_query == sample.endpoint_evidence

        # Independently load real retriever using pinned snapshot artifacts
        independent_retriever = FAISSRetriever.from_saved()

        # Check each RAG depth: rag_k1, rag_k3, rag_k5, rag_k10
        for k in (1, 3, 5, 10):
            cond_file = out_dir / f"rag_k{k}_predictions.jsonl"
            assert cond_file.exists(), f"Missing predictions file: {cond_file}"
            records = [json.loads(line) for line in cond_file.read_bytes().splitlines() if line]
            assert len(records) == 1
            rec = records[0]

            expected_results = independent_retriever.retrieve(sample.endpoint_evidence, k=k)
            retrieved_candidates = rec["retrieved_candidates"]

            assert len(retrieved_candidates) == k
            # Verify candidate technique IDs exactly match
            assert [c["technique_id"] for c in retrieved_candidates] == [
                r.technique_id for r in expected_results
            ]
            # Verify ranks exactly match
            assert [c["rank"] for c in retrieved_candidates] == [r.rank for r in expected_results]
            # Verify similarity scores match within numerical precision
            for c, exp in zip(retrieved_candidates, expected_results, strict=True):
                assert c["score"] == pytest.approx(exp.score, abs=1e-5)

            assert rec["retrieval_k"] == k
            target_key = (sample.sample_id, f"rag_k{k}")
            prompt_input = next(
                call[1]["input"] for call in captured_calls if call[0] == target_key
            )
            assert sample.endpoint_evidence.strip() in prompt_input
