"""FastAPI REST API router implementing all platform endpoints."""
from datetime import datetime, timedelta
from typing import Optional, List
from pathlib import Path
import json

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, asc

from backend.app.models.database import get_db, reset_db
from backend.app.models.entities import (
    Campaign, Channel, Creative, Audience, Contact, WebSession,
    Touchpoint, Lead, Opportunity, Order, CostRecord, AttributionResult,
    AnomalyIssue, ValidationResult, DataGenerationRun
)
from backend.app.schemas.api_models import (
    HealthResponse, DashboardSummaryResponse, DashboardTrendsResponse, TrendDataPoint,
    CampaignListResponse, CampaignListItem, CampaignDetailResponse,
    CustomerJourneyResponse, JourneyEvent,
    AttributionRunRequest, AttributionCompareResponse, AttributionCompareItem,
    AnomalyDashboardResponse, AnomalyIssueItem,
    GeneratorRunRequest, GeneratorStatusResponse,
    AuthMeResponse, ActorProfileResponse,
    ChronologicalPeriodsResponse, ChronologicalPeriodItem
)
from backend.app.security.rbac import (
    RoleEnum, require_roles, get_current_user,
    ACTOR_PERSONAS, ROLE_PERMISSIONS, ROLE_ALLOWED_PAGES
)
from backend.app.analytics.financials import FinancialEngine
from backend.app.attribution.engine import AttributionEngine
from backend.app.analytics.anomaly_detector import AnomalyDetectionEngine
from backend.app.validation.validator import ValidationEngine
from backend.app.generators.synthetic_data import SyntheticDataGenerator
from backend.app.generators.config import (
    STARTER_CONFIG, FULL_CONFIG, BASE_CURRENCY, get_dataset_config,
    PERIOD_START, TRAIN_END, VAL_END, TEST_END
)
from backend.app.services.export_service import ExportService

router = APIRouter(prefix="/api")

# ==========================================
# 0. Auth & RBAC Endpoints
# ==========================================
@router.get("/auth/me", response_model=AuthMeResponse)
def get_current_actor(user: dict = Depends(get_current_user)):
    """Return the profile, assigned permissions, and allowed page views for current actor."""
    return user

@router.get("/auth/actors", response_model=List[ActorProfileResponse])
def list_available_actors():
    """List the 5 primary actors defined in business requirements for live role-switching."""
    actors = []
    for role, persona in ACTOR_PERSONAS.items():
        p = persona.copy()
        p["permissions"] = [perm.value for perm in ROLE_PERMISSIONS[role]]
        p["allowed_pages"] = ROLE_ALLOWED_PAGES[role]
        actors.append(p)
    return actors

# ==========================================
# 1. Health Endpoint
# ==========================================
@router.get("/health", response_model=HealthResponse)
def health_check(db: Session = Depends(get_db)):
    try:
        # Simple DB check
        campaign_count = db.query(Campaign).count()
        db_status = f"CONNECTED ({campaign_count} campaigns)"
    except Exception as e:
        db_status = f"ERROR: {str(e)}"

    return {
        "status": "HEALTHY",
        "version": "1.0.0",
        "database": db_status,
        "timestamp": datetime.utcnow().isoformat()
    }

# ==========================================
# 2. Dashboard Endpoints
# ==========================================
@router.get("/dashboard/summary", response_model=DashboardSummaryResponse)
def get_dashboard_summary(
    user: dict = Depends(require_roles(RoleEnum.MARKETING_SALES_OPS, RoleEnum.ANALYST, RoleEnum.SYSTEM_ADMIN)),
    db: Session = Depends(get_db)
):
    engine = FinancialEngine(db)
    return engine.get_overall_summary()

