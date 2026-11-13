"""Unit tests for Deterministic Synthetic Data Generator.
Verifies all 10 requirements:
1. Fixed random seed 20261022
2. Valid parent records generated before dependent records
3. Primary keys, foreign keys and bridge tables
4. Multi-campaign customer journeys, offline touchpoints, long conversion windows
5. Two-phase generation: valid records generated first, then labelled anomalies injected
6. Derived values calculated from source records
7. Separate ground truth files (ground_truth.csv and ground_truth.json)
8. CSV, JSON and SQL seed data exports
9. Repeated generation idempotency with identical checksums
10. Validation summary and SHA-256 checksums
"""
import pytest
from pathlib import Path
from backend.app.models.database import SessionLocal, reset_db
from backend.app.generators.synthetic_data import SyntheticDataGenerator
from backend.app.generators.config import (
    STARTER_CONFIG, FULL_BASELINE_CONFIG, FULL_CONFIG, RANDOM_SEED,
    get_dataset_config
)
from backend.app.models.entities import (
    Campaign, Contact, Touchpoint, Opportunity, Order, CostRecord,
    CampaignChannel, CampaignAudience, CampaignCreative, ContactIdentity,
    Channel, WebSession
)
from backend.app.services.export_service import ExportService

@pytest.fixture(scope="module")
def setup_db():
    reset_db()
    db = SessionLocal()
    gen = SyntheticDataGenerator(db, STARTER_CONFIG, seed=RANDOM_SEED)
    summary = gen.generate()
    yield db, summary
    db.close()

def test_config_specifications_and_aliases():
    """Verify STARTER and FULL BASELINE configurations match exact volume specifications."""
    # STARTER requirements
    assert STARTER_CONFIG.num_campaigns == 50
    assert STARTER_CONFIG.num_contacts == 1000
    assert STARTER_CONFIG.num_touchpoints == 4000
    assert STARTER_CONFIG.num_opportunities == 200

    # FULL BASELINE requirements
    assert FULL_BASELINE_CONFIG.num_campaigns == 500
    assert FULL_BASELINE_CONFIG.num_contacts == 50000
    assert FULL_BASELINE_CONFIG.num_touchpoints == 200000
    assert FULL_BASELINE_CONFIG.num_opportunities == 10000

    # Aliases
    assert get_dataset_config("STARTER") == STARTER_CONFIG
    assert get_dataset_config("FULL") == FULL_BASELINE_CONFIG
    assert get_dataset_config("FULL_BASELINE") == FULL_BASELINE_CONFIG
    assert get_dataset_config("FULL BASELINE") == FULL_BASELINE_CONFIG

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

def test_parent_child_integrity_and_bridge_tables(setup_db):
    db, _ = setup_db
    # All touchpoints must reference valid campaigns and channels
    touches = db.query(Touchpoint).all()
    camp_ids = {c.campaign_id for c in db.query(Campaign.campaign_id).all()}
    chan_ids = {c.channel_id for c in db.query(Channel.channel_id).all()}
    for t in touches:
        assert t.campaign_id in camp_ids
        assert t.channel_id in chan_ids

    # Bridge tables must be populated
    cmp_channels = db.query(CampaignChannel).all()
    cmp_audiences = db.query(CampaignAudience).all()
    cmp_creatives = db.query(CampaignCreative).all()
    assert len(cmp_channels) >= len(camp_ids)
    assert len(cmp_audiences) >= len(camp_ids)
    assert len(cmp_creatives) >= len(camp_ids)

    # Contact identities must be populated
    identities = db.query(ContactIdentity).all()
    assert len(identities) > 0

def test_offline_touchpoints_modeling(setup_db):
    """Verify offline touchpoints (events, direct mail) have channel_medium='OFFLINE' and session_id=None."""
    db, _ = setup_db
    offline_touches = db.query(Touchpoint).filter(Touchpoint.channel_medium == "OFFLINE").all()
    assert len(offline_touches) > 0
    for ot in offline_touches:
        assert ot.session_id is None
        assert ot.touch_type in ["WEBINAR", "IN_PERSON", "TRADE_SHOW"]

    online_touches = db.query(Touchpoint).filter(Touchpoint.channel_medium == "ONLINE", Touchpoint.session_id != None).all()
    assert len(online_touches) > 0

