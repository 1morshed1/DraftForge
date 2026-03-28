"""Tests for EmbeddingService and RetrievalService."""

import pytest

from app.models.schemas import TextChunk
from app.services.embedding_service import EmbeddingService
from app.services.retrieval_service import RetrievalService


@pytest.fixture(scope="module")
def embedding_service():
    """Module-scoped to avoid reloading the model per test."""
    return EmbeddingService()


@pytest.fixture
def retrieval_service(embedding_service):
    return RetrievalService(embedding_service)


@pytest.fixture
def loaded_retrieval(retrieval_service):
    """RetrievalService pre-loaded with sample chunks."""
    chunks = [
        TextChunk(chunk_id="c1", doc_id="d1", text="Monthly rent is $2,450 due on the first of each month.",
                  chunk_index=0, start_char=0, end_char=55),
        TextChunk(chunk_id="c2", doc_id="d1", text="Security deposit of $4,900 collected at signing.",
                  chunk_index=1, start_char=55, end_char=103),
        TextChunk(chunk_id="c3", doc_id="d2", text="Patient suffered bowel perforation during appendectomy.",
                  chunk_index=0, start_char=0, end_char=55),
        TextChunk(chunk_id="c4", doc_id="d2", text="Medical expenses totaling $347,892 for extended hospitalization.",
                  chunk_index=1, start_char=55, end_char=118),
    ]
    retrieval_service.add_chunks(chunks, "lease.pdf")
    return retrieval_service


class TestEmbeddingService:
    def test_generates_embeddings(self, embedding_service):
        emb = embedding_service.embed_texts(["Hello world"])
        assert emb.shape == (1, 384)

    def test_batch_embeddings(self, embedding_service):
        texts = ["First text", "Second text", "Third text"]
        emb = embedding_service.embed_texts(texts)
        assert emb.shape == (3, 384)

    def test_similar_texts_closer(self, embedding_service):
        import numpy as np
        embs = embedding_service.embed_texts([
            "monthly rent payment",
            "lease rent amount due",
            "medical surgery complication",
        ])
        # Cosine similarity (already L2-normalized)
        sim_rent = float(np.dot(embs[0], embs[1]))
        sim_cross = float(np.dot(embs[0], embs[2]))
        assert sim_rent > sim_cross


class TestRetrievalService:
    def test_add_chunks_increases_index(self, loaded_retrieval):
        assert loaded_retrieval.index.ntotal == 4

    def test_search_returns_relevant_results(self, loaded_retrieval):
        results = loaded_retrieval.search("rent payment amount", top_k=2)
        assert len(results) > 0
        # Top result should be about rent
        assert "rent" in results[0].text.lower() or "$2,450" in results[0].text

    def test_search_medical_query(self, loaded_retrieval):
        results = loaded_retrieval.search("surgery complications", top_k=2)
        assert len(results) > 0
        top_doc_ids = [r.doc_id for r in results]
        assert "d2" in top_doc_ids

    def test_filter_by_doc_ids(self, loaded_retrieval):
        results = loaded_retrieval.search("money amount", top_k=4, doc_ids=["d1"])
        for r in results:
            assert r.doc_id == "d1"

    def test_top_k_limits_results(self, loaded_retrieval):
        results = loaded_retrieval.search("legal document", top_k=2)
        assert len(results) <= 2

    def test_scores_are_floats(self, loaded_retrieval):
        results = loaded_retrieval.search("rent", top_k=4)
        for r in results:
            assert isinstance(r.score, float)
