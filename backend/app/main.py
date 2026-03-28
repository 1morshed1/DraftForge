from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.services.document_processor import DocumentProcessor
from app.services.draft_generator import DraftGenerator
from app.services.edit_tracker import EditTracker, ImprovementEngine
from app.services.embedding_service import EmbeddingService
from app.services.retrieval_service import RetrievalService


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize services
    embedding_service = EmbeddingService()
    app.state.document_processor = DocumentProcessor()
    app.state.embedding_service = embedding_service
    app.state.retrieval_service = RetrievalService(embedding_service)
    app.state.draft_generator = DraftGenerator()
    app.state.edit_tracker = EditTracker()
    app.state.improvement_engine = ImprovementEngine()
    yield


app = FastAPI(title="DraftForge - Legal Document Processor", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
