import hashlib
import json
import uuid
from datetime import datetime
from pathlib import Path

import fitz  # PyMuPDF
import pytesseract
from PIL import Image

from app.config import settings
from app.models.schemas import DocumentMetadata, ExtractedContent, TextChunk
from app.utils.text_utils import clean_text, extract_structured_data

SUPPORTED_TYPES = {".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".txt", ".md"}


class DocumentProcessor:
    def __init__(self):
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.extracted_dir = Path(settings.EXTRACTED_DIR)

    async def process_document(
        self, file_path: str, original_filename: str
    ) -> ExtractedContent:
        path = Path(file_path)
        ext = path.suffix.lower()

        # Generate stable doc_id
        file_bytes = path.read_bytes()
        hash_part = hashlib.md5(file_bytes).hexdigest()[:12]
        uuid_part = uuid.uuid4().hex[:8]
        doc_id = f"{hash_part}_{uuid_part}"

        # Route to extraction method
        if ext == ".pdf":
            raw_text, page_count, method, confidence = self._process_pdf(path)
        elif ext in {".png", ".jpg", ".jpeg", ".tiff", ".bmp"}:
            raw_text, page_count, method, confidence = self._process_image(path)
        elif ext in {".txt", ".md"}:
            raw_text = path.read_text(encoding="utf-8", errors="replace")
            page_count = 1
            method = "direct_read"
            confidence = 1.0
        else:
            raise ValueError(f"Unsupported file type: {ext}")

        cleaned = clean_text(raw_text)
        structured = extract_structured_data(cleaned)
        chunks = self._chunk_text(cleaned, doc_id)

        metadata = DocumentMetadata(
            doc_id=doc_id,
            filename=original_filename,
            file_type=ext,
            page_count=page_count,
            extraction_method=method,
            confidence_score=confidence,
            uploaded_at=datetime.utcnow(),
            char_count=len(cleaned),
            word_count=len(cleaned.split()),
        )

        result = ExtractedContent(
            doc_id=doc_id,
            raw_text=raw_text,
            cleaned_text=cleaned,
            metadata=metadata,
            structured_data=structured,
            chunks=chunks,
        )

        # Persist
        out_path = self.extracted_dir / f"{doc_id}.json"
        out_path.write_text(result.model_dump_json(indent=2))

        return result

    def _process_pdf(
        self, path: Path
    ) -> tuple[str, int, str, float]:
        doc = fitz.open(str(path))
        pages_text = []
        text_pages = 0
        ocr_pages = 0
        total_confidence = 0.0

        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text("text").strip()

            if len(text) > 50:
                pages_text.append(f"[Page {page_num + 1}]\n{text}")
                text_pages += 1
                total_confidence += 0.95
            else:
                # Fallback to OCR
                pix = page.get_pixmap(dpi=300)
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                ocr_text = pytesseract.image_to_string(img)

                # Get per-word confidence
                try:
                    ocr_data = pytesseract.image_to_data(
                        img, output_type=pytesseract.Output.DICT
                    )
                    confidences = [
                        int(c)
                        for c in ocr_data["conf"]
                        if str(c).isdigit() and int(c) > 0
                    ]
                    page_conf = sum(confidences) / len(confidences) / 100.0 if confidences else 0.5
                except Exception:
                    page_conf = 0.5

                pages_text.append(f"[Page {page_num + 1}] [OCR]\n{ocr_text}")
                ocr_pages += 1
                total_confidence += page_conf

        doc.close()

        page_count = text_pages + ocr_pages
        avg_confidence = total_confidence / page_count if page_count > 0 else 0.0

        if ocr_pages == 0:
            method = "text_extraction"
        elif text_pages == 0:
            method = "ocr"
        else:
            method = f"hybrid (text: {text_pages} pages, OCR: {ocr_pages} pages)"

        return "\n\n".join(pages_text), page_count, method, round(avg_confidence, 3)

    def _process_image(
        self, path: Path
    ) -> tuple[str, int, str, float]:
        img = Image.open(path).convert("RGB")
        ocr_text = pytesseract.image_to_string(img)

        try:
            ocr_data = pytesseract.image_to_data(
                img, output_type=pytesseract.Output.DICT
            )
            confidences = [
                int(c)
                for c in ocr_data["conf"]
                if str(c).isdigit() and int(c) > 0
            ]
            avg_conf = sum(confidences) / len(confidences) / 100.0 if confidences else 0.5
        except Exception:
            avg_conf = 0.5

        return ocr_text, 1, "ocr", round(avg_conf, 3)

    def _chunk_text(self, text: str, doc_id: str) -> list[TextChunk]:
        paragraphs = text.split("\n\n")
        chunks: list[TextChunk] = []
        current_chunk = ""
        current_start = 0
        chunk_index = 0

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            if len(current_chunk) + len(para) + 1 > settings.CHUNK_SIZE and current_chunk:
                # Save current chunk
                end_char = current_start + len(current_chunk)
                chunks.append(
                    TextChunk(
                        chunk_id=f"{doc_id}_chunk_{chunk_index}",
                        doc_id=doc_id,
                        text=current_chunk.strip(),
                        chunk_index=chunk_index,
                        start_char=current_start,
                        end_char=end_char,
                    )
                )
                chunk_index += 1

                # Overlap: take last CHUNK_OVERLAP characters
                overlap = current_chunk[-settings.CHUNK_OVERLAP:] if len(current_chunk) > settings.CHUNK_OVERLAP else current_chunk
                current_start = end_char - len(overlap)
                current_chunk = overlap.strip() + "\n\n" + para
            else:
                if current_chunk:
                    current_chunk += "\n\n" + para
                else:
                    current_chunk = para

        # Save final chunk
        if current_chunk.strip():
            chunks.append(
                TextChunk(
                    chunk_id=f"{doc_id}_chunk_{chunk_index}",
                    doc_id=doc_id,
                    text=current_chunk.strip(),
                    chunk_index=chunk_index,
                    start_char=current_start,
                    end_char=current_start + len(current_chunk),
                )
            )

        return chunks
