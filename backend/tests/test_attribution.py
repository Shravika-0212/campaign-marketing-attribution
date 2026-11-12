"""Unit tests for Attribution Engine models."""
import pytest
from datetime import datetime, timedelta
from backend.app.models.database import SessionLocal, reset_db
from backend.app.generators.synthetic_data import SyntheticDataGenerator
from backend.app.generators.config import STARTER_CONFIG
from backend.app.attribution.engine import AttributionEngine
from backend.app.models.entities import AttributionResult, Order

@pytest.fixture(scope="module")
def setup_attribution():
    reset_db()
    db = SessionLocal()
    gen = SyntheticDataGenerator(db, STARTER_CONFIG)
    gen.generate()
    att = AttributionEngine(db)
    summary = att.run_all_models()
    yield db, summary
    db.close()

def test_attribution_models_executed(setup_attribution):
    _, summary = setup_attribution
    assert "FIRST_TOUCH" in summary["models_executed"]
    assert "LAST_TOUCH" in summary["models_executed"]
    assert "MULTI_TOUCH_LINEAR" in summary["models_executed"]
    assert summary["records_created"]["first_touch"] > 0
    assert summary["records_created"]["last_touch"] > 0
    assert summary["records_created"]["multi_touch"] > 0

def test_first_touch_has_weight_one(setup_attribution):
    db, _ = setup_attribution
    ft_results = db.query(AttributionResult).filter(AttributionResult.model_id == "MDL-FIRST-TOUCH").all()
    for r in ft_results:
        assert r.attribution_weight == 1.0
        assert r.attributed_revenue > 0

def test_last_touch_has_weight_one(setup_attribution):
    db, _ = setup_attribution
    lt_results = db.query(AttributionResult).filter(AttributionResult.model_id == "MDL-LAST-TOUCH").all()
    for r in lt_results:
        assert r.attribution_weight == 1.0
        assert r.attributed_revenue > 0

def test_multi_touch_sums_to_100_percent(setup_attribution):
    db, _ = setup_attribution
    orders = db.query(Order).filter(Order.is_duplicate_flag == False).all()
    for o in orders:
        mt_results = (
            db.query(AttributionResult)
            .filter(AttributionResult.model_id == "MDL-MULTI-TOUCH", AttributionResult.order_id == o.order_id)
            .all()
        )
        if mt_results:
            total_weight = sum(r.attribution_weight for r in mt_results)
            total_revenue = sum(r.attributed_revenue for r in mt_results)
            assert abs(total_weight - 1.0) < 0.001
            assert abs(total_revenue - o.amount) < 0.05

def test_no_touchpoints_after_conversion_in_results(setup_attribution):
    db, _ = setup_attribution
    invalid_results = (
        db.query(AttributionResult)
        .filter(AttributionResult.touchpoint_timestamp > AttributionResult.conversion_timestamp)
        .all()
    )
    assert len(invalid_results) == 0
