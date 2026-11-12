"""Unit tests for Financial and ROI Engine."""
import pytest
from backend.app.models.database import SessionLocal, reset_db
from backend.app.generators.synthetic_data import SyntheticDataGenerator
from backend.app.generators.config import STARTER_CONFIG
from backend.app.attribution.engine import AttributionEngine
from backend.app.analytics.financials import FinancialEngine
from backend.app.models.entities import Campaign, CostRecord

@pytest.fixture(scope="module")
def setup_financials():
    reset_db()
    db = SessionLocal()
    gen = SyntheticDataGenerator(db, STARTER_CONFIG)
    gen.generate()
    att = AttributionEngine(db)
    att.run_all_models()
    yield db
    db.close()

def test_financial_summary_metrics(setup_financials):
    db = setup_financials
    fin = FinancialEngine(db)
    summary = fin.get_overall_summary()

    assert summary["currency"] == "USD"
    assert summary["total_closed_revenue"] > 0
    assert summary["total_campaign_spend"] > 0
    assert summary["overall_roi"] is not None
    assert summary["excluded_duplicate_revenue"] > 0
    assert summary["excluded_duplicate_orders_count"] > 0
    assert summary["cost_per_lead"] > 0
    assert summary["cost_per_acquisition"] > 0

def test_missing_cost_campaign_roi_is_none(setup_financials):
    db = setup_financials
    fin = FinancialEngine(db)
    breakdown = fin.get_campaign_roi_breakdown()

    # Find campaign with 0 cost records
    missing_cost_camps = [c for c in breakdown if c["actual_spend"] == 0]
    assert len(missing_cost_camps) > 0
    for c in missing_cost_camps:
        assert c["roi"] is None
        assert c["roi_status"] == "UNAVAILABLE_MISSING_COST"

def test_channel_performance_aggregation(setup_financials):
    db = setup_financials
    fin = FinancialEngine(db)
    channels = fin.get_channel_performance()
    assert len(channels) == 8
    for ch in channels:
        assert "channel_id" in ch
        assert "spend" in ch
        assert "attributed_revenue" in ch
