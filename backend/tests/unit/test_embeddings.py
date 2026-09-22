import numpy as np
import pytest

from app.services.embeddings import validate_embedding


def test_embedding_validation_accepts_finite_vector():
    assert validate_embedding([1, 0, 0], expected_dimension=3) == [1.0, 0.0, 0.0]


@pytest.mark.parametrize("vector", [[], [np.nan, 0], [np.inf, 0]])
def test_embedding_validation_rejects_invalid_vector(vector):
    with pytest.raises(ValueError):
        validate_embedding(vector)