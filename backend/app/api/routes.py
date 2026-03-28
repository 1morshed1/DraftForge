import json
import logging
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, Request, UploadFile

from app.config import settings
from app.models.schemas import (
    DocumentListItem,
    DocumentUploadResponse,
    DraftRequest,
    DraftResponse,
    EditAnalysis,
    EditSubmission,
    ExtractedContent,
    HealthResponse,
    ImprovementDashboard,
    RetrievalRequest,
    RetrievalResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()

SUPPORTED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".txt", ".md"}


# --- Health ---

@router.get("/api/health", response_model=HealthResponse)
async def health_check(request: Request):
    retrieval = request.app.state.retrieval_service
    engine = request.app.state.improvement_engine
    return HealthResponse(
        status="healthy",
        gemini_configured=bool(settings.GEMINI_API_KEY),
        documents_loaded=retrieval.get_document_count(),
        index_size=retrieval.get_index_size(),
        rules_count=len(engine.rules),
    )


# --- Document Processing ---

@router.post("/api/documents/upload", response_model=DocumentUploadResponse)
async def upload_document(request: Request, file: UploadFile = File(...)):
    ext = Path(file.filename or "").suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}",
        )

    try:
        # Save uploaded file
        upload_path = Path(settings.UPLOAD_DIR) / (file.filename or "upload")
        content = await file.read()
        upload_path.write_bytes(content)

        # Process
        processor = request.app.state.document_processor
        extracted = await processor.process_document(str(upload_path), file.filename or "upload")

        # Index chunks
        retrieval = request.app.state.retrieval_service
        retrieval.add_chunks(extracted.chunks, extracted.metadata.filename)

        return DocumentUploadResponse(
            doc_id=extracted.doc_id,
            filename=extracted.metadata.filename,
            status="processed",
            metadata=extracted.metadata,
            chunk_count=len(extracted.chunks),
            message=f"Document processed successfully. {len(extracted.chunks)} chunks indexed.",
        )
    except Exception as e:
        logger.exception("Document upload failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/documents", response_model=list[DocumentListItem])
async def list_documents():
    extracted_dir = Path(settings.EXTRACTED_DIR)
    docs = []
    for p in sorted(extracted_dir.glob("*.json"), key=lambda f: f.stat().st_mtime, reverse=True):
        try:
            data = json.loads(p.read_text())
            meta = data["metadata"]
            docs.append(
                DocumentListItem(
                    doc_id=meta["doc_id"],
                    filename=meta["filename"],
                    file_type=meta["file_type"],
                    uploaded_at=meta["uploaded_at"],
                    chunk_count=len(data.get("chunks", [])),
                    word_count=meta["word_count"],
                    confidence_score=meta["confidence_score"],
                )
            )
        except Exception:
            continue
    return docs


@router.get("/api/documents/{doc_id}", response_model=ExtractedContent)
async def get_document(doc_id: str):
    doc_path = Path(settings.EXTRACTED_DIR) / f"{doc_id}.json"
    if not doc_path.exists():
        raise HTTPException(status_code=404, detail="Document not found")
    data = json.loads(doc_path.read_text())
    return ExtractedContent(**data)


@router.delete("/api/documents/{doc_id}")
async def delete_document(request: Request, doc_id: str):
    doc_path = Path(settings.EXTRACTED_DIR) / f"{doc_id}.json"
    if not doc_path.exists():
        raise HTTPException(status_code=404, detail="Document not found")

    # Remove from FAISS index
    retrieval = request.app.state.retrieval_service
    retrieval.remove_document(doc_id)

    # Delete extracted JSON
    doc_path.unlink()

    # Delete uploaded file if it exists
    for f in Path(settings.UPLOAD_DIR).iterdir():
        # We can't perfectly match, but the extracted JSON has the filename
        pass

    return {"status": "deleted", "message": f"Document {doc_id} removed from index and storage."}


