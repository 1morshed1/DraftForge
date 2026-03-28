import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


class Settings:
    def __init__(self):
        # Gemini
        self.GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
        self.GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

        # Embedding
        self.EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
        self.EMBEDDING_DIMENSION: int = 384

        # Storage paths
        base_data = Path(os.getenv("DATA_DIR", "data"))
        self.FAISS_INDEX_DIR: str = str(base_data / "faiss_indexes")
        self.UPLOAD_DIR: str = str(base_data / "uploads")
        self.EXTRACTED_DIR: str = str(base_data / "extracted")
        self.EDITS_DIR: str = str(base_data / "edits")
        self.PATTERNS_DIR: str = str(base_data / "patterns")
        self.DRAFTS_DIR: str = str(base_data / "drafts")

        # Chunking
        self.CHUNK_SIZE: int = 500
        self.CHUNK_OVERLAP: int = 100

        # Retrieval
        self.TOP_K: int = 5

        # Create all directories on startup
        for d in [
            self.FAISS_INDEX_DIR,
            self.UPLOAD_DIR,
            self.EXTRACTED_DIR,
            self.EDITS_DIR,
            self.PATTERNS_DIR,
            self.DRAFTS_DIR,
        ]:
            Path(d).mkdir(parents=True, exist_ok=True)


settings = Settings()