@router.get("/dashboard/trends", response_model=DashboardTrendsResponse)
def get_dashboard_trends(
    user: dict = Depends(require_roles(RoleEnum.MARKETING_SALES_OPS, RoleEnum.ANALYST, RoleEnum.SYSTEM_ADMIN)),
    db: Session = Depends(get_db)
):
    """Monthly trends for spend, revenue, and conversions throughout 2026."""
    months = [
        ("Jan 2026", "2026-01-01", "2026-01-31"),
        ("Feb 2026", "2026-02-01", "2026-02-28"),
        ("Mar 2026", "2026-03-01", "2026-03-31"),
        ("Apr 2026", "2026-04-01", "2026-04-30"),
        ("May 2026", "2026-05-01", "2026-05-31"),
        ("Jun 2026", "2026-06-01", "2026-06-30"),
        ("Jul 2026", "2026-07-01", "2026-07-31"),
        ("Aug 2026", "2026-08-01", "2026-08-31"),
        ("Sep 2026", "2026-09-01", "2026-09-30"),
        ("Oct 2026", "2026-10-01", "2026-10-31"),
        ("Nov 2026", "2026-11-01", "2026-11-30"),
        ("Dec 2026", "2026-12-01", "2026-12-31"),
    ]

    trends = []
    for label, start_s, end_s in months:
        start_dt = datetime.fromisoformat(f"{start_s}T00:00:00")
        end_dt = datetime.fromisoformat(f"{end_s}T23:59:59")

        # Spend
        spend = (
            db.query(func.sum(CostRecord.amount))
            .filter(
                CostRecord.currency == BASE_CURRENCY,
                CostRecord.recorded_date >= start_dt,
                CostRecord.recorded_date <= end_dt
            )
            .scalar() or 0.0
        )

        # Revenue & Conversions
        rev_conv = (
            db.query(
                func.sum(Order.amount),
                func.count(Order.order_id)
            )
            .filter(
                Order.status == "COMPLETED",
                Order.is_duplicate_flag == False,
                Order.order_date >= start_dt,
                Order.order_date <= end_dt
            )
            .first()
        )
        rev = rev_conv[0] or 0.0
        conv = rev_conv[1] or 0

        trends.append(TrendDataPoint(
            period=label,
            spend=round(spend, 2),
            revenue=round(rev, 2),
            conversions=conv
        ))

    return DashboardTrendsResponse(monthly_trends=trends)

# ==========================================
# 3. Campaign Endpoints
# ==========================================
@router.get("/campaigns", response_model=CampaignListResponse)
def list_campaigns(
    channel_id: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: str = "attributed_revenue",
    sort_order: str = "desc",
    page: int = Query(1, ge=1),
    limit: int = Query(15, ge=1, le=100),
    user: dict = Depends(require_roles(RoleEnum.MARKETING_SALES_OPS, RoleEnum.SUPPORT_AGENT, RoleEnum.ANALYST, RoleEnum.SYSTEM_ADMIN)),
    db: Session = Depends(get_db)
):
    fin = FinancialEngine(db)
    items = fin.get_campaign_roi_breakdown(model_id="MDL-MULTI-TOUCH")

    # In-memory filter
    if channel_id:
        items = [i for i in items if i["channel_id"] == channel_id]
    if status:
        st = status.upper()
        if st == "INCOMPLETE":
            items = [i for i in items if i.get("status_display") == "INCOMPLETE" or i.get("roi_status") == "UNAVAILABLE_MISSING_COST"]
        else:
            items = [i for i in items if i["status"].upper() == st]
    if search:
        q = search.lower()
        items = [i for i in items if q in i["campaign_name"].lower() or q in i["campaign_id"].lower()]

    # Sort
    reverse = (sort_order.lower() == "desc")
    if sort_by in ["budget", "actual_spend", "attributed_revenue", "leads", "conversions"]:
        items.sort(key=lambda x: x.get(sort_by, 0.0), reverse=reverse)
    elif sort_by == "roi":
        items.sort(key=lambda x: (x.get("roi") is not None, x.get("roi") or -999999), reverse=reverse)

    total = len(items)
    start_idx = (page - 1) * limit
    paginated = items[start_idx:start_idx + limit]

    return CampaignListResponse(
        total=total,
        page=page,
        limit=limit,
        items=paginated
    )