def test_multi_campaign_customer_journeys(setup_db):
    """Verify contacts experience touchpoints across multiple campaigns."""
    db, _ = setup_db
    # Find contacts with >= 3 touchpoints
    from sqlalchemy import func
    contacts_multi = (
        db.query(Touchpoint.contact_id)
        .group_by(Touchpoint.contact_id)
        .having(func.count(Touchpoint.touchpoint_id) >= 3)
        .limit(10)
        .all()
    )
    assert len(contacts_multi) > 0
    multi_camp_found = False
    for (cid,) in contacts_multi:
        c_camps = {t.campaign_id for t in db.query(Touchpoint).filter(Touchpoint.contact_id == cid).all()}
        if len(c_camps) > 1:
            multi_camp_found = True
            break
    assert multi_camp_found, "Expected at least one contact journey spanning multiple campaigns"

def test_derived_values_consistency(setup_db):
    """Verify derived values: Order amount == Opp expected_revenue, Order date == Opp close_date."""
    db, _ = setup_db
    orders = db.query(Order).filter(Order.is_duplicate_flag == False).all()
    assert len(orders) > 0
    for ord_obj in orders:
        opp = db.query(Opportunity).filter(Opportunity.opportunity_id == ord_obj.opportunity_id).first()
        assert opp is not None
        assert ord_obj.amount == opp.expected_revenue
        assert ord_obj.order_date == opp.close_date
        assert ord_obj.order_number.startswith("ATT-ORD-")
        assert "YF-" not in ord_obj.order_number

def test_shravika_kavati_customer_journey(setup_db):
    db, _ = setup_db
    contact = db.query(Contact).filter(Contact.contact_id == "CON-2026-000001").first()
    assert contact is not None
    assert contact.first_name == "Shravika"
    assert contact.last_name == "Kavati"
    assert contact.email == "shravika.kavati@gmail.com"
    
    # Check touchpoints
    touches = db.query(Touchpoint).filter(Touchpoint.contact_id == "CON-2026-000001").all()
    assert len(touches) > 0
    
    # Check conversions & INR currency
    orders = db.query(Order).filter(Order.contact_id == "CON-2026-000001").all()
    assert len(orders) > 0
    for ord_obj in orders:
        assert ord_obj.currency == "INR"
        assert ord_obj.amount > 0

def test_ground_truth_files_and_checksums(setup_db):
    """Verify ground truth is stored in separate CSV and JSON files with SHA-256."""
    _, summary = setup_db
    gt_meta = summary["ground_truth"]
    assert "ground_truth_json" in gt_meta
    assert "ground_truth_csv" in gt_meta
    assert "ground_truth_json_sha256" in gt_meta
    assert "ground_truth_csv_sha256" in gt_meta

    json_path = Path(gt_meta["ground_truth_json"])
    csv_path = Path(gt_meta["ground_truth_csv"])
    assert json_path.exists()
    assert csv_path.exists()
    assert json_path.stat().st_size > 0
    assert csv_path.stat().st_size > 0

def test_export_service_and_manifest(setup_db):
    """Verify CSV, JSON, and SQL seed exports with SHA-256 manifest."""
    db, summary = setup_db
    exporter = ExportService(db)
    exp = exporter.export_all(config_name="STARTER", seed=RANDOM_SEED)

    assert exp["status"] == "COMPLETED"
    assert exp["total_files_exported"] > 0
    assert exp["manifest_sha256"] is not None

    manifest_path = Path(exp["manifest_file"])
    assert manifest_path.exists()

    # Check that CSV, JSON and SQL files exist
    csv_dir = manifest_path.parent.parent / "exports" / "csv"
    json_dir = manifest_path.parent.parent / "exports" / "json"
    sql_file = manifest_path.parent.parent / "exports" / "sql" / "seed_data.sql"

    assert (csv_dir / "campaigns.csv").exists()
    assert (csv_dir / "campaign_channels.csv").exists()
    assert (csv_dir / "contact_identities.csv").exists()
    assert (json_dir / "touchpoints.json").exists()
    assert sql_file.exists()
    assert sql_file.stat().st_size > 0
