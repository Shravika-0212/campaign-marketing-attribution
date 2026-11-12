"""Relational Database Schema & Entity Definitions for Marketing Attribution Platform.
Fully normalized relational entities with foreign keys, constraints, and audit trails.
"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    String, Integer, Float, Boolean, DateTime, ForeignKey, 
    Text, Index, UniqueConstraint, CheckConstraint
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.models.base import Base, TimestampMixin

# ==========================================
# 1. CHANNEL ENTITY
# ==========================================
class Channel(Base):
    __tablename__ = "channels"

    channel_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    channel_type: Mapped[str] = mapped_column(String(20), nullable=False)  # ONLINE, OFFLINE
    cost_structure: Mapped[str] = mapped_column(String(20), nullable=False) # CPC, CPM, FLAT, COMMISSION
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    campaigns = relationship("Campaign", back_populates="primary_channel")
    touchpoints = relationship("Touchpoint", back_populates="channel")
    cost_records = relationship("CostRecord", back_populates="channel")
    campaign_links = relationship("CampaignChannel", back_populates="channel")

# ==========================================
# 2. AUDIENCE ENTITY
# ==========================================
class Audience(Base):
    __tablename__ = "audiences"

    audience_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    segment_type: Mapped[str] = mapped_column(String(50), nullable=False) # B2B_ENTERPRISE, SMB, RETARGETING, PROSPECT
    target_criteria: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    campaign_links = relationship("CampaignAudience", back_populates="audience")

# ==========================================
# 3. CREATIVE ENTITY
# ==========================================
class Creative(Base):
    __tablename__ = "creatives"

    creative_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    creative_format: Mapped[str] = mapped_column(String(50), nullable=False) # BANNER, VIDEO, TEXT, EMAIL_TEMPLATE
    asset_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    message_theme: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    campaign_links = relationship("CampaignCreative", back_populates="creative")
    touchpoints = relationship("Touchpoint", back_populates="creative")

# ==========================================
# 4. CAMPAIGN ENTITY
# ==========================================
class Campaign(Base, TimestampMixin):
    __tablename__ = "campaigns"

    campaign_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    channel_id: Mapped[str] = mapped_column(String(50), ForeignKey("channels.channel_id"), nullable=False)
    budget: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="USD")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="ACTIVE") # DRAFT, ACTIVE, PAUSED, COMPLETED
    start_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    primary_channel = relationship("Channel", back_populates="campaigns")
    channel_links = relationship("CampaignChannel", back_populates="campaign")
    audience_links = relationship("CampaignAudience", back_populates="campaign")
    creative_links = relationship("CampaignCreative", back_populates="campaign")
    touchpoints = relationship("Touchpoint", back_populates="campaign")
    leads = relationship("Lead", back_populates="campaign")
    opportunities = relationship("Opportunity", back_populates="campaign")
    cost_records = relationship("CostRecord", back_populates="campaign")
    attribution_results = relationship("AttributionResult", back_populates="campaign")

    __table_args__ = (
        Index("idx_campaigns_status", "status"),
        Index("idx_campaigns_channel", "channel_id"),
        Index("idx_campaigns_dates", "start_date", "end_date"),
    )

# ==========================================
# 5. CONTACT ENTITY
# ==========================================
class Contact(Base):
    __tablename__ = "contacts"

    contact_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(150), nullable=False, unique=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    lifecycle_stage: Mapped[str] = mapped_column(String(30), nullable=False, default="SUBSCRIBER") # SUBSCRIBER, LEAD, MQL, SQL, OPPORTUNITY, CUSTOMER
    first_seen_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    identities = relationship("ContactIdentity", back_populates="contact")
    web_sessions = relationship("WebSession", back_populates="contact")
    touchpoints = relationship("Touchpoint", back_populates="contact")
    leads = relationship("Lead", back_populates="contact")
    opportunities = relationship("Opportunity", back_populates="contact")
    orders = relationship("Order", back_populates="contact")

    __table_args__ = (
        Index("idx_contacts_email", "email"),
        Index("idx_contacts_stage", "lifecycle_stage"),
    )

# ==========================================
# 6. WEB SESSION ENTITY
# ==========================================
class WebSession(Base):
    __tablename__ = "web_sessions"

    session_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    contact_id: Mapped[Optional[str]] = mapped_column(String(50), ForeignKey("contacts.contact_id"), nullable=True)
    anonymous_cookie_id: Mapped[str] = mapped_column(String(100), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    ended_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    device_type: Mapped[str] = mapped_column(String(30), nullable=False) # DESKTOP, MOBILE, TABLET
    landing_page: Mapped[str] = mapped_column(String(255), nullable=False)
    referrer: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_authenticated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    contact = relationship("Contact", back_populates="web_sessions")
    touchpoints = relationship("Touchpoint", back_populates="session")

    __table_args__ = (
        Index("idx_sessions_contact", "contact_id"),
        Index("idx_sessions_cookie", "anonymous_cookie_id"),
        Index("idx_sessions_started", "started_at"),
    )

# ==========================================
# 7. TOUCHPOINT ENTITY
# ==========================================
class Touchpoint(Base):
    __tablename__ = "touchpoints"

    touchpoint_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    contact_id: Mapped[Optional[str]] = mapped_column(String(50), ForeignKey("contacts.contact_id"), nullable=True)
    campaign_id: Mapped[str] = mapped_column(String(50), ForeignKey("campaigns.campaign_id"), nullable=False)
    channel_id: Mapped[str] = mapped_column(String(50), ForeignKey("channels.channel_id"), nullable=False)
    creative_id: Mapped[Optional[str]] = mapped_column(String(50), ForeignKey("creatives.creative_id"), nullable=True)
    session_id: Mapped[Optional[str]] = mapped_column(String(50), ForeignKey("web_sessions.session_id"), nullable=True)
    touch_type: Mapped[str] = mapped_column(String(30), nullable=False) # CLICK, IMPRESSION, EMAIL_OPEN, WEBINAR, IN_PERSON, CALL
    channel_medium: Mapped[str] = mapped_column(String(20), nullable=False) # ONLINE, OFFLINE
    occurred_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    interaction_cost: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    contact = relationship("Contact", back_populates="touchpoints")
    campaign = relationship("Campaign", back_populates="touchpoints")
    channel = relationship("Channel", back_populates="touchpoints")
    creative = relationship("Creative", back_populates="touchpoints")
    session = relationship("WebSession", back_populates="touchpoints")
    attribution_results = relationship("AttributionResult", back_populates="touchpoint")

    __table_args__ = (
        Index("idx_touchpoints_contact", "contact_id"),
        Index("idx_touchpoints_campaign", "campaign_id"),
        Index("idx_touchpoints_occurred", "occurred_at"),
        Index("idx_touchpoints_contact_date", "contact_id", "occurred_at"),
    )

# ==========================================
# 8. LEAD ENTITY
# ==========================================
class Lead(Base):
    __tablename__ = "leads"

    lead_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    contact_id: Mapped[str] = mapped_column(String(50), ForeignKey("contacts.contact_id"), nullable=False)
    campaign_id: Mapped[str] = mapped_column(String(50), ForeignKey("campaigns.campaign_id"), nullable=False)
    lead_source: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="NEW") # NEW, CONTACTED, QUALIFIED, UNQUALIFIED
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    contact = relationship("Contact", back_populates="leads")
    campaign = relationship("Campaign", back_populates="leads")
    opportunities = relationship("Opportunity", back_populates="lead")

    __table_args__ = (
        Index("idx_leads_contact", "contact_id"),
        Index("idx_leads_campaign", "campaign_id"),
        Index("idx_leads_status", "status"),
    )

# ==========================================
# 9. OPPORTUNITY ENTITY
# ==========================================
class Opportunity(Base, TimestampMixin):
    __tablename__ = "opportunities"

    opportunity_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    contact_id: Mapped[str] = mapped_column(String(50), ForeignKey("contacts.contact_id"), nullable=False)
    lead_id: Mapped[Optional[str]] = mapped_column(String(50), ForeignKey("leads.lead_id"), nullable=True)
    campaign_id: Mapped[str] = mapped_column(String(50), ForeignKey("campaigns.campaign_id"), nullable=False)
    stage: Mapped[str] = mapped_column(String(30), nullable=False) # PROSPECTING, QUALIFICATION, PROPOSAL, NEGOTIATION, CLOSED_WON, CLOSED_LOST
    expected_revenue: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    close_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    contact = relationship("Contact", back_populates="opportunities")
    lead = relationship("Lead", back_populates="opportunities")
    campaign = relationship("Campaign", back_populates="opportunities")
    orders = relationship("Order", back_populates="opportunity")
    attribution_results = relationship("AttributionResult", back_populates="opportunity")

    __table_args__ = (
        Index("idx_opps_contact", "contact_id"),
        Index("idx_opps_stage", "stage"),
        Index("idx_opps_close_date", "close_date"),
    )

# ==========================================
# 10. ORDER ENTITY (CLOSED REVENUE)
# ==========================================
class Order(Base):
    __tablename__ = "orders"

    order_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    opportunity_id: Mapped[str] = mapped_column(String(50), ForeignKey("opportunities.opportunity_id"), nullable=False)
    contact_id: Mapped[str] = mapped_column(String(50), ForeignKey("contacts.contact_id"), nullable=False)
    order_number: Mapped[str] = mapped_column(String(50), nullable=False)
    order_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="USD")
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="COMPLETED") # PENDING, COMPLETED, CANCELLED, REFUNDED
    is_duplicate_flag: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False) # For tracking injected duplicate order anomaly
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    opportunity = relationship("Opportunity", back_populates="orders")
    contact = relationship("Contact", back_populates="orders")
    attribution_results = relationship("AttributionResult", back_populates="order")

    __table_args__ = (
        Index("idx_orders_opp", "opportunity_id"),
        Index("idx_orders_contact", "contact_id"),
        Index("idx_orders_date", "order_date"),
        Index("idx_orders_number", "order_number"),
    )

# ==========================================
# 11. COST RECORD ENTITY
# ==========================================
class CostRecord(Base):
    __tablename__ = "cost_records"

    cost_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    campaign_id: Mapped[str] = mapped_column(String(50), ForeignKey("campaigns.campaign_id"), nullable=False)
    channel_id: Mapped[str] = mapped_column(String(50), ForeignKey("channels.channel_id"), nullable=False)
    recorded_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="USD")
    cost_type: Mapped[str] = mapped_column(String(30), nullable=False) # MEDIA_SPEND, AGENCY_FEE, PRODUCTION
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    campaign = relationship("Campaign", back_populates="cost_records")
    channel = relationship("Channel", back_populates="cost_records")

    __table_args__ = (
        Index("idx_costs_campaign", "campaign_id"),
        Index("idx_costs_date", "recorded_date"),
    )

# ==========================================
# 12. ATTRIBUTION RESULT ENTITY
# ==========================================
class AttributionResult(Base):
    __tablename__ = "attribution_results"

    result_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    model_id: Mapped[str] = mapped_column(String(50), ForeignKey("attribution_models.model_id"), nullable=False)
    opportunity_id: Mapped[str] = mapped_column(String(50), ForeignKey("opportunities.opportunity_id"), nullable=False)
    order_id: Mapped[str] = mapped_column(String(50), ForeignKey("orders.order_id"), nullable=False)
    campaign_id: Mapped[str] = mapped_column(String(50), ForeignKey("campaigns.campaign_id"), nullable=False)
    channel_id: Mapped[str] = mapped_column(String(50), ForeignKey("channels.channel_id"), nullable=False)
    touchpoint_id: Mapped[str] = mapped_column(String(100), ForeignKey("touchpoints.touchpoint_id"), nullable=False)
    attribution_weight: Mapped[float] = mapped_column(Float, nullable=False) # Credit: 0.0 to 1.0
    attributed_revenue: Mapped[float] = mapped_column(Float, nullable=False) # Weight * Order Amount
    touchpoint_timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    conversion_timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    evaluation_period: Mapped[str] = mapped_column(String(20), nullable=False) # TRAIN, VALIDATION, TEST
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    model = relationship("AttributionModel", back_populates="results")
    opportunity = relationship("Opportunity", back_populates="attribution_results")
    order = relationship("Order", back_populates="attribution_results")
    campaign = relationship("Campaign", back_populates="attribution_results")
    touchpoint = relationship("Touchpoint", back_populates="attribution_results")

    __table_args__ = (
        Index("idx_att_model_campaign", "model_id", "campaign_id"),
        Index("idx_att_order", "order_id"),
        Index("idx_att_period", "evaluation_period"),
    )

# ==========================================
# 13. BRIDGE TABLES (MANY-TO-MANY)
# ==========================================
class CampaignChannel(Base):
    __tablename__ = "campaign_channels"

    campaign_id: Mapped[str] = mapped_column(String(50), ForeignKey("campaigns.campaign_id"), primary_key=True)
    channel_id: Mapped[str] = mapped_column(String(50), ForeignKey("channels.channel_id"), primary_key=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    campaign = relationship("Campaign", back_populates="channel_links")
    channel = relationship("Channel", back_populates="campaign_links")

class CampaignAudience(Base):
    __tablename__ = "campaign_audiences"

    campaign_id: Mapped[str] = mapped_column(String(50), ForeignKey("campaigns.campaign_id"), primary_key=True)
    audience_id: Mapped[str] = mapped_column(String(50), ForeignKey("audiences.audience_id"), primary_key=True)

    campaign = relationship("Campaign", back_populates="audience_links")
    audience = relationship("Audience", back_populates="campaign_links")

class CampaignCreative(Base):
    __tablename__ = "campaign_creatives"

    campaign_id: Mapped[str] = mapped_column(String(50), ForeignKey("campaigns.campaign_id"), primary_key=True)
    creative_id: Mapped[str] = mapped_column(String(50), ForeignKey("creatives.creative_id"), primary_key=True)

    campaign = relationship("Campaign", back_populates="creative_links")
    creative = relationship("Creative", back_populates="campaign_links")

# ==========================================
# 14. IDENTITY RESOLUTION TABLE
# ==========================================
class ContactIdentity(Base):
    __tablename__ = "contact_identities"

    identity_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    contact_id: Mapped[str] = mapped_column(String(50), ForeignKey("contacts.contact_id"), nullable=False)
    identity_type: Mapped[str] = mapped_column(String(30), nullable=False) # COOKIE, EMAIL_HASH, DEVICE_ID
    identity_value: Mapped[str] = mapped_column(String(100), nullable=False)
    evidence_source: Mapped[str] = mapped_column(String(100), nullable=False) # FORM_SUBMISSION, LOGIN, EMAIL_CLICK
    first_observed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    contact = relationship("Contact", back_populates="identities")

    __table_args__ = (
        Index("idx_identities_val_type", "identity_type", "identity_value"),
    )

# ==========================================
# 15. AUDIT EVENT HISTORY TABLE
# ==========================================
class EventHistory(Base):
    __tablename__ = "event_history"

    history_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    entity_name: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(50), nullable=False)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False) # STAGE_CHANGE, ATTRIBUTION_CALCULATED, ANOMALY_DETECTED
    old_state: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    new_state: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    details_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("idx_events_entity", "entity_name", "entity_id"),
        Index("idx_events_timestamp", "timestamp"),
    )

# ==========================================
# 16. ANOMALY ISSUES TABLE
# ==========================================
class AnomalyIssue(Base):
    __tablename__ = "anomaly_issues"

    issue_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False) # ORDER, TOUCHPOINT, COST, SESSION
    entity_id: Mapped[str] = mapped_column(String(100), nullable=False)
    issue_type: Mapped[str] = mapped_column(String(60), nullable=False)
    # Types:
    # 1. DUPLICATE_REVENUE
    # 2. POST_CONVERSION_TOUCHPOINT
    # 3. CURRENCY_MISMATCH
    # 4. MISSING_CAMPAIGN_COST
    # 5. UNSUPPORTED_IDENTITY_LINK
    severity: Mapped[str] = mapped_column(String(20), nullable=False) # CRITICAL, HIGH, MEDIUM, LOW
    description: Mapped[str] = mapped_column(Text, nullable=False)
    detection_timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    expected_decision: Mapped[str] = mapped_column(String(100), nullable=False) # What the system should do
    actual_decision: Mapped[str] = mapped_column(String(100), nullable=False) # What the engine decided
    resolution_status: Mapped[str] = mapped_column(String(30), default="QUARANTINED", nullable=False) # QUARANTINED, RESOLVED, IGNORED
    related_record_ids: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("idx_anomalies_type", "issue_type"),
        Index("idx_anomalies_severity", "severity"),
    )

# ==========================================
# 17. ATTRIBUTION MODEL CONFIG TABLE
# ==========================================
class AttributionModel(Base):
    __tablename__ = "attribution_models"

    model_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    model_code: Mapped[str] = mapped_column(String(40), nullable=False, unique=True) # FIRST_TOUCH, LAST_TOUCH, MULTI_TOUCH_LINEAR
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    lookback_window_days: Mapped[int] = mapped_column(Integer, default=90, nullable=False)
    version: Mapped[str] = mapped_column(String(20), default="1.0.0", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    results = relationship("AttributionResult", back_populates="model")

# ==========================================
# 18. DATA GENERATION RUN AUDIT
# ==========================================
class DataGenerationRun(Base):
    __tablename__ = "data_generation_runs"

    run_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    config_name: Mapped[str] = mapped_column(String(30), nullable=False) # STARTER, FULL
    seed: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False) # RUNNING, COMPLETED, FAILED
    row_counts_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    checksums_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

# ==========================================
# 19. VALIDATION AUDIT RESULTS
# ==========================================
class ValidationResult(Base):
    __tablename__ = "validation_results"

    validation_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    run_timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    rule_code: Mapped[str] = mapped_column(String(50), nullable=False)
    rule_name: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False) # PASS, FAIL, WARN
    records_checked: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    records_passed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    records_failed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    details_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
