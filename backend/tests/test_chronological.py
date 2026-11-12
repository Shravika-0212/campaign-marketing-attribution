"""Unit tests for Chronological Evaluation Splitting."""
from datetime import datetime
from backend.app.generators.config import get_period, TRAIN_END, VAL_END, TEST_END

def test_period_splitting_boundaries():
    train_date = datetime(2026, 3, 15, 12, 0)
    val_date = datetime(2026, 8, 20, 10, 0)
    test_date = datetime(2026, 11, 5, 16, 0)

    assert get_period(train_date) == "TRAIN"
    assert get_period(val_date) == "VALIDATION"
    assert get_period(test_date) == "TEST"

def test_no_period_leakage():
    # Boundary exact timestamp
    assert get_period(TRAIN_END) == "TRAIN"
    assert get_period(VAL_END) == "VALIDATION"
    assert get_period(TEST_END) == "TEST"