@router.get("/campaigns/{campaign_id}", response_model=CampaignDetailResponse)
def get_campaign_detail(
    campaign_id: str,
    user: dict = Depends(require_roles(RoleEnum.MARKETING_SALES_OPS, RoleEnum.SUPPORT_AGENT, RoleEnum.ANALYST, RoleEnum.SYSTEM_ADMIN)),
    db: Session = Depends(get_db)
):
    cmp = db.query(Campaign).filter(Campaign.campaign_id == campaign_id).first()
    if not cmp:
        raise HTTPException(status_code=404, detail="Campaign not found")

    channel = db.query(Channel).filter(Channel.channel_id == cmp.channel_id).first()
    channel_name = channel.name if channel else cmp.channel_id

    # Spend
    spend = (
        db.query(func.sum(CostRecord.amount))
        .filter(CostRecord.campaign_id == cmp.campaign_id, CostRecord.currency == BASE_CURRENCY)
        .scalar() or 0.0
    )

    # Attributed revenue
    attr_rev = (
        db.query(func.sum(AttributionResult.attributed_revenue))
        .filter(AttributionResult.campaign_id == cmp.campaign_id, AttributionResult.model_id == "MDL-MULTI-TOUCH")
        .scalar() or 0.0
    )

    # Counts
    touches = db.query(Touchpoint).filter(Touchpoint.campaign_id == cmp.campaign_id).count()
    leads = db.query(Lead).filter(Lead.campaign_id == cmp.campaign_id).count()
    opps = db.query(Opportunity).filter(Opportunity.campaign_id == cmp.campaign_id).count()
    convs = (
        db.query(func.count(func.distinct(AttributionResult.order_id)))
        .filter(AttributionResult.campaign_id == cmp.campaign_id)
        .scalar() or 0
    )

    cost_count = (
        db.query(func.count(CostRecord.cost_id))
        .filter(CostRecord.campaign_id == cmp.campaign_id)
        .scalar() or 0
    )

    if cost_count == 0 or spend <= 0.0:
        roi = None
        roi_status = "UNAVAILABLE_MISSING_COST"
        status_display = "INCOMPLETE"
        is_incomplete = True
    else:
        roi = round(((attr_rev - spend) / spend) * 100, 2)
        roi_status = "CALCULATED"
        status_display = cmp.status
        is_incomplete = False

    # Creatives & Audiences
    creatives = [
        {"creative_id": cl.creative.creative_id, "name": cl.creative.name, "format": cl.creative.creative_format}
        for cl in cmp.creative_links if cl.creative
    ]
    audiences = [
        {"audience_id": al.audience.audience_id, "name": al.audience.name, "segment": al.audience.segment_type}
        for al in cmp.audience_links if al.audience
    ]

    return CampaignDetailResponse(
        campaign_id=cmp.campaign_id,
        name=cmp.name,
        channel_id=cmp.channel_id,
        channel_name=channel_name,
        budget=cmp.budget,
        actual_spend=round(spend, 2),
        status=cmp.status,
        status_display=status_display,
        is_incomplete=is_incomplete,
        start_date=cmp.start_date.isoformat(),
        end_date=cmp.end_date.isoformat() if cmp.end_date else None,
        creatives=creatives,
        audiences=audiences,
        touchpoints_count=touches,
        leads_count=leads,
        opportunities_count=opps,
        conversions_count=convs,
        attributed_revenue=round(attr_rev, 2),
        roi=roi,
        roi_status=roi_status
    )

# ==========================================
# 4. Customer Journey Explorer
# ==========================================
@router.get("/contacts")
def list_contacts(
    search: Optional[str] = None,
    lifecycle_stage: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Contact)
    if user["role"] == RoleEnum.CUSTOMER_PROSPECT.value:
        cid = user.get("contact_id") or "CON-2026-000001"
        query = query.filter(Contact.contact_id == cid)
    else:
        if lifecycle_stage:
            query = query.filter(Contact.lifecycle_stage == lifecycle_stage)
        if search:
            q = f"%{search}%"
            query = query.filter((Contact.contact_id.like(q)) | (Contact.email.like(q)) | (Contact.first_name.like(q)) | (Contact.last_name.like(q)))

    contacts = query.limit(limit).all()
    return [
        {
            "contact_id": c.contact_id,
            "name": f"{c.first_name} {c.last_name}",
            "email": c.email,
            "lifecycle_stage": c.lifecycle_stage,
            "first_seen_at": c.first_seen_at.isoformat()
        }
        for c in contacts
    ]

