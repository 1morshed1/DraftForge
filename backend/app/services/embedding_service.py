import numpy as np
from sentence_transformers import SentenceTransformer

from app.config import settings


class EmbeddingService:
    def __init__(self):
        self._model = SentenceTransformer(settings.EMBEDDING_MODEL)

    def embed_texts(self, texts: list[str]) -> np.ndarray:
        return self._model.encode(texts, normalize_embeddings=True, batch_size=32)

    def embed_query(self, query: str) -> np.ndarray:
        return self._model.encode([query], normalize_embeddings=True)[0]
