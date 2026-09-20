"""Deterministic planning helpers for the AI tutor orchestration layer."""

from dataclasses import dataclass
import re


@dataclass(frozen=True)
class TutorPlan:
    intent: str
    strategy: str
    needs_web: bool
    needs_documents: bool
    document_only: bool


TIME_SENSITIVE_TERMS = {"latest", "today", "current", "recent", "news", "now", "update"}
INTENT_TERMS = {
    "quiz": {"quiz", "test me", "questions", "practice"},
    "summary": {"summarize", "summary", "key points", "tl;dr"},
    "example": {"example", "illustrate", "show me"},
    "step_by_step": {"step by step", "steps", "derive", "work through"},
    "simplify": {"simpler", "simply", "beginner", "eli5", "easy"},
    "flashcards": {"flashcard", "flash cards", "cards"},
}


def plan_tutor_request(message: str) -> TutorPlan:
    normalized = re.sub(r"\s+", " ", message or "").strip().casefold()
    if not normalized:
        return TutorPlan("explain", "clear_explanation", False, True, False)

    intent = "explain"
    for candidate, terms in INTENT_TERMS.items():
        if any(term in normalized for term in terms):
            intent = candidate
            break

    needs_web = any(term in normalized.split() for term in TIME_SENSITIVE_TERMS)
    document_only = any(
        phrase in normalized
        for phrase in ("in my document", "in my notes", "uploaded material", "uploaded document")
    )
    strategy = {
        "quiz": "practice_questions",
        "summary": "concise_summary",
        "example": "worked_example",
        "step_by_step": "step_by_step_explanation",
        "simplify": "plain_language_explanation",
        "flashcards": "flashcard_prompts",
    }.get(intent, "clear_explanation")
    return TutorPlan(intent, strategy, needs_web, True, document_only)


def insufficient_evidence_message(document_only: bool) -> str:
    if document_only:
        return "I couldn't find enough evidence in your uploaded material to answer that reliably."
    return "I don't have enough evidence to answer that reliably yet. You can upload relevant material or ask for a current web lookup."