@router.get("/contacts/{contact_id}/journey", response_model=CustomerJourneyResponse)
def get_customer_journey(
    contact_id: str,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Customer/Prospect can only inspect their own contact journey
    if user["role"] == RoleEnum.CUSTOMER_PROSPECT.value:
        allowed_cid = user.get("contact_id") or "CON-2026-000001"
        if contact_id != allowed_cid:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: Customer '{user['name']}' is restricted to their personal journey ({allowed_cid})."
            )

    contact = db.query(Contact).filter(Contact.contact_id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    events: List[JourneyEvent] = []

    # 1. Sessions
    sessions = db.query(WebSession).filter(WebSession.contact_id == contact_id).all()
    for s in sessions:
        events.append(JourneyEvent(
            event_id=s.session_id,
            event_type="SESSION",
            timestamp=s.started_at.isoformat(),
            title="Web Session Started",
            description=f"Device: {s.device_type} | Landing: {s.landing_page} | Referrer: {s.referrer or 'Direct'}",
            status="ACTIVE"
        ))

    # 2. Touchpoints
    touches = db.query(Touchpoint).filter(Touchpoint.contact_id == contact_id).all()
    for t in touches:
        events.append(JourneyEvent(
            event_id=t.touchpoint_id,
            event_type="TOUCHPOINT",
            timestamp=t.occurred_at.isoformat(),
            title=f"Marketing Touch: {t.touch_type}",
            description=f"Medium: {t.channel_medium} | Interaction Cost: ₹{t.interaction_cost:.2f}",
            channel=t.channel_id,
            campaign_id=t.campaign_id,
            amount=t.interaction_cost
        ))

    # 3. Leads
    leads = db.query(Lead).filter(Lead.contact_id == contact_id).all()
    for l in leads:
        events.append(JourneyEvent(
            event_id=l.lead_id,
            event_type="LEAD",
            timestamp=l.created_at.isoformat(),
            title="Lead Created",
            description=f"Source: {l.lead_source} | Status: {l.status}",
            campaign_id=l.campaign_id,
            status=l.status
        ))

    # 4. Opportunities
    opps = db.query(Opportunity).filter(Opportunity.contact_id == contact_id).all()
    for op in opps:
        events.append(JourneyEvent(
            event_id=op.opportunity_id,
            event_type="OPPORTUNITY",
            timestamp=op.created_at.isoformat(),
            title=f"Opportunity ({op.stage})",
            description=f"Expected Revenue: ₹{op.expected_revenue:,.2f}",
            campaign_id=op.campaign_id,
            amount=op.expected_revenue,
            status=op.stage
        ))

    # 5. Orders
    orders = db.query(Order).filter(Order.contact_id == contact_id).all()
    for o in orders:
        events.append(JourneyEvent(
            event_id=o.order_id,
            event_type="ORDER",
            timestamp=o.order_date.isoformat(),
            title="Closed Revenue Order",
            description=f"Order #{o.order_number} | Amount: ₹{o.amount:,.2f} | Status: {o.status}" + (" [DUPLICATE QUARANTINED]" if o.is_duplicate_flag else ""),
            amount=o.amount,
            status=o.status,
            is_anomaly=o.is_duplicate_flag
        ))

    # Sort strictly chronologically
    events.sort(key=lambda x: x.timestamp)

    return CustomerJourneyResponse(
        contact_id=contact.contact_id,
        contact_name=f"{contact.first_name} {contact.last_name}",
        email=contact.email,
        lifecycle_stage=contact.lifecycle_stage,
        first_seen_at=contact.first_seen_at.isoformat(),
        total_events=len(events),
        events=events
    )

# ==========================================
# 5. Attribution Endpoints
# ==========================================
@router.get("/attribution/compare", response_model=AttributionCompareResponse)
def compare_attribution_models(
    evaluation_period: Optional[str] = None,
    user: dict = Depends(require_roles(RoleEnum.ANALYST, RoleEnum.SYSTEM_ADMIN)),
    db: Session = Depends(get_db)
):
    fin = FinancialEngine(db)
    ft_items = {c["campaign_id"]: c for c in fin.get_campaign_roi_breakdown("MDL-FIRST-TOUCH", evaluation_period=evaluation_period)}
    lt_items = {c["campaign_id"]: c for c in fin.get_campaign_roi_breakdown("MDL-LAST-TOUCH", evaluation_period=evaluation_period)}
    mt_items = {c["campaign_id"]: c for c in fin.get_campaign_roi_breakdown("MDL-MULTI-TOUCH", evaluation_period=evaluation_period)}

    channel_map = {c.channel_id: c.name for c in db.query(Channel).all()}

    comparisons = []
    for cid, mt_item in mt_items.items():
        ft = ft_items.get(cid, {})
        lt = lt_items.get(cid, {})
        ch_name = channel_map.get(mt_item["channel_id"], mt_item["channel_id"])

        comparisons.append(AttributionCompareItem(
            campaign_id=cid,
            campaign_name=mt_item["campaign_name"],
            channel_name=ch_name,
            spend=mt_item["actual_spend"],
            first_touch_revenue=ft.get("attributed_revenue", 0.0),
            last_touch_revenue=lt.get("attributed_revenue", 0.0),
            multi_touch_revenue=mt_item.get("attributed_revenue", 0.0),
            first_touch_roi=ft.get("roi"),
            last_touch_roi=lt.get("roi"),
            multi_touch_roi=mt_item.get("roi")
        ))

    comparisons.sort(key=lambda x: x.multi_touch_revenue, reverse=True)

    # Calculate exact totals across all campaigns
    total_ft = round(sum(c.first_touch_revenue for c in comparisons), 2)
    total_lt = round(sum(c.last_touch_revenue for c in comparisons), 2)
    total_mt = round(sum(c.multi_touch_revenue for c in comparisons), 2)

    order_query = db.query(func.sum(Order.amount)).filter(
        Order.status == "COMPLETED",
        Order.is_duplicate_flag == False,
        Order.currency == BASE_CURRENCY
    )
    total_eligible = round(order_query.scalar() or 0.0, 2)

    is_reconciled = (
        abs(total_ft - total_mt) < 0.05 and 
        abs(total_lt - total_mt) < 0.05
    )

    return AttributionCompareResponse(
        campaigns=comparisons,
        total_eligible_revenue=total_eligible,
        total_first_touch_revenue=total_ft,
        total_last_touch_revenue=total_lt,
        total_multi_touch_revenue=total_mt,
        is_fully_reconciled=is_reconciled
    )

@router.post("/attribution/run")
def run_attribution_recalculation(
    req: AttributionRunRequest,
    user: dict = Depends(require_roles(RoleEnum.ANALYST, RoleEnum.SYSTEM_ADMIN)),
    db: Session = Depends(get_db)
):
    engine = AttributionEngine(db, lookback_days=req.lookback_days)
    summary = engine.run_all_models()
    return summary

@router.get("/attribution/results")
def list_attribution_results(
    model_id: Optional[str] = None,
    campaign_id: Optional[str] = None,
    evaluation_period: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    user: dict = Depends(require_roles(RoleEnum.ANALYST, RoleEnum.SYSTEM_ADMIN)),
    db: Session = Depends(get_db)
):
    query = db.query(AttributionResult)
    if model_id:
        query = query.filter(AttributionResult.model_id == model_id)
    if campaign_id:
        query = query.filter(AttributionResult.campaign_id == campaign_id)
    if evaluation_period:
        query = query.filter(AttributionResult.evaluation_period == evaluation_period.upper())

    total = query.count()
    results = query.order_by(desc(AttributionResult.conversion_timestamp)).offset((page - 1) * limit).limit(limit).all()

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "items": [
            {
                "result_id": r.result_id,
                "model_id": r.model_id,
                "opportunity_id": r.opportunity_id,
                "order_id": r.order_id,
                "campaign_id": r.campaign_id,
                "channel_id": r.channel_id,
                "touchpoint_id": r.touchpoint_id,
                "attribution_weight": r.attribution_weight,
                "attributed_revenue": r.attributed_revenue,
                "touchpoint_timestamp": r.touchpoint_timestamp.isoformat(),
                "conversion_timestamp": r.conversion_timestamp.isoformat(),
                "evaluation_period": r.evaluation_period
            }
            for r in results
        ]
    }

