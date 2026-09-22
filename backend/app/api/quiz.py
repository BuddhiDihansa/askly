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
from app.api.notifications import create_notification
from app.services.rag import retrieve

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


def _validate_questions(data: dict, expected_count: int) -> list[dict]:
    questions = data.get("questions") if isinstance(data, dict) else None
    if not isinstance(questions, list) or len(questions) != expected_count:
        raise ValueError("Quiz response has an invalid question count")
    validated = []
    for question in questions:
        if not isinstance(question, dict):
            raise ValueError("Quiz question must be an object")
        prompt = question.get("question")
        options = question.get("options")
        answer = question.get("answer")
        explanation = question.get("explanation")
        if (
            not isinstance(prompt, str) or not prompt.strip()
            or not isinstance(options, list) or len(options) != 4
            or not all(isinstance(option, str) and option.strip() for option in options)
            or not isinstance(answer, int) or not 0 <= answer < len(options)
            or not isinstance(explanation, str) or not explanation.strip()
        ):
            raise ValueError("Quiz response contains an invalid question")
        validated.append({
            "question": prompt.strip(),
            "options": [option.strip() for option in options],
            "answer": answer,
            "explanation": explanation.strip(),
        })
    return validated


@router.post("/generate")
async def generate(payload: QuizRequest, request: Request, current: dict = Depends(current_user)):
    user_id = str(current["_id"])
    quiz_attempts = get_quiz_attempts_collection()

    # quiz generation calls the LLM (real cost), so it's rate-limited
    # the same way chat is
    check_rate_limit(key=f"quiz:{user_id}", max_per_minute=settings.rate_limit_chat_per_minute)

    rag_result = await retrieve(user_id, payload.topic)
    source_chunks = rag_result["results"]
    mastery_levels = await get_mastery(user_id)
    current_mastery = next(
        (m["mastery"] for m in mastery_levels if " ".join(m["topic"].lower().split()) == " ".join(payload.topic.lower().split())),
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
        questions = _validate_questions(data, payload.count)
    except Exception:
        # don't leak the raw LLM output or internal exception to the client
        raise HTTPException(status_code=502, detail="Quiz generation failed. Please try again.")

    quiz_id = str(uuid.uuid4())
    await quiz_attempts.insert_one({
        "quiz_id": quiz_id,
        "user_id": user_id,
        "topic": payload.topic,
        "questions": questions,
        "difficulty": difficulty,
        "sources": rag_result["sources"],
        "evidence_quality": rag_result["retrieval_metadata"]["evidence_quality"],
        "created_at": datetime.now(timezone.utc).isoformat(),
    })

    # SECURITY: only send the client an explicit allow-list of fields, built
    # from the *validated* questions. The old code filtered the raw LLM
    # output by removing "answer"/"explanation", so if the model added any
    # other field (e.g. "correct_answer", "hint") the answer key leaked
    # through the network tab. An allow-list can't leak unknown fields.
    questions_without_answers = [
        {"question": q["question"], "options": q["options"]}
        for q in questions
    ]

    return {
        "quiz_id": quiz_id,
        "topic": payload.topic,
        "difficulty": difficulty,
        "questions": questions_without_answers,
        "mastery": current_mastery,
        "sources": rag_result["sources"],
        "evidence_quality": rag_result["retrieval_metadata"]["evidence_quality"],
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

    # A quiz may only be submitted ONCE. Otherwise a student could submit the
    # same (already answered) quiz again and again to push mastery towards
    # 100%. The "claim" below is a single atomic database operation: it only
    # matches while `submitted_at` does not exist yet, so even two requests
    # arriving at the same instant cannot both succeed.
    claim = await quiz_attempts.update_one(
        {"_id": quiz["_id"], "submitted_at": {"$exists": False}},
        {"$set": {"score": correct, "submitted_at": datetime.now(timezone.utc).isoformat()}},
    )
    if claim.matched_count == 0:
        raise HTTPException(status_code=409, detail="This quiz has already been submitted")

    new_mastery = await update_mastery(user_id, quiz["topic"], correct, total)
    await create_notification(
        user_id,
        "Quiz reviewed",
        f"You scored {correct}/{total} on {quiz['topic']}. Review the topic again to strengthen retention.",
    )

    return {
        "correct": correct,
        "total": total,
        "score": correct / total,
        "new_mastery": new_mastery,
        "topic": quiz["topic"],
    }