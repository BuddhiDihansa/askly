from io import BytesIO

from pypdf import PdfReader, PdfWriter

from app.services.document_intelligence import (
    analyze_pages,
    build_chunks,
    clean_text,
    extract_pages,
)


def _pdf_bytes(*pages: str) -> bytes:
    writer = PdfWriter()
    for _ in pages:
        writer.add_blank_page(width=612, height=792)
    # PdfWriter cannot create text content, so extraction behavior is tested
    # with lightweight page doubles below; this helper remains useful for
    # parser-level malformed/empty smoke checks.
    return BytesIO().getvalue()


def test_clean_text_normalizes_unicode_and_whitespace():
    assert clean_text("  Newton\u00ad\n  laws   of motion  ") == "Newton laws of motion"


def test_extract_pages_removes_repeated_headers_and_preserves_pages():
    class Page:
        def __init__(self, text):
            self.text = text

        def extract_text(self):
            return self.text

    class Reader:
        pages = [
            Page("ASKLY COURSE\nChapter 1\nPhotosynthesis\nASKLY 1"),
            Page("ASKLY COURSE\nChlorophyll absorbs light.\nASKLY 2"),
        ]

    pages = extract_pages(Reader())
    assert [page.page_number for page in pages] == [1, 2]
    assert all("ASKLY COURSE" not in page.text for page in pages)
    assert "Photosynthesis" in pages[0].text


def test_structure_and_learning_metadata_are_detected():
    class Page:
        def extract_text(self):
            return (
                "Chapter 3: Cell Division\n\n"
                "3.1 Mitosis\n\n"
                "F = ma. Example: A solved problem. What is the result?"
            )

    class Reader:
        pages = [Page()]

    units, chapters = analyze_pages(extract_pages(Reader()))
    chunks = build_chunks(units)
    assert chapters[0]["chapter"] == "Chapter 3: Cell Division"
    assert chapters[0]["page_start"] == 1
    assert any(unit.formula for unit in units)
    assert any(unit.example for unit in units)
    assert any(unit.question for unit in units)
    assert chunks[0]["page_start"] == 1
    assert chunks[0]["content_type"] in {"heading", "section", "paragraph", "formula", "example", "question"}
    assert "document_id" not in chunks[0]


def test_build_chunks_respects_learning_units_and_metadata():
    class Page:
        def extract_text(self):
            return "Chapter 1: Biology\n\nPhotosynthesis converts light into energy."

    class Reader:
        pages = [Page()]

    units, _ = analyze_pages(extract_pages(Reader()))
    chunks = build_chunks(units, max_chars=100)
    assert chunks
    assert all(chunk["text"].strip() for chunk in chunks)
    assert all(chunk["page_start"] <= chunk["page_end"] for chunk in chunks)
    assert all(isinstance(chunk["concepts"], list) for chunk in chunks)
