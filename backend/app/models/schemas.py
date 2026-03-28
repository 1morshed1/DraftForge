from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# --- Enums ---

class DraftType(str, Enum):
    CASE_SUMMARY = "case_summary"
    TITLE_REVIEW = "title_review"
    NOTICE_SUMMARY = "notice_summary"
    DOCUMENT_CHECKLIST = "document_checklist"
    INTERNAL_MEMO = "internal_memo"


class EditCategory(str, Enum):
    STRUCTURAL = "structural"
    TONE = "tone"
    FACTUAL_CORRECTION = "factual_correction"
    ADDITION = "addition"
    DELETION = "deletion"
    FORMATTING = "formatting"
    LEGAL_PRECISION = "legal_precision"


# --- Document Processing Models ---

class DocumentMetadata(BaseModel):
    doc_id: str
    filename: str
    file_type: str
    page_count: int
    extraction_method: str
    confidence_score: float
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    char_count: int
    word_count: int


class TextChunk(BaseModel):
    chunk_id: str
    doc_id: str
    text: str
    chunk_index: int
    start_char: int
    end_char: int
    page_number: Optional[int] = None


class ExtractedContent(BaseModel):
    doc_id: str
    raw_text: str
    cleaned_text: str
    metadata: DocumentMetadata
    structured_data: dict = Field(default_factory=dict)
    chunks: list[TextChunk] = Field(default_factory=list)


class DocumentUploadResponse(BaseModel):
    doc_id: str
    filename: str
    status: str
    metadata: DocumentMetadata
    chunk_count: int
    message: str


class DocumentListItem(BaseModel):
    doc_id: str
    filename: str
    file_type: str
    uploaded_at: datetime
    chunk_count: int
    word_count: int
    confidence_score: float


# --- Retrieval Models ---

class RetrievalResult(BaseModel):
    chunk_id: str
    doc_id: str
    text: str
    score: float
    page_number: Optional[int] = None
    filename: str = ""


class RetrievalRequest(BaseModel):
    query: str
    top_k: int = 5
    doc_ids: Optional[list[str]] = None


class RetrievalResponse(BaseModel):
    query: str
    results: list[RetrievalResult]


# --- Draft Generation Models ---

class DraftRequest(BaseModel):
    draft_type: DraftType
    doc_ids: Optional[list[str]] = None
    custom_instructions: Optional[str] = None
    use_improvements: bool = True


class Citation(BaseModel):
    chunk_id: str
    doc_id: str
    text_snippet: str
    relevance_score: float
    filename: str = ""


class DraftResponse(BaseModel):
    draft_id: str
    draft_type: DraftType
    content: str
    citations: list[Citation] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    improvement_rules_applied: list[str] = Field(default_factory=list)


# --- Edit & Improvement Models ---

class EditSubmission(BaseModel):
    draft_id: str
    original_content: str
    edited_content: str
    editor_notes: Optional[str] = None


class EditDiff(BaseModel):
    edit_type: EditCategory
    original_segment: str
    edited_segment: str
    context: str = ""
    explanation: str = ""


class EditAnalysis(BaseModel):
    edit_id: str
    draft_id: str
    draft_type: Optional[DraftType] = None
    diffs: list[EditDiff] = Field(default_factory=list)
    summary: str = ""
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)


class ImprovementRule(BaseModel):
    rule_id: str
    draft_type: Optional[DraftType] = None
    category: EditCategory
    rule_text: str
    examples: list[dict] = Field(default_factory=list)
    confidence: float = 0.5
    times_applied: int = 1
    created_from_edit_ids: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ImprovementDashboard(BaseModel):
    total_edits: int
    total_rules: int
    rules_by_category: dict[str, int] = Field(default_factory=dict)
    rules: list[ImprovementRule] = Field(default_factory=list)
    recent_edits: list[EditAnalysis] = Field(default_factory=list)


# --- Health Check ---

class HealthResponse(BaseModel):
    status: str
    gemini_configured: bool
    documents_loaded: int
    index_size: int
    rules_count: int
