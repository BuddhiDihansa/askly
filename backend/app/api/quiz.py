import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request

from app.ai.llm import chat, parse_json
from app.api.dependencies import current_user
from app.core.config import settings
from app.core.rate_limit import check_rate_limit
from app.db.mongo import get_quiz_attempts_collection
from app.schemas.chat import QuizRequest, QuizSubmit
from app.services.mastery import get_mastery, update_mastery
from app.services.retrieval import hybrid_retrieve

router = APIRouter(prefix="/api/quiz", tags=["quiz"])

# mastery thresholds that decide adaptive difficulty - matches the bands
# used when displaying progress, so a student's quiz difficulty always
# matches how their progress dashboard describes them
ADVANCED_THRESHOLD = 0.7
INTERMEDIATE_THRESHOLD = 0.45


def _pick_difficulty(requested: str, current_mastery: float) -> str:
    if requested != "adaptive":
        return requested
    if current_mastery > ADVANCED_THRESHOLD:
        return "advanced"
    if current_mastery > INTERMEDIATE_THRESHOLD:
        return "intermediate"
    return "beginner"


@router.post("/generate")
async def generate(payload: QuizRequest, request: Request, current: dict = Depends(current_user)):
    user_id = str(current["_id"])
    quiz_attempts = get_quiz_attempts_collection()

    # quiz generation calls the LLM (real cost), so it's rate-limited
    # the same way chat is
    check_rate_limit(key=f"quiz:{user_id}", max_per_minute=settings.rate_limit_chat_per_minute)

    source_chunks = await hybrid_retrieve(user_id, payload.topic, top_k=8)
    mastery_levels = await get_mastery(user_id)
    current_mastery = next(
        (m["mastery"] for m in mastery_levels if m["topic"].lower() == payload.topic.lower()),
        0.25,
    )
    difficulty = _pick_difficulty(payload.difficulty, current_mastery)

    context = "\n".join(chunk["text"] for chunk in source_chunks)
    prompt = (
        f"Create exactly {payload.count} multiple-choice questions about {payload.topic} "
        f"at {difficulty} difficulty. Use this evidence when available:\n{context}\n"
        f'Return ONLY JSON: {{"questions":[{{"question":"...","options":["...","...","...","..."],'
        f'"answer":0,"explanation":"..."}}]}}. answer is zero-based index.'
    )

    try:
        raw_reply = await chat(
            [
                {"role": "system", "content": "You generate rigorous educational quizzes. Do not invent facts when evidence is supplied."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.4,
        )
        data = parse_json(raw_reply)
    except Exception:
        # don't leak the raw LLM output or internal exception to the client
        raise HTTPException(status_code=502, detail="Quiz generation failed. Please try again.")

    quiz_id = str(uuid.uuid4())
    await quiz_attempts.insert_one({
        "quiz_id": quiz_id,
        "user_id": user_id,
        "topic": payload.topic,
        "questions": data["questions"],
        "difficulty": difficulty,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })

    # strip the answer/explanation before sending to the client - otherwise
    # a student could just read the answer key out of the network tab
    questions_without_answers = [
        {k: v for k, v in q.items() if k not in ("answer", "explanation")}
        for q in data["questions"]
    ]

    return {
        "quiz_id": quiz_id,
        "topic": payload.topic,
        "difficulty": difficulty,
        "questions": questions_without_answers,
        "mastery": current_mastery,
    }


@router.post("/submit")
async def submit(payload: QuizSubmit, current: dict = Depends(current_user)):
    user_id = str(current["_id"])
    quiz_attempts = get_quiz_attempts_collection()
    quiz = await quiz_attempts.find_one({"quiz_id": payload.quiz_id, "user_id": user_id})
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    questions = quiz["questions"]
    total = len(questions)
    if total == 0:
        raise HTTPException(status_code=400, detail="This quiz has no questions")

    correct = sum(
        1 for i, question in enumerate(questions)
        if payload.answers.get(str(i)) == question["answer"]
    )
    new_mastery = await update_mastery(user_id, quiz["topic"], correct, total)

    await quiz_attempts.update_one(
        {"_id": quiz["_id"]},
        {"$set": {"score": correct, "submitted_at": datetime.now(timezone.utc).isoformat()}},
    )

    return {
        "correct": correct,
        "total": total,
        "score": correct / total,
        "new_mastery": new_mastery,
        "topic": quiz["topic"],
    }