# ==========================================
# 6. Analytics Endpoints
# ==========================================
@router.get("/analytics/roi")
def get_roi_analytics(
    model_id: str = "MDL-MULTI-TOUCH",
    user: dict = Depends(require_roles(RoleEnum.MARKETING_SALES_OPS, RoleEnum.ANALYST, RoleEnum.SYSTEM_ADMIN)),
    db: Session = Depends(get_db)
):
    fin = FinancialEngine(db)
    return {
        "model_id": model_id,
        "campaigns": fin.get_campaign_roi_breakdown(model_id=model_id)
    }

@router.get("/analytics/channels")
def get_channel_analytics(
    model_id: str = "MDL-MULTI-TOUCH",
    user: dict = Depends(require_roles(RoleEnum.MARKETING_SALES_OPS, RoleEnum.ANALYST, RoleEnum.SYSTEM_ADMIN)),
    db: Session = Depends(get_db)
):
    fin = FinancialEngine(db)
    return {
        "model_id": model_id,
        "channels": fin.get_channel_performance(model_id=model_id)
    }

# ==========================================
# 7. Anomaly & Quality Endpoints
# ==========================================
@router.get("/anomalies", response_model=AnomalyDashboardResponse)
def get_anomalies_dashboard(
    issue_type: Optional[str] = None,
    severity: Optional[str] = None,
    user: dict = Depends(require_roles(RoleEnum.ANALYST, RoleEnum.SYSTEM_ADMIN)),
    db: Session = Depends(get_db)
):
    detector = AnomalyDetectionEngine(db)
    
    # Self-healing: if anomaly issues table is empty but campaigns exist, auto-run detection!
    if db.query(AnomalyIssue).count() == 0 and db.query(Campaign).count() > 0:
        detector.run_detection()

    # Get ground truth evaluation
    eval_metrics = detector.evaluate_against_ground_truth()

    query = db.query(AnomalyIssue)
    if issue_type:
        query = query.filter(AnomalyIssue.issue_type == issue_type)
    if severity:
        query = query.filter(AnomalyIssue.severity == severity.upper())

    issues = query.order_by(desc(AnomalyIssue.detection_timestamp)).all()

    # Aggregate counts
    all_issues = db.query(AnomalyIssue).all()
    by_type = {}
    by_sev = {}
    for iss in all_issues:
        by_type[iss.issue_type] = by_type.get(iss.issue_type, 0) + 1
        by_sev[iss.severity] = by_sev.get(iss.severity, 0) + 1

    return AnomalyDashboardResponse(
        total_anomalies=len(all_issues),
        by_type=by_type,
        by_severity=by_sev,
        evaluation_metrics=eval_metrics,
        issues=[
            AnomalyIssueItem(
                issue_id=i.issue_id,
                entity_type=i.entity_type,
                entity_id=i.entity_id,
                issue_type=i.issue_type,
                severity=i.severity,
                description=i.description,
                detection_timestamp=i.detection_timestamp.isoformat(),
                expected_decision=i.expected_decision,
                actual_decision=i.actual_decision,
                resolution_status=i.resolution_status,
                related_record_ids=i.related_record_ids
            )
            for i in issues
        ]
    )

