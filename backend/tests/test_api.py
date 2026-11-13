"""Unit tests for FastAPI endpoints."""
import pytest
from fastapi.testclient import TestClient
from backend.app.models.database import SessionLocal, reset_db
from backend.app.generators.synthetic_data import SyntheticDataGenerator
from backend.app.generators.config import STARTER_CONFIG
from backend.app.attribution.engine import AttributionEngine
from backend.app.analytics.anomaly_detector import AnomalyDetectionEngine
from backend.app.main import app

@pytest.fixture(scope="module")
def client():
    reset_db()
    db = SessionLocal()
    gen = SyntheticDataGenerator(db, STARTER_CONFIG)
    gen.generate()
    att = AttributionEngine(db)
    att.run_all_models()
    det = AnomalyDetectionEngine(db)
    det.run_detection()
    db.close()
    return TestClient(app)

def test_health_endpoint(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "HEALTHY"

def test_dashboard_summary_endpoint(client):
    res = client.get("/api/dashboard/summary")
    assert res.status_code == 200
    data = res.json()
    assert "total_campaigns" in data
    assert "overall_roi" in data
    assert "revenue_by_model" in data

def test_campaigns_list_and_detail(client):
    res = client.get("/api/campaigns?limit=5")
    assert res.status_code == 200
    data = res.json()
    assert len(data["items"]) == 5
    cid = data["items"][0]["campaign_id"]

    res_detail = client.get(f"/api/campaigns/{cid}")
    assert res_detail.status_code == 200
    detail = res_detail.json()
    assert detail["campaign_id"] == cid
    assert "creatives" in detail
    assert "audiences" in detail

def test_customer_journey_endpoint(client):
    contacts_res = client.get("/api/contacts?limit=1")
    assert contacts_res.status_code == 200
    contact_id = contacts_res.json()[0]["contact_id"]

    journey_res = client.get(f"/api/contacts/{contact_id}/journey")
    assert journey_res.status_code == 200
    jdata = journey_res.json()
    assert jdata["contact_id"] == contact_id
    assert len(jdata["events"]) > 0

def test_shravika_kavati_journey_api(client):
    res = client.get("/api/contacts/CON-2026-000001/journey")
    assert res.status_code == 200
    jdata = res.json()
    assert jdata["contact_name"] == "Shravika Kavati"
    assert jdata["email"] == "shravika.kavati@gmail.com"
    assert len(jdata["events"]) > 0
    # Verify events include amounts formatted with INR (₹)
    order_events = [e for e in jdata["events"] if e["event_type"] == "ORDER"]
    assert len(order_events) > 0
    for oe in order_events:
        assert "₹" in oe["description"]

def test_anomalies_endpoint(client):
    res = client.get("/api/anomalies")
    assert res.status_code == 200
    data = res.json()
    assert data["total_anomalies"] > 0
    assert "evaluation_metrics" in data

def test_validation_report_endpoint(client):
    res = client.get("/api/validation/report")
    assert res.status_code == 200
    data = res.json()
    assert data["summary"]["total_rules"] == 15

def test_chronological_evaluation_periods_endpoint(client):
    res = client.get("/api/evaluation/chronological-periods")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "SUCCESS"
    assert data["total_periods"] == 3
    period_codes = [p["period_code"] for p in data["periods"]]
    assert "TRAIN" in period_codes
    assert "VALIDATION" in period_codes
    assert "TEST" in period_codes
    for p in data["periods"]:
        assert "start_date" in p
        assert "end_date" in p
        assert p["orders_count"] >= 0
        assert p["order_revenue"] >= 0.0

def test_exports_ground_truth_download_endpoint(client):
    res_csv = client.get("/api/exports/ground-truth/csv")
    assert res_csv.status_code == 200
    assert len(res_csv.content) > 0

    res_json = client.get("/api/exports/ground-truth/json")
    assert res_json.status_code == 200
    assert len(res_json.content) > 0
