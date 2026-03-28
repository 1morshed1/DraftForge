import json
import uuid
from datetime import datetime
from pathlib import Path

from app.config import settings
from app.models.schemas import (
    Citation,
    DraftRequest,
    DraftResponse,
    DraftType,
    ImprovementRule,
    RetrievalResult,
)

DRAFT_PROMPTS: dict[DraftType, str] = {
    DraftType.CASE_SUMMARY: """You are a legal analyst at a law firm preparing a case summary.
Structure your output as:
1. **Case Overview** - Brief description of the case
2. **Key Facts** - Numbered list of critical facts
3. **Legal Issues** - Legal questions at stake
4. **Current Status** - Where the case stands

Rules:
- Only include information supported by the source documents.
- Use [Source N] references to cite specific documents.
- If information is unclear, note this explicitly.
- Do not make assumptions beyond what the documents state.""",

    DraftType.TITLE_REVIEW: """You are a real estate attorney conducting a title review.
Structure your output as:
1. **Property Identification** - Address, parcel number, legal description
2. **Chain of Title** - Ownership history from sources
3. **Encumbrances** - Liens, easements, restrictions found
4. **Issues Identified** - Problems or gaps
5. **Recommendations** - Next steps

Rules:
- Only include information supported by the source documents.
- Use [Source N] references to cite specific documents.
- If information is unclear, note this explicitly.
- Do not make assumptions beyond what the documents state.""",

    DraftType.NOTICE_SUMMARY: """You are a legal assistant summarizing a legal notice.
Structure your output as:
1. **Notice Type** - What kind of notice this is
2. **Parties Involved** - Who sent it, who received it
3. **Key Dates** - All relevant deadlines and dates
4. **Required Actions** - What must be done
5. **Compliance Notes** - Requirements and consequences

Rules:
- Only include information supported by the source documents.
- Use [Source N] references to cite specific documents.
- If information is unclear, note this explicitly.
- Do not make assumptions beyond what the documents state.""",

    DraftType.DOCUMENT_CHECKLIST: """You are a paralegal preparing a document checklist.
Structure your output as:
1. **Documents Present** - What we have
2. **Documents Referenced** - Mentioned but not provided
3. **Documents Potentially Needed** - Based on case type
4. **Completeness Assessment** - Overall readiness

Rules:
- Only include information supported by the source documents.
- Use [Source N] references to cite specific documents.
- If information is unclear, note this explicitly.
- Do not make assumptions beyond what the documents state.""",

    DraftType.INTERNAL_MEMO: """You are a junior associate drafting an internal memo.
Structure your output as:
**TO:** [Senior Partner]
**FROM:** [Associate]
**DATE:** [Today]
**RE:** [Subject from documents]

1. **Summary** - Executive summary
2. **Background** - Relevant context
3. **Analysis** - Legal analysis of the issues
4. **Recommendations** - Suggested course of action
5. **Open Questions** - Items needing further research

Rules:
- Only include information supported by the source documents.
- Use [Source N] references to cite specific documents.
- If information is unclear, note this explicitly.
- Do not make assumptions beyond what the documents state.""",
}


class DraftGenerator:
    def __init__(self):
        self.drafts_dir = Path(settings.DRAFTS_DIR)
        self._model = None

        if settings.GEMINI_API_KEY:
            try:
                import google.generativeai as genai

                genai.configure(api_key=settings.GEMINI_API_KEY)
                self._model = genai.GenerativeModel(settings.GEMINI_MODEL)
            except Exception:
                self._model = None

    async def generate_draft(
        self,
        request: DraftRequest,
        retrieved_chunks: list[RetrievalResult],
        improvement_rules: list[ImprovementRule] | None = None,
    ) -> DraftResponse:
        draft_id = str(uuid.uuid4())

        # Build context from retrieved chunks
        context_parts = []
        citations = []
        for i, chunk in enumerate(retrieved_chunks, 1):
            context_parts.append(
                f"[Source {i}] (from: {chunk.filename}, relevance: {chunk.score:.2f})\n{chunk.text}\n---"
            )
            citations.append(
                Citation(
                    chunk_id=chunk.chunk_id,
                    doc_id=chunk.doc_id,
                    text_snippet=chunk.text[:200],
                    relevance_score=chunk.score,
                    filename=chunk.filename,
                )
            )

        context = "\n\n".join(context_parts)

        # Build prompt
        system_prompt = DRAFT_PROMPTS.get(
            request.draft_type, DRAFT_PROMPTS[DraftType.CASE_SUMMARY]
        )

        rules_applied: list[str] = []
        if request.use_improvements and improvement_rules:
            rules_text = self._format_improvement_rules(improvement_rules)
            system_prompt += f"\n\nADDITIONAL GUIDELINES (learned from previous edits):\n{rules_text}"
            rules_applied = [r.rule_id for r in improvement_rules]

        if request.custom_instructions:
            system_prompt += f"\n\nADDITIONAL INSTRUCTIONS:\n{request.custom_instructions}"

        user_prompt = f"Based on the following source documents, generate a {request.draft_type.value.replace('_', ' ')}.\n\nSOURCE DOCUMENTS:\n{context}"

        # Generate
        if self._model is not None:
            try:
                response = self._model.generate_content(
                    f"{system_prompt}\n\n{user_prompt}",
                    generation_config={
                        "temperature": 0.3,
                        "max_output_tokens": 4096,
                    },
                )
                content = response.text
            except Exception as e:
                content = (
                    f"**Draft generation failed:** {str(e)}\n\n"
                    f"**Retrieved context ({len(retrieved_chunks)} sources) is shown below:**\n\n{context}"
                )
        else:
            content = (
                "**Gemini API not configured.** Set GEMINI_API_KEY in your environment.\n\n"
                f"**Retrieved context ({len(retrieved_chunks)} sources) is shown below "
                "to demonstrate retrieval is working:**\n\n" + context
            )

        draft = DraftResponse(
            draft_id=draft_id,
            draft_type=request.draft_type,
            content=content,
            citations=citations,
            generated_at=datetime.utcnow(),
            improvement_rules_applied=rules_applied,
        )

        # Save draft to disk
        draft_path = self.drafts_dir / f"{draft_id}.json"
        draft_path.write_text(draft.model_dump_json(indent=2))

        return draft

    def get_draft(self, draft_id: str) -> DraftResponse | None:
        draft_path = self.drafts_dir / f"{draft_id}.json"
        if not draft_path.exists():
            return None
        data = json.loads(draft_path.read_text())
        return DraftResponse(**data)

    def _format_improvement_rules(self, rules: list[ImprovementRule]) -> str:
        lines = []
        for i, rule in enumerate(rules, 1):
            lines.append(f"{i}. [{rule.category.value}] {rule.rule_text}")
            if rule.examples:
                ex = rule.examples[0]
                before = ex.get("before", "")[:80]
                after = ex.get("after", "")[:80]
                if before and after:
                    lines.append(f"   Example: '{before}' → '{after}'")
        return "\n".join(lines)
