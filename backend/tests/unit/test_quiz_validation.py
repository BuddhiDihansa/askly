import pytest

from app.api.quiz import _validate_questions


def _question():
    return {
        "question": "What is force?",
        "options": ["A", "B", "C", "D"],
        "answer": 1,
        "explanation": "The selected option is correct.",
    }


def test_quiz_validation_accepts_expected_shape():
    questions = _validate_questions({"questions": [_question()]}, expected_count=1)
    assert questions[0]["answer"] == 1


@pytest.mark.parametrize("change", [
    {"options": ["A", "B"]},
    {"answer": 4},
    {"explanation": ""},
])
def test_quiz_validation_rejects_malformed_question(change):
    question = _question()
    question.update(change)
    with pytest.raises(ValueError):
        _validate_questions({"questions": [question]}, expected_count=1)