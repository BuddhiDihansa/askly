"""
Tracks how well a student knows each topic, using an Exponential Moving
Average (EMA) - the same idea used for "current form" ratings in games
or stock price moving averages.

Why EMA instead of a simple running average of all quiz scores ever:
a plain average treats a quiz score from 3 months ago as equally
important as today's. EMA weights *recent* performance more heavily,
so mastery reflects "how the student is doing now", and a bad quiz
from long ago doesn't permanently drag the score down.
"""
import re
from datetime import datetime, timezone

from app.db.mongo import get_mastery_collection

# How much weight a new quiz result gets vs. the existing mastery score.
# 0.3 means each new result nudges the score by up to 30% toward this
# quiz's result, while 70% of the score is "memory" of past performance.
# Higher = mastery reacts faster to recent quizzes; lower = more stable
# but slower to reflect real improvement or regression.
NEW_RESULT_WEIGHT = 0.3
PREVIOUS_MASTERY_WEIGHT = 1 - NEW_RESULT_WEIGHT  # 0.7

# A brand-new topic starts at 0.25 (not 0.0) so the first quiz's
# difficulty isn't assumed to be "total beginner" - 0 would make the
# very first adaptive quiz maximally easy regardless of how the
# student actually performs.
DEFAULT_STARTING_MASTERY = 0.25


async def get_mastery(user_id: str) -> list[dict]:
    """All topics this user has attempted, ranked strongest first."""
    mastery = get_mastery_collection()
    cursor = mastery.find({"user_id": user_id}, {"_id": 0}).sort("mastery", -1)
    return await cursor.to_list(length=100)


async def update_mastery(user_id: str, topic: str, correct: int, total: int) -> float:
    """Call this after a quiz attempt. Returns the topic's updated
    mastery score (0.0 = no mastery, 1.0 = full mastery)."""
    mastery = get_mastery_collection()
    quiz_score = correct / max(total, 1)  # max(total, 1) avoids a divide-by-zero on an empty quiz

    # Topic names are matched case-insensitively ("Python" == "python") and
    # ignoring extra spaces, otherwise the same topic gets split into
    # several separate mastery records. We keep the spelling that was
    # stored first as the canonical name.
    topic = " ".join(topic.split())
    existing = await mastery.find_one(
        {"user_id": user_id, "topic": {"$regex": f"^{re.escape(topic)}$", "$options": "i"}}
    )
    if existing:
        topic = existing["topic"]
    previous_mastery = existing["mastery"] if existing else DEFAULT_STARTING_MASTERY

    updated_mastery = previous_mastery * PREVIOUS_MASTERY_WEIGHT + quiz_score * NEW_RESULT_WEIGHT
    updated_mastery = round(max(0.0, min(1.0, updated_mastery)), 3)  # clamp to [0, 1]
    previous_attempts = (existing or {}).get("attempts", 0)
    previous_correct = (existing or {}).get("correct_answers", 0)
    previous_incorrect = (existing or {}).get("incorrect_answers", 0)
    correct_answers = previous_correct + max(correct, 0)
    incorrect_answers = previous_incorrect + max(total - correct, 0)
    total_answers = correct_answers + incorrect_answers

    await mastery.update_one(
        {"user_id": user_id, "topic": topic},
        {
            "$set": {
                "mastery": updated_mastery,
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "last_practiced": datetime.now(timezone.utc).isoformat(),
                "attempts": previous_attempts + 1,
                "correct_answers": correct_answers,
                "incorrect_answers": incorrect_answers,
                "accuracy": round(correct_answers / max(total_answers, 1), 3),
            }
        },
        upsert=True,
    )
    return updated_mastery