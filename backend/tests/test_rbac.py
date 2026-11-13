"""Unit tests for Role-Based Access Control (RBAC).
Validates permissions for all 5 primary actors:
1. Customer/Prospect
2. Marketing/Sales Operations
3. Support Agent
4. Analyst
5. System Administrator
"""
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

def test_auth_me_and_actors_endpoints(client):
    # Default without header runs as SYSTEM_ADMIN
    res = client.get("/api/auth/me")
    assert res.status_code == 200
    data = res.json()
    assert data["role"] == "SYSTEM_ADMIN"
    assert len(data["permissions"]) > 0

    # Actors list endpoint returns all 5 actors
    res_actors = client.get("/api/auth/actors")
    assert res_actors.status_code == 200
    actors = res_actors.json()
    assert len(actors) == 5
    roles = [a["role"] for a in actors]
    assert "CUSTOMER_PROSPECT" in roles
    assert "MARKETING_SALES_OPS" in roles
    assert "SUPPORT_AGENT" in roles
    assert "ANALYST" in roles
    assert "SYSTEM_ADMIN" in roles

def test_customer_prospect_permissions(client):
    headers = {"X-User-Role": "CUSTOMER_PROSPECT"}

    # 1. Allowed: Inspect own contact and journey (Shravika Kavati)
    res_journey = client.get("/api/contacts/CON-2026-000001/journey", headers=headers)
    assert res_journey.status_code == 200
    assert res_journey.json()["contact_name"] == "Shravika Kavati"

    # 2. Forbidden: Inspect other customer's journey
    res_other = client.get("/api/contacts/CON-2026-000002/journey", headers=headers)
    assert res_other.status_code == 403

    # 3. Forbidden: Access internal financial summary
    res_summary = client.get("/api/dashboard/summary", headers=headers)
    assert res_summary.status_code == 403

    # 4. Forbidden: Access campaigns management
    res_camps = client.get("/api/campaigns", headers=headers)
    assert res_camps.status_code == 403

    # 5. Forbidden: Access attribution models
    res_attr = client.get("/api/attribution/compare", headers=headers)
    assert res_attr.status_code == 403

    # 6. Forbidden: Access generator
    res_gen = client.get("/api/generator/status", headers=headers)
    assert res_gen.status_code == 403

def test_marketing_sales_ops_permissions(client):
    headers = {"X-User-Role": "MARKETING_SALES_OPS"}

    # Allowed: Dashboard summary, campaigns, channel analytics, contacts
    assert client.get("/api/dashboard/summary", headers=headers).status_code == 200
    assert client.get("/api/campaigns", headers=headers).status_code == 200
    assert client.get("/api/analytics/channels", headers=headers).status_code == 200
    assert client.get("/api/contacts", headers=headers).status_code == 200

    # Forbidden: Attribution model comparison, anomalies, system generator
    assert client.get("/api/attribution/compare", headers=headers).status_code == 403
    assert client.get("/api/anomalies", headers=headers).status_code == 403
    assert client.get("/api/generator/status", headers=headers).status_code == 403

def test_support_agent_permissions(client):
    headers = {"X-User-Role": "SUPPORT_AGENT"}

    # Allowed: Contact search, customer journeys, campaign directory (read-only)
    assert client.get("/api/contacts", headers=headers).status_code == 200
    assert client.get("/api/contacts/CON-2026-000001/journey", headers=headers).status_code == 200
    assert client.get("/api/campaigns", headers=headers).status_code == 200

    # Forbidden: Macro financial summary, attribution deep dive, anomalies, generator
    assert client.get("/api/dashboard/summary", headers=headers).status_code == 403
    assert client.get("/api/attribution/compare", headers=headers).status_code == 403
    assert client.get("/api/anomalies", headers=headers).status_code == 403
    assert client.get("/api/generator/status", headers=headers).status_code == 403

def test_analyst_permissions(client):
    headers = {"X-User-Role": "ANALYST"}

    # Allowed: Dashboard summary, attribution compare, ROI analytics, anomalies, validation reports, exports
    assert client.get("/api/dashboard/summary", headers=headers).status_code == 200
    assert client.get("/api/attribution/compare", headers=headers).status_code == 200
    assert client.get("/api/analytics/roi", headers=headers).status_code == 200
    assert client.get("/api/anomalies", headers=headers).status_code == 200
    assert client.get("/api/validation/report", headers=headers).status_code == 200
    assert client.get("/api/exports/list", headers=headers).status_code == 200

    # Forbidden: System dataset generator controls
    assert client.get("/api/generator/status", headers=headers).status_code == 403

def test_system_admin_permissions(client):
    headers = {"X-User-Role": "SYSTEM_ADMIN"}

    # Allowed: Full access to all endpoints
    assert client.get("/api/dashboard/summary", headers=headers).status_code == 200
    assert client.get("/api/campaigns", headers=headers).status_code == 200
    assert client.get("/api/contacts", headers=headers).status_code == 200
    assert client.get("/api/attribution/compare", headers=headers).status_code == 200
    assert client.get("/api/anomalies", headers=headers).status_code == 200
    assert client.get("/api/validation/report", headers=headers).status_code == 200
    assert client.get("/api/generator/status", headers=headers).status_code == 200
    assert client.get("/api/exports/list", headers=headers).status_code == 200
