"""Pydantic schemas for API request validation and structured responses."""
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field

# ==========================================
# Generic & Health Schemas
# ==========================================
class HealthResponse(BaseModel):
    status: str
    version: str
    database: str
    timestamp: str

# ==========================================
# Dashboard & Analytics Schemas
# ==========================================
class DashboardSummaryResponse(BaseModel):
    currency: str
    total_campaigns: int
    total_leads: int
    total_opportunities: int
    total_conversions: int
    total_budget: float
    total_campaign_spend: float
    total_closed_revenue: float
    attributed_revenue_multi_touch: float
    unattributed_revenue: float
    excluded_duplicate_revenue: float
    excluded_duplicate_orders_count: int
    overall_roi: Optional[float]
    cost_per_lead: float
    cost_per_acquisition: float
    revenue_by_model: Dict[str, float]

class TrendDataPoint(BaseModel):
    period: str
    spend: float
    revenue: float
    conversions: int

class DashboardTrendsResponse(BaseModel):
    monthly_trends: List[TrendDataPoint]

# ==========================================
# Campaign Schemas
# ==========================================
class CampaignListItem(BaseModel):
    campaign_id: str
    campaign_name: str
    channel_id: str
    status: str
    budget: float
    actual_spend: float
    attributed_revenue: float
    leads: int
    opportunities: int
    conversions: int
    roi: Optional[float]
    roi_status: str
    cost_per_lead: Optional[float]
    cost_per_acquisition: Optional[float]
    start_date: str
    end_date: Optional[str]

class CampaignListResponse(BaseModel):
    total: int
    page: int
    limit: int
    items: List[CampaignListItem]

class CampaignDetailResponse(BaseModel):
    campaign_id: str
    name: str
    channel_id: str
    channel_name: str
    budget: float
    actual_spend: float
    status: str
    start_date: str
    end_date: Optional[str]
    creatives: List[Dict[str, Any]]
    audiences: List[Dict[str, Any]]
    touchpoints_count: int
    leads_count: int
    opportunities_count: int
    conversions_count: int
    attributed_revenue: float
    roi: Optional[float]

# ==========================================
# Customer Journey Schemas
# ==========================================
class JourneyEvent(BaseModel):
    event_id: str
    event_type: str # TOUCHPOINT, SESSION, LEAD, OPPORTUNITY, ORDER
    timestamp: str
    title: str
    description: str
    channel: Optional[str] = None
    campaign_id: Optional[str] = None
    amount: Optional[float] = None
    status: Optional[str] = None
    is_anomaly: bool = False

class CustomerJourneyResponse(BaseModel):
    contact_id: str
    contact_name: str
    email: str
    lifecycle_stage: str
    first_seen_at: str
    total_events: int
    events: List[JourneyEvent]

# ==========================================
# Attribution Schemas
# ==========================================
class AttributionRunRequest(BaseModel):
    lookback_days: int = Field(90, ge=1, le=365)

class AttributionCompareItem(BaseModel):
    campaign_id: str
    campaign_name: str
    channel_name: str
    spend: float
    first_touch_revenue: float
    last_touch_revenue: float
    multi_touch_revenue: float
    first_touch_roi: Optional[float]
    last_touch_roi: Optional[float]
    multi_touch_roi: Optional[float]

class AttributionCompareResponse(BaseModel):
    campaigns: List[AttributionCompareItem]

# ==========================================
# Anomaly Schemas
# ==========================================
class AnomalyIssueItem(BaseModel):
    issue_id: str
    entity_type: str
    entity_id: str
    issue_type: str
    severity: str
    description: str
    detection_timestamp: str
    expected_decision: str
    actual_decision: str
    resolution_status: str
    related_record_ids: Optional[str]

class AnomalyDashboardResponse(BaseModel):
    total_anomalies: int
    by_type: Dict[str, int]
    by_severity: Dict[str, int]
    evaluation_metrics: Dict[str, Any]
    issues: List[AnomalyIssueItem]

# ==========================================
# Generator & Validation Schemas
# ==========================================
class GeneratorRunRequest(BaseModel):
    config_name: str = Field("STARTER", pattern="^(STARTER|FULL)$")
    seed: int = Field(20261022)

class GeneratorStatusResponse(BaseModel):
    last_run_id: Optional[str]
    config_name: Optional[str]
    seed: Optional[int]
    status: Optional[str]
    row_counts: Dict[str, int]
    completed_at: Optional[str]
