"""
The AI Orchestrator: decides what context the LLM needs before answering
a student's message, then asks the LLM to answer *grounded* in that
context (see the system prompt below for how hallucination is controlled).
"""
from bson import ObjectId
from bson.errors import InvalidId

from app.ai.llm import chat
from app.db.mongo import get_users_collection
from app.services.mastery import get_mastery
from app.services.rag import retrieve
from app.services.web_search import search_web
from app.services.tutor import insufficient_evidence_message, plan_tutor_request

# how many of the student's most recent mastery topics to show the LLM,
# so answers can be pitched at roughly the right level without the
# prompt growing unbounded as a student studies more topics over time
MAX_MASTERY_TOPICS_SHOWN = 8

# how many previous messages of chat history to include - keeps the LLM
# call's cost and latency bounded, since very long conversations would
# otherwise resend the entire history on every single message
MAX_HISTORY_MESSAGES = 8

SYSTEM_PROMPT = """You are ASKLY, a personalized learning assistant. Answer clearly at the student's level.
Prefer provided document evidence for course material. If web evidence is provided, distinguish it from
student documents. Never invent citations. If the evidence provided does not answer the question, say so
explicitly rather than guessing - it is better to say "I don't have enough information in your documents
to answer this" than to make something up. Explain difficult concepts step-by-step. End with a short
'Next step' when useful."""


def clean_history(history: list[dict]) -> list[dict]:
    """Keep only the fields the LLM API accepts.

    Stored conversation messages also carry our own bookkeeping fields
    ("at" timestamp, "action"). LLM chat APIs such as Groq's reject
    messages that contain unknown properties, which would make every
    follow-up message in a conversation fail. So we strip each message
    down to just role + content, and skip anything malformed.
    """
    cleaned = []
    for message in history[-MAX_HISTORY_MESSAGES:]:
        role = message.get("role")
        content = message.get("content")
        if role in {"user", "assistant"} and isinstance(content, str) and content:
            cleaned.append({"role": role, "content": content})
    return cleaned


async def answer(user_id: str, message: str, history: list[dict]) -> tuple[str, list[dict], list[dict]]:
    plan = plan_tutor_request(message)

    rag_result = await retrieve(user_id, message)
    document_sources = rag_result["sources"]
    web_sources = await search_web(message) if plan.needs_web else []
    mastery_levels = await get_mastery(user_id)
    try:
        user_object_id = ObjectId(user_id)
    except (InvalidId, TypeError):
        user_object_id = None
    profile = await get_users_collection().find_one(
        {"_id": user_object_id},
        {"_id": 0, "name": 1, "education_level": 1, "learning_goal": 1,
         "preferred_language": 1, "study_style": 1, "study_subjects": 1},
    ) or {}

    mastery_summary = (
        ", ".join(f"{m['topic']}={m['mastery']:.0%}" for m in mastery_levels[:MAX_MASTERY_TOPICS_SHOWN])
        or "No mastery data yet"
    )
    document_context = rag_result["context"]
    web_context = "\n".join(
        f"[Web: {w.get('title', '')}] {w.get('content', '')} ({w.get('url', '')})" for w in web_sources
    )

    user_prompt = (
        f"Tutor intent: {plan.intent}\n"
        f"Answer strategy: {plan.strategy}\n"
        f"Learner profile: {profile}\n"
        f"Student mastery: {mastery_summary}\n"
        f"DOCUMENT EVIDENCE:\n{document_context or 'None'}\n"
        f"WEB EVIDENCE:\n{web_context or 'None'}\n\n"
        f"Question: {message}"
    )

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        *clean_history(history),
        {"role": "user", "content": user_prompt},
    ]
    if not document_sources and not web_sources and plan.document_only:
        return insufficient_evidence_message(True), [], []
    reply = await chat(messages)
    return reply, document_sources, web_sources