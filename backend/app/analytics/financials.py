"""Financial Metrics, Attribution Revenue, and ROI Reconciliation Engine.
Calculates all financial KPIs directly from validated database source records.
Enforces base currency consistency (USD), duplicate revenue exclusion,
and safe handling of missing/zero campaign costs (no divide-by-zero).
"""
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.app.models.entities import (
    Campaign, Channel, CostRecord, Order, AttributionResult,
    Lead, Opportunity, AnomalyIssue
)
from backend.app.generators.config import BASE_CURRENCY

class FinancialEngine:
    def __init__(self, db: Session):
        self.db = db

    def get_overall_summary(self) -> Dict[str, Any]:
        """Aggregate top-level dashboard financial and marketing KPIs."""
        # Valid non-duplicate completed orders
        valid_orders_query = self.db.query(Order).filter(
            Order.status == "COMPLETED",
            Order.is_duplicate_flag == False,
            Order.currency == BASE_CURRENCY
        )
        total_closed_revenue = round(valid_orders_query.with_entities(func.sum(Order.amount)).scalar() or 0.0, 2)
        total_conversions = valid_orders_query.count()

        # Excluded duplicate revenue
        dup_orders_query = self.db.query(Order).filter(
            Order.status == "COMPLETED",
            Order.is_duplicate_flag == True
        )
        excluded_duplicate_revenue = round(dup_orders_query.with_entities(func.sum(Order.amount)).scalar() or 0.0, 2)
        excluded_duplicate_orders_count = dup_orders_query.count()

        # Total Campaign Spend (only valid base currency USD records)
        valid_costs_query = self.db.query(CostRecord).filter(
            CostRecord.currency == BASE_CURRENCY
        )
        total_campaign_spend = round(valid_costs_query.with_entities(func.sum(CostRecord.amount)).scalar() or 0.0, 2)

        # Total Campaign Budget
        total_budget = round(self.db.query(func.sum(Campaign.budget)).scalar() or 0.0, 2)

        # Total Counts
        total_campaigns = self.db.query(Campaign).count()
        total_leads = self.db.query(Lead).count()
        total_opportunities = self.db.query(Opportunity).count()

        # Attributed revenue by model
        model_map = {
            "FIRST_TOUCH": "MDL-FIRST-TOUCH",
            "LAST_TOUCH": "MDL-LAST-TOUCH",
            "MULTI_TOUCH_LINEAR": "MDL-MULTI-TOUCH"
        }
        model_revenues = {}
        for m_code, m_id in model_map.items():
            rev = (
                self.db.query(func.sum(AttributionResult.attributed_revenue))
                .filter(AttributionResult.model_id == m_id)
                .scalar() or 0.0
            )
            model_revenues[m_code] = round(rev, 2)

        # Default model for headline ROI is MULTI_TOUCH_LINEAR
        headline_attributed_rev = model_revenues.get("MULTI_TOUCH_LINEAR", 0.0)
        unattributed_revenue = round(max(0.0, total_closed_revenue - headline_attributed_rev), 2)

        overall_roi: Optional[float] = None
        if total_campaign_spend > 0:
            overall_roi = round(((headline_attributed_rev - total_campaign_spend) / total_campaign_spend) * 100, 2)

        cost_per_lead = round(total_campaign_spend / total_leads, 2) if total_leads > 0 else 0.0
        cost_per_acquisition = round(total_campaign_spend / total_conversions, 2) if total_conversions > 0 else 0.0

        return {
            "currency": BASE_CURRENCY,
            "total_campaigns": total_campaigns,
            "total_leads": total_leads,
            "total_opportunities": total_opportunities,
            "total_conversions": total_conversions,
            "total_budget": total_budget,
            "total_campaign_spend": total_campaign_spend,
            "total_closed_revenue": total_closed_revenue,
            "attributed_revenue_multi_touch": headline_attributed_rev,
            "unattributed_revenue": unattributed_revenue,
            "excluded_duplicate_revenue": excluded_duplicate_revenue,
            "excluded_duplicate_orders_count": excluded_duplicate_orders_count,
            "overall_roi": overall_roi,
            "cost_per_lead": cost_per_lead,
            "cost_per_acquisition": cost_per_acquisition,
            "revenue_by_model": model_revenues
        }

    def get_campaign_roi_breakdown(self, model_id: str = "MDL-MULTI-TOUCH") -> List[Dict[str, Any]]:
        """Calculate detailed ROI, Spend, Revenue, CPL, CPA per campaign."""
        campaigns = self.db.query(Campaign).all()
        breakdown = []

        for cmp in campaigns:
            # Reconciled USD spend
            actual_spend = (
                self.db.query(func.sum(CostRecord.amount))
                .filter(CostRecord.campaign_id == cmp.campaign_id, CostRecord.currency == BASE_CURRENCY)
                .scalar() or 0.0
            )
            actual_spend = round(actual_spend, 2)

            # Check if campaign has missing cost anomaly
            cost_record_count = (
                self.db.query(CostRecord)
                .filter(CostRecord.campaign_id == cmp.campaign_id)
                .count()
            )

            # Attributed revenue for chosen model_id
            attr_rev = (
                self.db.query(func.sum(AttributionResult.attributed_revenue))
                .filter(
                    AttributionResult.campaign_id == cmp.campaign_id,
                    AttributionResult.model_id == model_id
                )
                .scalar() or 0.0
            )
            attr_rev = round(attr_rev, 2)

            leads_count = self.db.query(Lead).filter(Lead.campaign_id == cmp.campaign_id).count()
            opps_count = self.db.query(Opportunity).filter(Opportunity.campaign_id == cmp.campaign_id).count()
            conversions_count = (
                self.db.query(func.count(func.distinct(AttributionResult.order_id)))
                .filter(
                    AttributionResult.campaign_id == cmp.campaign_id,
                    AttributionResult.model_id == model_id
                )
                .scalar() or 0
            )

            # Safe ROI calculation
            roi: Optional[float] = None
            roi_status: str = "CALCULATED"

            if cost_record_count == 0 or actual_spend <= 0.0:
                roi = None
                roi_status = "UNAVAILABLE_MISSING_COST"
            else:
                roi = round(((attr_rev - actual_spend) / actual_spend) * 100, 2)

            cpl = round(actual_spend / leads_count, 2) if (leads_count > 0 and actual_spend > 0) else None
            cpa = round(actual_spend / conversions_count, 2) if (conversions_count > 0 and actual_spend > 0) else None

            breakdown.append({
                "campaign_id": cmp.campaign_id,
                "campaign_name": cmp.name,
                "channel_id": cmp.channel_id,
                "status": cmp.status,
                "budget": cmp.budget,
                "actual_spend": actual_spend,
                "attributed_revenue": attr_rev,
                "leads": leads_count,
                "opportunities": opps_count,
                "conversions": conversions_count,
                "roi": roi,
                "roi_status": roi_status,
                "cost_per_lead": cpl,
                "cost_per_acquisition": cpa,
                "start_date": cmp.start_date.isoformat(),
                "end_date": cmp.end_date.isoformat() if cmp.end_date else None
            })

        # Sort descending by attributed revenue
        breakdown.sort(key=lambda x: x["attributed_revenue"], reverse=True)
        return breakdown

    def get_channel_performance(self, model_id: str = "MDL-MULTI-TOUCH") -> List[Dict[str, Any]]:
        """Calculate spend, attributed revenue, and ROI aggregated by channel."""
        channels = self.db.query(Channel).all()
        channel_metrics = []

        for ch in channels:
            # Spend
            spend = (
                self.db.query(func.sum(CostRecord.amount))
                .filter(CostRecord.channel_id == ch.channel_id, CostRecord.currency == BASE_CURRENCY)
                .scalar() or 0.0
            )
            spend = round(spend, 2)

            # Attributed revenue
            revenue = (
                self.db.query(func.sum(AttributionResult.attributed_revenue))
                .filter(
                    AttributionResult.channel_id == ch.channel_id,
                    AttributionResult.model_id == model_id
                )
                .scalar() or 0.0
            )
            revenue = round(revenue, 2)

            conversions = (
                self.db.query(func.count(func.distinct(AttributionResult.order_id)))
                .filter(
                    AttributionResult.channel_id == ch.channel_id,
                    AttributionResult.model_id == model_id
                )
                .scalar() or 0
            )

            roi = round(((revenue - spend) / spend) * 100, 2) if spend > 0 else None

            channel_metrics.append({
                "channel_id": ch.channel_id,
                "channel_name": ch.name,
                "channel_type": ch.channel_type,
                "cost_structure": ch.cost_structure,
                "spend": spend,
                "attributed_revenue": revenue,
                "conversions": conversions,
                "roi": roi
            })

        channel_metrics.sort(key=lambda x: x["attributed_revenue"], reverse=True)
        return channel_metrics
