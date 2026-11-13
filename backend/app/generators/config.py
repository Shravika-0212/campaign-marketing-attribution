"""Configuration dataclasses and constants for synthetic data generation."""
from dataclasses import dataclass
from datetime import datetime

RANDOM_SEED = 20261022
BASE_CURRENCY = "INR"
LOOKBACK_WINDOW_DAYS = 90

# Chronological Period Boundaries
PERIOD_START = datetime(2026, 1, 1, 0, 0, 0)
TRAIN_END = datetime(2026, 7, 31, 23, 59, 59)
VAL_END = datetime(2026, 9, 30, 23, 59, 59)
TEST_END = datetime(2026, 12, 31, 23, 59, 59)

def get_period(dt: datetime) -> str:
    """Return TRAIN, VALIDATION, or TEST based on datetime."""
    if dt <= TRAIN_END:
        return "TRAIN"
    elif dt <= VAL_END:
        return "VALIDATION"
    else:
        return "TEST"

@dataclass
class DatasetConfig:
    name: str
    num_campaigns: int
    num_contacts: int
    num_touchpoints: int
    num_opportunities: int
    num_creatives: int
    num_audiences: int
    
    # Anomaly injection rates (proportional)
    duplicate_revenue_count: int
    post_conversion_touches_count: int
    currency_mismatch_count: int
    missing_cost_campaigns_count: int
    unsupported_identity_links_count: int

# STARTER: Lightweight and fast for development, testing, and UI live demo
STARTER_CONFIG = DatasetConfig(
    name="STARTER",
    num_campaigns=50,
    num_contacts=1000,
    num_touchpoints=4000,
    num_opportunities=200,
    num_creatives=30,
    num_audiences=15,
    duplicate_revenue_count=10,
    post_conversion_touches_count=25,
    currency_mismatch_count=8,
    missing_cost_campaigns_count=5,
    unsupported_identity_links_count=15
)

# FULL BASELINE: The exact volume required by the specification
FULL_BASELINE_CONFIG = DatasetConfig(
    name="FULL_BASELINE",
    num_campaigns=500,
    num_contacts=50000,
    num_touchpoints=200000,
    num_opportunities=10000,
    num_creatives=150,
    num_audiences=50,
    duplicate_revenue_count=100,
    post_conversion_touches_count=500,
    currency_mismatch_count=25,
    missing_cost_campaigns_count=15,
    unsupported_identity_links_count=200
)

# Alias for backwards compatibility
FULL_CONFIG = FULL_BASELINE_CONFIG

def get_dataset_config(name_or_alias: str) -> DatasetConfig:
    """Return appropriate DatasetConfig based on name or alias."""
    cleaned = (name_or_alias or "").strip().upper().replace(" ", "_").replace("-", "_")
    if cleaned in ("FULL", "FULL_BASELINE", "FULLBASELINE"):
        return FULL_BASELINE_CONFIG
    elif cleaned == "STARTER":
        return STARTER_CONFIG
    else:
        raise ValueError(f"Unknown dataset config: '{name_or_alias}'. Supported: 'STARTER', 'FULL_BASELINE'.")

