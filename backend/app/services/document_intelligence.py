import re
import unicodedata
from dataclasses import dataclass

from pypdf import PdfReader


class DocumentProcessingError(Exception):
    """Raised when a document cannot produce a usable knowledge base."""


@dataclass
class ExtractedPage:
    page_number: int
    text: str


@dataclass
class KnowledgeUnit:
    text: str
    page_start: int
    page_end: int
    chapter: str | None
    section: str | None
    topic: str | None
    concepts: list[str]
    content_type: str
    formula: str | None = None
    example: str | None = None
    question: str | None = None


CHAPTER_RE = re.compile(r"^(chapter|unit|module|lesson)\s+[\w.-]+\s*[:.-]?\s*(.*)$", re.I)
SECTION_RE = re.compile(r"^(section|topic|subsection)\s+[\w.-]+\s*[:.-]?\s*(.*)$", re.I)
NUMBERED_HEADING_RE = re.compile(r"^\d+(?:\.\d+)*[.)]?\s+(.{2,100})$")
FORMULA_RE = re.compile(r"(?:\b[A-Za-z]\s*[=≈]\s*[^.;]{1,120}|[A-Za-z0-9)]+\s*[+\-*/^]\s*[A-Za-z0-9(]+)")
EXAMPLE_RE = re.compile(r"\b(example|worked example|solved problem|case study)\b", re.I)
QUESTION_RE = re.compile(r"^(question|exercise|review question|problem)\b|\?$", re.I)


def clean_text(text: str) -> str:
    text = unicodedata.normalize("NFKC", text or "")
    text = text.replace("\u00ad", "")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    lines = [line.strip() for line in text.splitlines()]
    cleaned_lines: list[str] = []
    blank_pending = False
    for line in lines:
        if not line:
            blank_pending = True
            continue
        if blank_pending and cleaned_lines:
            cleaned_lines.append("")
        cleaned_lines.append(line)
        blank_pending = False
    cleaned = "\n".join(cleaned_lines).strip()
    return re.sub(r"(?<![.!?:])\n(?=[a-z])", " ", cleaned)


def extract_pages(reader: PdfReader) -> list[ExtractedPage]:
    pages: list[ExtractedPage] = []
    failures = 0
    for page_number, page in enumerate(reader.pages, start=1):
        try:
            text = clean_text(page.extract_text() or "")
        except Exception:
            failures += 1
            continue
        if text:
            pages.append(ExtractedPage(page_number, text))

    if not pages:
        raise DocumentProcessingError("No readable text found in PDF")
    if failures == len(reader.pages):
        raise DocumentProcessingError("PDF text extraction failed")

    margin_pages: dict[str, set[int]] = {}
    for page in pages:
        lines = page.text.splitlines()
        margins = set(lines[:2] + lines[-2:])
        for line in margins:
            if len(line) >= 3:
                margin_pages.setdefault(line, set()).add(page.page_number)

    repeated_margins = {
        line for line, page_numbers in margin_pages.items()
        if len(page_numbers) >= 2 and len(page_numbers) >= max(2, len(pages) // 2)
    }
    for page in pages:
        lines = [line for line in page.text.splitlines() if line not in repeated_margins]
        page.text = "\n".join(lines).strip()

    pages = [page for page in pages if page.text]
    if not pages:
        raise DocumentProcessingError("No readable text found after cleaning PDF content")
    return pages


def _is_heading(line: str) -> bool:
    if CHAPTER_RE.match(line) or SECTION_RE.match(line) or NUMBERED_HEADING_RE.match(line):
        return True
    return len(line) <= 100 and line.isupper() and len(line.split()) <= 12


def _heading_title(line: str) -> str:
    match = CHAPTER_RE.match(line) or SECTION_RE.match(line) or NUMBERED_HEADING_RE.match(line)
    if match:
        return (match.group(2) if match.lastindex and match.lastindex >= 2 else match.group(1)).strip()
    return line.strip().title()


def _concepts(text: str, topic: str | None) -> list[str]:
    candidates = re.findall(r"\b[A-Z][A-Za-z0-9'-]{2,}(?:\s+[A-Z][A-Za-z0-9'-]{2,}){0,3}", text)
    values = []
    for value in ([topic] if topic else []) + candidates:
        if value and value not in values and len(value) <= 100:
            values.append(value)
    return values[:10]


def analyze_pages(pages: list[ExtractedPage]) -> tuple[list[KnowledgeUnit], list[dict]]:
    units: list[KnowledgeUnit] = []
    chapters: list[dict] = []
    chapter_name: str | None = None
    section_name: str | None = None
    topic: str | None = None
    current_chapter: dict | None = None

    for page in pages:
        blocks = [block.strip() for block in re.split(r"\n\s*\n", page.text) if block.strip()]
        for block in blocks:
            lines = block.splitlines()
            heading = lines[0].strip()
            if CHAPTER_RE.match(heading):
                chapter_name = heading
                topic = _heading_title(heading) or None
                current_chapter = {"chapter": chapter_name, "title": topic, "page_start": page.page_number, "page_end": page.page_number}
                chapters.append(current_chapter)
                if len(lines) == 1:
                    continue
                block = "\n".join(lines[1:]).strip()
                lines = block.splitlines()
                heading = lines[0].strip()
            if current_chapter:
                current_chapter["page_end"] = page.page_number
            if SECTION_RE.match(heading) or NUMBERED_HEADING_RE.match(heading) or (len(lines) == 1 and _is_heading(heading)):
                section_name = heading
                topic = _heading_title(heading) or topic
                content_type = "section" if SECTION_RE.match(heading) else "heading"
            else:
                section_name = section_name
                content_type = "paragraph"

            formula_match = FORMULA_RE.search(block)
            example_match = EXAMPLE_RE.search(block)
            question_match = QUESTION_RE.search(block)
            if example_match:
                content_type = "example"
            elif question_match:
                content_type = "question"
            elif formula_match:
                content_type = "formula"

            units.append(KnowledgeUnit(
                text=block,
                page_start=page.page_number,
                page_end=page.page_number,
                chapter=chapter_name,
                section=section_name,
                topic=topic,
                concepts=_concepts(block, topic),
                content_type=content_type,
                formula=formula_match.group(0) if formula_match else None,
                example=block if example_match else None,
                question=block if question_match else None,
            ))

    return units, chapters


def build_chunks(units: list[KnowledgeUnit], max_chars: int = 1400) -> list[dict]:
    chunks: list[dict] = []
    current: list[KnowledgeUnit] = []
    current_length = 0

    def flush() -> None:
        nonlocal current, current_length
        if not current:
            return
        first = current[0]
        last = current[-1]
        chunks.append({
            "text": "\n\n".join(unit.text for unit in current),
            "page": first.page_start,
            "page_start": first.page_start,
            "page_end": last.page_end,
            "chapter": first.chapter,
            "section": first.section,
            "topic": first.topic,
            "concepts": sorted({concept for unit in current for concept in unit.concepts}),
            "content_type": first.content_type,
            "formula": next((unit.formula for unit in current if unit.formula), None),
            "example": next((unit.example for unit in current if unit.example), None),
            "question": next((unit.question for unit in current if unit.question), None),
            "source_order": len(chunks),
        })
        current = []
        current_length = 0

    for unit in units:
        if current and current_length + len(unit.text) + 2 > max_chars:
            flush()
        current.append(unit)
        current_length += len(unit.text) + 2
    flush()
    return chunks
