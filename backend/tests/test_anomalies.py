"""Unit tests for Anomaly Detection Engine and Ground Truth Evaluation."""
import pytest
from backend.app.models.database import SessionLocal, reset_db
from backend.app.generators.synthetic_data import SyntheticDataGenerator
from backend.app.generators.config import STARTER_CONFIG
from backend.app.attribution.engine import AttributionEngine
from backend.app.analytics.anomaly_detector import AnomalyDetectionEngine
from backend.app.models.entities import AnomalyIssue

@pytest.fixture(scope="module")
def setup_anomalies():
    reset_db()
    db = SessionLocal()
    gen = SyntheticDataGenerator(db, STARTER_CONFIG)
    gen.generate()
    att = AttributionEngine(db)
    att.run_all_models()
    detector = AnomalyDetectionEngine(db)
    summary = detector.run_detection()
    eval_res = detector.evaluate_against_ground_truth()
    yield db, summary, eval_res
    db.close()

def test_all_five_anomalies_detected(setup_anomalies):
    db, summary, _ = setup_anomalies
    by_type = summary["by_issue_type"]

    assert "DUPLICATE_REVENUE" in by_type
    assert "POST_CONVERSION_TOUCHPOINT" in by_type
    assert "CURRENCY_MISMATCH" in by_type
    assert "MISSING_CAMPAIGN_COST" in by_type
    assert "UNSUPPORTED_IDENTITY_LINK" in by_type

def test_ground_truth_evaluation_metrics(setup_anomalies):
    _, _, eval_res = setup_anomalies
    assert eval_res["evaluation_status"] == "SUCCESS"
    metrics = eval_res["overall_metrics"]
    assert metrics["precision"] == 1.0
    assert metrics["recall"] == 1.0
    assert metrics["f1_score"] == 1.0

def test_anomaly_table_populated(setup_anomalies):
    db, _, _ = setup_anomalies
    issues = db.query(AnomalyIssue).all()
    assert len(issues) > 0
    for iss in issues:
        assert iss.issue_id.startswith("ANO-2026-")
        assert iss.severity in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
        assert iss.resolution_status == "QUARANTINED"
