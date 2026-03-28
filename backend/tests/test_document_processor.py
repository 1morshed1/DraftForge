"""Tests for the DocumentProcessor service."""

import pytest

from app.services.document_processor import DocumentProcessor


@pytest.fixture
def processor():
    return DocumentProcessor()


class TestPDFProcessing:
    @pytest.mark.asyncio
    async def test_extracts_text_from_pdf(self, processor, sample_pdf):
        result = await processor.process_document(str(sample_pdf), "test.pdf")
        assert result.doc_id
        assert "LEASE AGREEMENT" in result.raw_text or "LEASE" in result.raw_text
        assert result.metadata.file_type == ".pdf"
        assert result.metadata.extraction_method == "text_extraction"
        assert result.metadata.confidence_score >= 0.9

    @pytest.mark.asyncio
    async def test_pdf_produces_chunks(self, processor, sample_pdf):
        result = await processor.process_document(str(sample_pdf), "test.pdf")
        assert len(result.chunks) >= 1
        for chunk in result.chunks:
            assert chunk.doc_id == result.doc_id
            assert chunk.text.strip()


class TestTextProcessing:
    @pytest.mark.asyncio
    async def test_extracts_text_from_txt(self, processor, sample_txt):
        result = await processor.process_document(str(sample_txt), "notice.txt")
        assert "Martha Reynolds" in result.cleaned_text
        assert result.metadata.extraction_method == "direct_read"
        assert result.metadata.confidence_score == 1.0

    @pytest.mark.asyncio
    async def test_txt_metadata(self, processor, sample_txt):
        result = await processor.process_document(str(sample_txt), "notice.txt")
        assert result.metadata.file_type == ".txt"
        assert result.metadata.page_count == 1
        assert result.metadata.word_count > 0
        assert result.metadata.char_count > 0


class TestImageProcessing:
    @pytest.mark.asyncio
    async def test_ocr_on_image(self, processor, sample_image):
        result = await processor.process_document(str(sample_image), "note.png")
        assert result.metadata.extraction_method == "ocr"
        assert result.metadata.file_type == ".png"
        # OCR may not be perfect but should extract something
        assert result.metadata.word_count > 0


class TestChunking:
    @pytest.mark.asyncio
    async def test_chunk_ids_are_unique(self, processor, sample_txt):
        result = await processor.process_document(str(sample_txt), "notice.txt")
        ids = [c.chunk_id for c in result.chunks]
        assert len(ids) == len(set(ids))

    @pytest.mark.asyncio
    async def test_chunk_indices_sequential(self, processor, sample_txt):
        result = await processor.process_document(str(sample_txt), "notice.txt")
        for i, chunk in enumerate(result.chunks):
            assert chunk.chunk_index == i


class TestStructuredData:
    @pytest.mark.asyncio
    async def test_extracts_structured_fields(self, processor, sample_txt):
        result = await processor.process_document(str(sample_txt), "notice.txt")
        sd = result.structured_data
        assert "dates_found" in sd
        assert "monetary_amounts" in sd
        assert "$347,892.00" in sd["monetary_amounts"]