# ==========================================
# 8. Validation Endpoints
# ==========================================
@router.get("/validation/report")
def get_validation_report(
    user: dict = Depends(require_roles(RoleEnum.ANALYST, RoleEnum.SYSTEM_ADMIN)),
    db: Session = Depends(get_db)
):
    val = ValidationEngine(db)
    return val.run_all_validations()

@router.post("/validation/run")
def trigger_validation_run(
    user: dict = Depends(require_roles(RoleEnum.ANALYST, RoleEnum.SYSTEM_ADMIN)),
    db: Session = Depends(get_db)
):
    val = ValidationEngine(db)
    return val.run_all_validations()

@router.get("/evaluation/chronological-periods", response_model=ChronologicalPeriodsResponse)
def get_chronological_evaluation_periods(
    user: dict = Depends(require_roles(RoleEnum.ANALYST, RoleEnum.SYSTEM_ADMIN)),
    db: Session = Depends(get_db)
):
    """Return chronological evaluation period splitting, date boundaries, and partition metrics."""
    periods_def = [
        {
            "period_code": "TRAIN",
            "name": "Training Period",
            "start_date": PERIOD_START.isoformat(),
            "end_date": TRAIN_END.isoformat(),
            "duration_days": (TRAIN_END - PERIOD_START).days + 1,
            "purpose": "Model calibration, initial touchpoint weight discovery, baseline conversion paths."
        },
        {
            "period_code": "VALIDATION",
            "name": "Validation Period",
            "start_date": (TRAIN_END + timedelta(seconds=1)).isoformat(),
            "end_date": VAL_END.isoformat(),
            "duration_days": (VAL_END - TRAIN_END).days,
            "purpose": "Hyperparameter tuning, lookback window optimization (30d vs 60d vs 90d), anomaly threshold tuning."
        },
        {
            "period_code": "TEST",
            "name": "Test Period (Out-of-Sample)",
            "start_date": (VAL_END + timedelta(seconds=1)).isoformat(),
            "end_date": TEST_END.isoformat(),
            "duration_days": (TEST_END - VAL_END).days,
            "purpose": "Strict out-of-sample attribution benchmarking, simulated financial ROI reconciliation, anomaly generalization."
        }
    ]

    items = []
    for p in periods_def:
        start_dt = datetime.fromisoformat(p["start_date"])
        end_dt = datetime.fromisoformat(p["end_date"])

        # Orders & revenue in this period
        orders = (
            db.query(Order)
            .filter(
                Order.order_date >= start_dt,
                Order.order_date <= end_dt,
                Order.status == "COMPLETED",
                Order.is_duplicate_flag == False
            )
            .all()
        )
        orders_count = len(orders)
        order_revenue = round(sum(o.amount for o in orders), 2)

        # Multi-touch attributed revenue in this period
        attr_results = (
            db.query(AttributionResult)
            .filter(
                AttributionResult.conversion_timestamp >= start_dt,
                AttributionResult.conversion_timestamp <= end_dt,
                AttributionResult.model_id == "MDL-MULTI-TOUCH"
            )
            .all()
        )
        attributed_revenue = round(sum(r.attributed_revenue for r in attr_results), 2)

        # Touchpoints in this period
        touch_count = (
            db.query(Touchpoint)
            .filter(
                Touchpoint.occurred_at >= start_dt,
                Touchpoint.occurred_at <= end_dt
            )
            .count()
        )

        # Spend in this period (INR only)
        spend = (
            db.query(func.sum(CostRecord.amount))
            .filter(
                CostRecord.recorded_date >= start_dt,
                CostRecord.recorded_date <= end_dt,
                CostRecord.currency == BASE_CURRENCY
            )
            .scalar() or 0.0
        )

        # Anomalies in this period
        anomalies_count = (
            db.query(AnomalyIssue)
            .filter(
                AnomalyIssue.detection_timestamp >= start_dt,
                AnomalyIssue.detection_timestamp <= end_dt
            )
            .count()
        )

        items.append(ChronologicalPeriodItem(
            period_code=p["period_code"],
            name=p["name"],
            start_date=p["start_date"],
            end_date=p["end_date"],
            duration_days=p["duration_days"],
            purpose=p["purpose"],
            orders_count=orders_count,
            order_revenue=order_revenue,
            attributed_revenue_multi_touch=attributed_revenue,
            touchpoints_count=touch_count,
            campaign_spend=round(spend, 2),
            anomalies_detected=anomalies_count
        ))

    return ChronologicalPeriodsResponse(
        status="SUCCESS",
        total_periods=len(items),
        boundaries_summary="Strictly chronological non-overlapping partitions across 2026",
        periods=items
    )

