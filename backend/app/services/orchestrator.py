"""
The AI Orchestrator: decides what context the LLM needs before answering
a student's message, then asks the LLM to answer *grounded* in that
context (see the system prompt below for how hallucination is controlled).
"""
from app.ai.llm import chat
from app.services.mastery import get_mastery
from app.services.rag import retrieve
from app.services.web_search import search_web

# if the student's message contains any of these words, assume they want
# up-to-date information the LLM's training data can't have, and trigger
# a live web search rather than relying on the model's memorized knowledge
TIME_SENSITIVE_KEYWORDS = {"latest", "today", "current", "recent", "news", "2026", "now", "update"}

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


async def answer(user_id: str, message: str, history: list[dict]) -> tuple[str, list[dict], list[dict]]:
    needs_web_search = any(word in message.lower().split() for word in TIME_SENSITIVE_KEYWORDS)

    rag_result = await retrieve(user_id, message)
    document_sources = rag_result["sources"]
    web_sources = await search_web(message) if needs_web_search else []
    mastery_levels = await get_mastery(user_id)

    mastery_summary = (
        ", ".join(f"{m['topic']}={m['mastery']:.0%}" for m in mastery_levels[:MAX_MASTERY_TOPICS_SHOWN])
        or "No mastery data yet"
    )
    document_context = rag_result["context"]
    web_context = "\n".join(
        f"[Web: {w.get('title', '')}] {w.get('content', '')} ({w.get('url', '')})" for w in web_sources
    )

    user_prompt = (
        f"Student mastery: {mastery_summary}\n"
        f"DOCUMENT EVIDENCE:\n{document_context or 'None'}\n"
        f"WEB EVIDENCE:\n{web_context or 'None'}\n\n"
        f"Question: {message}"
    )

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        *history[-MAX_HISTORY_MESSAGES:],
        {"role": "user", "content": user_prompt},
    ]
    reply = await chat(messages)
    return reply, document_sources, web_sources
