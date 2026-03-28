"""Tests for text cleaning and structured data extraction."""

from app.utils.text_utils import clean_text, extract_structured_data


class TestCleanText:
    def test_removes_control_characters(self):
        raw = "Hello\x00World\x0bTest"
        assert "\x00" not in clean_text(raw)
        assert "\x0b" not in clean_text(raw)

    def test_normalizes_whitespace(self):
        raw = "Too   many    spaces"
        assert "  " not in clean_text(raw)

    def test_collapses_excessive_newlines(self):
        raw = "Paragraph one.\n\n\n\n\nParagraph two."
        result = clean_text(raw)
        assert "\n\n\n" not in result
        assert "Paragraph one." in result
        assert "Paragraph two." in result

    def test_repairs_broken_sentences(self):
        raw = "this line ends with a lowercase\nletter that continues here"
        result = clean_text(raw)
        assert "lowercase letter" in result

    def test_preserves_intentional_line_breaks(self):
        raw = "Section 1.\n\nSection 2."
        result = clean_text(raw)
        assert "Section 1." in result
        assert "Section 2." in result


class TestExtractStructuredData:
    def test_extracts_dates(self, sample_text):
        data = extract_structured_data(sample_text)
        assert len(data["dates_found"]) > 0
        assert any("January" in d for d in data["dates_found"])

    def test_extracts_case_references(self, sample_text):
        data = extract_structured_data(sample_text)
        assert len(data["case_references"]) > 0

    def test_extracts_monetary_amounts(self, sample_text):
        data = extract_structured_data(sample_text)
        amounts = data["monetary_amounts"]
        assert "$2,450.00" in amounts
        assert "$4,900.00" in amounts

    def test_returns_dict_structure(self, sample_text):
        data = extract_structured_data(sample_text)
        assert "dates_found" in data
        assert "case_references" in data
        assert "parties" in data
        assert "monetary_amounts" in data
        assert "sections" in data

    def test_handles_empty_text(self):
        data = extract_structured_data("")
        assert data["dates_found"] == []
        assert data["monetary_amounts"] == []