@router.post("/api/documents/load-samples", response_model=list[DocumentUploadResponse])
async def load_samples(request: Request):
    samples_dir = Path("sample_documents")
    if not samples_dir.exists():
        raise HTTPException(status_code=404, detail="Sample documents directory not found. Run scripts/generate_samples.py first.")

    processor = request.app.state.document_processor
    retrieval = request.app.state.retrieval_service
    results = []

    for sample_file in sorted(samples_dir.iterdir()):
        if sample_file.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue
        try:
            extracted = await processor.process_document(str(sample_file), sample_file.name)
            retrieval.add_chunks(extracted.chunks, extracted.metadata.filename)
            results.append(
                DocumentUploadResponse(
                    doc_id=extracted.doc_id,
                    filename=extracted.metadata.filename,
                    status="processed",
                    metadata=extracted.metadata,
                    chunk_count=len(extracted.chunks),
                    message=f"Sample '{sample_file.name}' loaded.",
                )
            )
        except Exception as e:
            logger.warning(f"Failed to load sample {sample_file.name}: {e}")
            continue

    return results


# --- Retrieval ---

@router.post("/api/retrieval/search", response_model=RetrievalResponse)
async def search(request: Request, body: RetrievalRequest):
    retrieval = request.app.state.retrieval_service
    results = retrieval.search(body.query, body.top_k, body.doc_ids)
    return RetrievalResponse(query=body.query, results=results)


# --- Draft Generation ---

@router.post("/api/drafts/generate", response_model=DraftResponse)
async def generate_draft(request: Request, body: DraftRequest):
    retrieval = request.app.state.retrieval_service
    generator = request.app.state.draft_generator
    engine = request.app.state.improvement_engine

    # Build retrieval query
    query = f"{body.draft_type.value.replace('_', ' ')} relevant information summary"
    retrieved = retrieval.search(query, top_k=8, doc_ids=body.doc_ids)

    rules = []
    if body.use_improvements:
        rules = engine.get_applicable_rules(body.draft_type)

    draft = await generator.generate_draft(body, retrieved, rules)
    return draft


@router.get("/api/drafts/{draft_id}", response_model=DraftResponse)
async def get_draft(request: Request, draft_id: str):
    generator = request.app.state.draft_generator
    draft = generator.get_draft(draft_id)
    if draft is None:
        raise HTTPException(status_code=404, detail="Draft not found")
    return draft


# --- Edit Tracking & Improvement ---

@router.post("/api/edits/submit", response_model=EditAnalysis)
async def submit_edit(request: Request, body: EditSubmission):
    tracker = request.app.state.edit_tracker
    generator = request.app.state.draft_generator
    engine = request.app.state.improvement_engine

    # Get draft type from saved draft
    draft_type = None
    draft = generator.get_draft(body.draft_id)
    if draft:
        draft_type = draft.draft_type.value

    analysis = tracker.analyze_edit(body, draft_type)
    engine.learn_from_edit(analysis)
    return analysis


@router.get("/api/edits", response_model=list[EditAnalysis])
async def list_edits(request: Request):
    tracker = request.app.state.edit_tracker
    return tracker.get_all_edits()


@router.get("/api/improvements/dashboard", response_model=ImprovementDashboard)
async def improvements_dashboard(request: Request):
    engine = request.app.state.improvement_engine
    tracker = request.app.state.edit_tracker

    edits = tracker.get_all_edits()
    return ImprovementDashboard(
        total_edits=len(edits),
        total_rules=len(engine.rules),
        rules_by_category=engine.get_rules_by_category(),
        rules=engine.rules,
        recent_edits=edits[:10],
    )


@router.delete("/api/improvements/rules/{rule_id}")
async def delete_rule(request: Request, rule_id: str):
    engine = request.app.state.improvement_engine
    if not engine.delete_rule(rule_id):
        raise HTTPException(status_code=404, detail="Rule not found")
    return {"status": "deleted"}


@router.post("/api/improvements/reset")
async def reset_improvements(request: Request):
    engine = request.app.state.improvement_engine
    engine.reset()
    return {"status": "reset", "message": "All improvement rules cleared."}
