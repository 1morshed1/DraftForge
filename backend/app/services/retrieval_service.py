import json
from pathlib import Path

import faiss
import numpy as np

from app.config import settings
from app.models.schemas import RetrievalResult, TextChunk
from app.services.embedding_service import EmbeddingService


class RetrievalService:
    def __init__(self, embedding_service: EmbeddingService):
        self.embedding_service = embedding_service
        self.index_dir = Path(settings.FAISS_INDEX_DIR)
        self.index_path = self.index_dir / "index.faiss"
        self.metadata_path = self.index_dir / "metadata.json"

        self.index: faiss.IndexFlatIP = faiss.IndexFlatIP(settings.EMBEDDING_DIMENSION)
        self.chunk_store: dict[int, dict] = {}
        self.doc_filenames: dict[str, str] = {}

        self._load()

    def _load(self):
        if self.index_path.exists() and self.metadata_path.exists():
            self.index = faiss.read_index(str(self.index_path))
            meta = json.loads(self.metadata_path.read_text())
            # JSON keys are strings, convert back to int
            self.chunk_store = {int(k): v for k, v in meta.get("chunk_store", {}).items()}
            self.doc_filenames = meta.get("doc_filenames", {})

    def _save(self):
        faiss.write_index(self.index, str(self.index_path))
        meta = {
            "chunk_store": {str(k): v for k, v in self.chunk_store.items()},
            "doc_filenames": self.doc_filenames,
        }
        self.metadata_path.write_text(json.dumps(meta, default=str))

    def add_chunks(self, chunks: list[TextChunk], filename: str):
        if not chunks:
            return

        texts = [c.text for c in chunks]
        embeddings = self.embedding_service.embed_texts(texts)
        embeddings = np.array(embeddings, dtype=np.float32)

        start_id = self.index.ntotal
        self.index.add(embeddings)

        for i, chunk in enumerate(chunks):
            faiss_id = start_id + i
            self.chunk_store[faiss_id] = {
                "chunk_id": chunk.chunk_id,
                "doc_id": chunk.doc_id,
                "text": chunk.text,
                "chunk_index": chunk.chunk_index,
                "page_number": chunk.page_number,
            }
            self.doc_filenames[chunk.doc_id] = filename

        self._save()

    def search(
        self,
        query: str,
        top_k: int = 5,
        doc_ids: list[str] | None = None,
    ) -> list[RetrievalResult]:
        if self.index.ntotal == 0:
            return []

        query_vec = self.embedding_service.embed_query(query)
        query_vec = np.array([query_vec], dtype=np.float32)

        search_k = top_k * 3 if doc_ids else top_k
        search_k = min(search_k, self.index.ntotal)

        scores, indices = self.index.search(query_vec, search_k)

        results: list[RetrievalResult] = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:
                continue
            meta = self.chunk_store.get(int(idx))
            if meta is None:
                continue
            if doc_ids and meta["doc_id"] not in doc_ids:
                continue

            results.append(
                RetrievalResult(
                    chunk_id=meta["chunk_id"],
                    doc_id=meta["doc_id"],
                    text=meta["text"],
                    score=float(score),
                    page_number=meta.get("page_number"),
                    filename=self.doc_filenames.get(meta["doc_id"], ""),
                )
            )
            if len(results) >= top_k:
                break

        return results

    def remove_document(self, doc_id: str):
        # Filter out chunks belonging to this document
        remaining = {
            k: v for k, v in self.chunk_store.items() if v["doc_id"] != doc_id
        }

        if doc_id in self.doc_filenames:
            del self.doc_filenames[doc_id]

        # Rebuild index from remaining chunks
        self.index = faiss.IndexFlatIP(settings.EMBEDDING_DIMENSION)
        new_store: dict[int, dict] = {}

        if remaining:
            texts = [v["text"] for v in remaining.values()]
            embeddings = self.embedding_service.embed_texts(texts)
            embeddings = np.array(embeddings, dtype=np.float32)
            self.index.add(embeddings)

            for i, (_, meta) in enumerate(remaining.items()):
                new_store[i] = meta

        self.chunk_store = new_store
        self._save()

    def clear(self):
        self.index = faiss.IndexFlatIP(settings.EMBEDDING_DIMENSION)
        self.chunk_store = {}
        self.doc_filenames = {}
        self._save()

    def get_index_size(self) -> int:
        return self.index.ntotal

    def get_document_count(self) -> int:
        doc_ids = {v["doc_id"] for v in self.chunk_store.values()}
        return len(doc_ids)
