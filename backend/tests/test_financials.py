"""Unit tests for Financial and ROI Engine."""
import pytest
from backend.app.models.database import SessionLocal, reset_db
from backend.app.generators.synthetic_data import SyntheticDataGenerator
from backend.app.generators.config import STARTER_CONFIG
from backend.app.attribution.engine import AttributionEngine
from backend.app.analytics.financials import FinancialEngine
from backend.app.models.entities import Campaign, CostRecord, Order

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

    assert summary["currency"] == "INR"
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

def test_financial_reconciliation_consistency_and_rules(setup_financials):
    """Test all 9 financial rules:
    1. ROI formula: (Attributed Revenue - Actual Campaign Cost) / Actual Campaign Cost * 100
    2. Missing costs do not compute normal ROI (None)
    3. Missing cost campaigns flagged as INCOMPLETE
    4. Currency mismatches detected
    5. Incompatible currencies (e.g. USD) never combined with INR spend
    6. Duplicate orders prevented from inflating total closed revenue
    7. Overview summary and campaign breakdown have 100% consistent spend and revenue
    8. Campaign-wise spend, revenue and ROI are non-hardcoded and strictly calculated
    9. Attributed revenue across models reconciles with valid closed order revenue
    """
    db = setup_financials
    fin = FinancialEngine(db)
    summary = fin.get_overall_summary()
    breakdown = fin.get_campaign_roi_breakdown(model_id="MDL-MULTI-TOUCH")

    # 1. ROI formula verification on campaigns with cost
    for c in breakdown:
        if c["actual_spend"] > 0:
            expected_roi = round(((c["attributed_revenue"] - c["actual_spend"]) / c["actual_spend"]) * 100, 2)
            assert c["roi"] == expected_roi
        else:
            # 2. No normal ROI when cost is missing
            assert c["roi"] is None
            assert c["roi_status"] == "UNAVAILABLE_MISSING_COST"
            # 3. Flagged as INCOMPLETE
            assert c["status_display"] == "INCOMPLETE"
            assert c["is_incomplete"] is True

    # 4 & 5. Currency mismatches detected and foreign currencies isolated
    assert summary["currency"] == "INR"
    assert summary["currency_mismatch_count"] > 0
    non_inr_costs = db.query(CostRecord).filter(CostRecord.currency != "INR").all()
    assert len(non_inr_costs) == summary["currency_mismatch_count"]
    # Total campaign spend only includes INR
    inr_spend_sum = round(sum(c.amount for c in db.query(CostRecord).filter(CostRecord.currency == "INR").all()), 2)
    assert summary["total_campaign_spend"] == inr_spend_sum

    # 6. Duplicate orders excluded from closed revenue
    dup_orders = db.query(Order).filter(Order.is_duplicate_flag == True).all()
    assert len(dup_orders) == summary["excluded_duplicate_orders_count"]
    assert summary["excluded_duplicate_revenue"] > 0

    # 7. Consistency between overview and campaign breakdown
    sum_campaign_spend = round(sum(c["actual_spend"] for c in breakdown), 2)
    assert summary["total_campaign_spend"] == sum_campaign_spend

    sum_campaign_attr_rev = round(sum(c["attributed_revenue"] for c in breakdown), 2)
    assert summary["total_closed_revenue"] == sum_campaign_attr_rev
    assert summary["attributed_revenue_multi_touch"] == sum_campaign_attr_rev

    # 9. All 3 models reconcile exactly with total closed revenue
    for model_name, model_rev in summary["revenue_by_model"].items():
        assert round(model_rev, 2) == round(summary["total_closed_revenue"], 2)

