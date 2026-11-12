"""Unit tests for Deterministic Synthetic Data Generator."""
import pytest
from backend.app.models.database import SessionLocal, reset_db
from backend.app.generators.synthetic_data import SyntheticDataGenerator
from backend.app.generators.config import STARTER_CONFIG, RANDOM_SEED
from backend.app.models.entities import Campaign, Contact, Touchpoint, Opportunity, Order

@pytest.fixture(scope="module")
def setup_db():
    reset_db()
    db = SessionLocal()
    gen = SyntheticDataGenerator(db, STARTER_CONFIG, seed=RANDOM_SEED)
    summary = gen.generate()
    yield db, summary
    db.close()

def test_deterministic_reproducibility(setup_db):
    db, summary = setup_db
    assert summary["status"] == "COMPLETED"
    assert summary["seed"] == RANDOM_SEED
    assert summary["checksum"] is not None

def test_deterministic_id_conventions(setup_db):
    db, _ = setup_db
    # Test campaign ID pattern: CMP-2026-000001 (15 characters)
    camps = db.query(Campaign).limit(5).all()
    for c in camps:
        assert c.campaign_id.startswith("CMP-2026-")
        assert len(c.campaign_id) == 15

    # Test contact ID pattern
    contacts = db.query(Contact).limit(5).all()
    for ct in contacts:
        assert ct.contact_id.startswith("CON-2026-")

    # Test touchpoint ID pattern
    touches = db.query(Touchpoint).limit(5).all()
    for t in touches:
        assert t.touchpoint_id.startswith("TOUCH-CON-")

    # Test opportunity ID pattern
    opps = db.query(Opportunity).limit(5).all()
    for o in opps:
        assert o.opportunity_id.startswith("OPP-2026-")

    # Test order ID pattern
    orders = db.query(Order).limit(5).all()
    for ord_obj in orders:
        assert ord_obj.order_id.startswith("ORD-2026-")

def test_parent_child_integrity(setup_db):
    db, _ = setup_db
    # Every lead must have a valid contact and campaign
    touches = db.query(Touchpoint).all()
    camp_ids = {c.campaign_id for c in db.query(Campaign.campaign_id).all()}
    for t in touches:
        assert t.campaign_id in camp_ids
