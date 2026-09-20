from app.api.flashcards import _schedule


def test_again_resets_interval_and_reduces_ease():
    interval, ease = _schedule({"interval": 8, "ease": 2.5}, "again")
    assert interval == 0
    assert ease < 2.5


def test_easy_increases_interval():
    interval, ease = _schedule({"interval": 3, "ease": 2.5}, "easy")
    assert interval > 3
    assert ease > 2.5