# ==========================================
# 9. Generator Endpoints
# ==========================================
@router.post("/generator/run")
def run_generator(
    req: GeneratorRunRequest,
    user: dict = Depends(require_roles(RoleEnum.SYSTEM_ADMIN)),
    db: Session = Depends(get_db)
):
    config = get_dataset_config(req.config_name)
    reset_db()
    gen = SyntheticDataGenerator(db, config=config, seed=req.seed)
    gen_result = gen.generate()

    # Automatically recompute attribution and anomaly detection
    att = AttributionEngine(db)
    att.run_all_models()
    det = AnomalyDetectionEngine(db)
    det.run_detection()

    return gen_result

@router.get("/generator/status", response_model=GeneratorStatusResponse)
def get_generator_status(
    user: dict = Depends(require_roles(RoleEnum.SYSTEM_ADMIN)),
    db: Session = Depends(get_db)
):
    last_run = db.query(DataGenerationRun).order_by(desc(DataGenerationRun.started_at)).first()
    if not last_run:
        return GeneratorStatusResponse(
            last_run_id=None,
            config_name=None,
            seed=None,
            status="NEVER_RUN",
            row_counts={},
            completed_at=None
        )

    row_counts = json.loads(last_run.row_counts_json) if last_run.row_counts_json else {}
    return GeneratorStatusResponse(
        last_run_id=last_run.run_id,
        config_name=last_run.config_name,
        seed=last_run.seed,
        status=last_run.status,
        row_counts=row_counts,
        completed_at=last_run.completed_at.isoformat() if last_run.completed_at else None
    )

