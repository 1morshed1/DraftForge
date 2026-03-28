"""Shared fixtures for DraftForge backend tests."""

import os
import tempfile
from pathlib import Path

import pytest

# Point data dirs to a temp directory so tests don't pollute real data
_tmp = tempfile.mkdtemp(prefix="draftforge_test_")
os.environ.setdefault("DATA_DIR", _tmp)

from app.config import settings  # noqa: E402  — must import after env override


@pytest.fixture(autouse=True)
def _clean_data_dirs():
    """Ensure each test starts with clean data directories."""
    for d in [
        settings.UPLOAD_DIR, settings.EXTRACTED_DIR, settings.FAISS_INDEX_DIR,
        settings.EDITS_DIR, settings.PATTERNS_DIR, settings.DRAFTS_DIR,
    ]:
        p = Path(d)
        p.mkdir(parents=True, exist_ok=True)
        for f in p.glob("*"):
            if f.is_file():
                f.unlink()
    yield


@pytest.fixture
def sample_text():
    return (
        "RESIDENTIAL LEASE AGREEMENT\n\n"
        "This Agreement is entered into as of January 15, 2024, by and between "
        "GREENFIELD PROPERTIES LLC (\"Landlord\") and JAMES WHITMORE (\"Tenant\").\n\n"
        "The monthly rent shall be $2,450.00, due on the first day of each month. "
        "A security deposit of $4,900.00 shall be collected.\n\n"
        "Case File No. LL-2024-00417.\n\n"
        "The lease term shall commence on February 1, 2024, and terminate on "
        "January 31, 2025."
    )


@pytest.fixture
def sample_pdf(tmp_path):
    """Create a minimal PDF with extractable text."""
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph
    from reportlab.lib.styles import getSampleStyleSheet

    path = tmp_path / "test.pdf"
    doc = SimpleDocTemplate(str(path), pagesize=letter)
    styles = getSampleStyleSheet()
    doc.build([
        Paragraph("LEASE AGREEMENT", styles["Title"]),
        Paragraph(
            "This lease agreement is between GREENFIELD PROPERTIES LLC and "
            "JAMES WHITMORE for property at 1847 Oak Valley Drive. "
            "Monthly rent is $2,450.00. Case File No. LL-2024-00417. "
            "Dated January 15, 2024.",
            styles["BodyText"],
        ),
    ])
    return path


@pytest.fixture
def sample_txt(tmp_path):
    """Create a plain text legal document."""
    path = tmp_path / "notice.txt"
    path.write_text(
        "NOTICE OF INTENT\n\n"
        "Re: Martha Reynolds v. Summit Healthcare Group\n"
        "Case No. 3:2024-CV-00156\n\n"
        "Medical expenses: $347,892.00\n"
        "Lost wages: $42,500.00\n\n"
        "Filed: February 28, 2024\n"
    )
    return path


@pytest.fixture
def sample_image(tmp_path):
    """Create a simple PNG with text for OCR testing."""
    from PIL import Image, ImageDraw, ImageFont

    path = tmp_path / "note.png"
    img = Image.new("RGB", (400, 100), "white")
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
    except OSError:
        font = ImageFont.load_default()
    draw.text((10, 10), "Legal Notice Document", fill="black", font=font)
    draw.text((10, 50), "Case No. 2024-001", fill="black", font=font)
    img.save(str(path))
    return path
