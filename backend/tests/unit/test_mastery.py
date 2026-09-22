import pytest

from app.services.mastery import DEFAULT_STARTING_MASTERY, get_mastery, update_mastery


@pytest.mark.asyncio
async def test_new_topic_starts_from_default_mastery():
    # perfect score on a brand-new topic: new = 0.25*0.7 + 1.0*0.3 = 0.475
    new_mastery = await update_mastery("user1", "algebra", correct=5, total=5)
    assert new_mastery == round(DEFAULT_STARTING_MASTERY * 0.7 + 1.0 * 0.3, 3)


@pytest.mark.asyncio
async def test_mastery_moves_toward_repeated_good_scores():
    m1 = await update_mastery("user1", "algebra", correct=5, total=5)
    m2 = await update_mastery("user1", "algebra", correct=5, total=5)
    m3 = await update_mastery("user1", "algebra", correct=5, total=5)
    # each additional perfect quiz should push mastery higher, converging toward 1.0
    assert m1 < m2 < m3


@pytest.mark.asyncio
async def test_mastery_is_clamped_between_0_and_1():
    # even a string of perfect scores should never exceed 1.0
    mastery = 0.0
    for _ in range(20):
        mastery = await update_mastery("user1", "algebra", correct=10, total=10)
    assert 0.0 <= mastery <= 1.0


@pytest.mark.asyncio
async def test_zero_total_does_not_crash():
    # defensive: an empty quiz (total=0) shouldn't cause a divide-by-zero
    mastery = await update_mastery("user1", "algebra", correct=0, total=0)
    assert 0.0 <= mastery <= 1.0


@pytest.mark.asyncio
async def test_get_mastery_returns_topics_sorted_strongest_first():
    await update_mastery("user2", "weak_topic", correct=1, total=10)
    await update_mastery("user2", "strong_topic", correct=10, total=10)
    levels = await get_mastery("user2")
    assert levels[0]["topic"] == "strong_topic"