# ==========================================
# 10. Exports Endpoints
# ==========================================
@router.get("/exports/list")
def list_exports(
    user: dict = Depends(require_roles(RoleEnum.ANALYST, RoleEnum.SYSTEM_ADMIN))
):
    manifest_dir = Path(__file__).resolve().parent.parent.parent.parent / "data" / "manifests"
    manifest_files = list(manifest_dir.glob("manifest_*.json")) if manifest_dir.exists() else []

    if manifest_files:
        # Sort by modification time to return the most recently generated manifest
        latest_manifest = sorted(manifest_files, key=lambda f: f.stat().st_mtime, reverse=True)[0]
        with open(latest_manifest, "r", encoding="utf-8") as f:
            manifest_data = json.load(f)
            return manifest_data

    return {"message": "No manifest found. Please run generator or export first."}

@router.get("/exports/download/{fmt}/{filename}")
def download_export_file(
    fmt: str,
    filename: str,
    user: dict = Depends(require_roles(RoleEnum.ANALYST, RoleEnum.SYSTEM_ADMIN))
):
    export_dir = Path(__file__).resolve().parent.parent.parent.parent / "data" / "exports" / fmt
    file_path = export_dir / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"File {filename} in {fmt} format not found")

    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type="application/octet-stream"
    )

@router.get("/exports/ground-truth/{fmt}")
def download_ground_truth_file(
    fmt: str,
    user: dict = Depends(require_roles(RoleEnum.ANALYST, RoleEnum.SYSTEM_ADMIN))
):
    clean_fmt = fmt.lower().strip()
    if clean_fmt not in ("csv", "json"):
        raise HTTPException(status_code=400, detail="Format must be 'csv' or 'json'")
    gt_dir = Path(__file__).resolve().parent.parent.parent.parent / "data" / "ground_truth"
    file_path = gt_dir / f"ground_truth.{clean_fmt}"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"Ground truth {clean_fmt} file not found")
    return FileResponse(
        path=str(file_path),
        filename=f"ground_truth.{clean_fmt}",
        media_type="application/octet-stream"
    )

# ==========================================
# 10. Matplotlib Visual Analytics Endpoints
# ==========================================
@router.get("/analytics/charts/generate")
def generate_matplotlib_charts(
    db: Session = Depends(get_db),
    user: dict = Depends(require_roles(RoleEnum.MARKETING_SALES_OPS, RoleEnum.ANALYST, RoleEnum.SYSTEM_ADMIN))
):
    """Generate high-resolution analytical charts using Python, Pandas, NumPy & Matplotlib."""
    from backend.app.analytics.visualizations import generate_all_analytics_charts
    return generate_all_analytics_charts(db)

@router.get("/analytics/charts/view/{chart_name}")
def view_matplotlib_chart(
    chart_name: str,
    db: Session = Depends(get_db)
):
    """Serve a generated Matplotlib PNG chart image."""
    charts_dir = Path(__file__).resolve().parent.parent.parent.parent / "data" / "exports" / "charts"
    if not chart_name.endswith(".png"):
        chart_name = f"{chart_name}.png"
    file_path = charts_dir / chart_name
    if not file_path.exists():
        from backend.app.analytics.visualizations import generate_all_analytics_charts
        generate_all_analytics_charts(db)
        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"Chart {chart_name} not found")
    return FileResponse(
        path=str(file_path),
        media_type="image/png"
    )
