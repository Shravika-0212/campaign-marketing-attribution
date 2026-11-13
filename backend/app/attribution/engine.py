"""Marketing Attribution Engine.
Implements First-Touch, Last-Touch, and Multi-Touch (Linear / Equal-Weight) attribution models.
Applies lookback windows, chronological filtering, post-conversion exclusion,
and numerical tolerance credit reconciliation (sum(weights) == 1.0).
"""
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.app.models.entities import (
    AttributionModel, AttributionResult, Order, Opportunity,
    Touchpoint, Campaign, Channel
)
from backend.app.generators.config import get_period, BASE_CURRENCY

class AttributionEngine:
    def __init__(self, db: Session, lookback_days: int = 90):
        self.db = db
        self.lookback_days = lookback_days

    def run_all_models(self) -> Dict[str, Any]:
        """Execute attribution across all three models: First-Touch, Last-Touch, Multi-Touch."""
        # Clear existing attribution results to allow idempotent re-runs
        self.db.query(AttributionResult).delete()
        self.db.commit()

        ft_count = self.calculate_model_attribution("MDL-FIRST-TOUCH", "FIRST_TOUCH")
        lt_count = self.calculate_model_attribution("MDL-LAST-TOUCH", "LAST_TOUCH")
        mt_count = self.calculate_model_attribution("MDL-MULTI-TOUCH", "MULTI_TOUCH_LINEAR")

        return {
            "status": "COMPLETED",
            "models_executed": ["FIRST_TOUCH", "LAST_TOUCH", "MULTI_TOUCH_LINEAR"],
            "records_created": {
                "first_touch": ft_count,
                "last_touch": lt_count,
                "multi_touch": mt_count,
                "total": ft_count + lt_count + mt_count
            }
        }

    def calculate_model_attribution(self, model_id: str, model_code: str) -> int:
        """Calculate attribution for a specific model."""
        # Fetch valid, completed, non-duplicate orders matching base currency
        orders = (
            self.db.query(Order)
            .filter(
                Order.status == "COMPLETED",
                Order.is_duplicate_flag == False,
                Order.currency == BASE_CURRENCY
            )
            .order_by(Order.order_date.asc(), Order.order_id.asc())
            .all()
        )

        results_to_insert: List[AttributionResult] = []
        result_counter = 1

        for order in orders:
            conv_time = order.order_date
            lookback_cutoff = conv_time - timedelta(days=self.lookback_days)

            # Query eligible touchpoints:
            # 1. Matches contact_id
            # 2. occurred_at <= conversion timestamp (strictly no post-conversion touchpoints)
            # 3. occurred_at >= lookback cutoff (e.g. 90 days lookback)
            # 4. Deterministic tie-breaking on occurred_at and touchpoint_id
            eligible_touches = (
                self.db.query(Touchpoint)
                .filter(
                    Touchpoint.contact_id == order.contact_id,
                    Touchpoint.occurred_at <= conv_time,
                    Touchpoint.occurred_at >= lookback_cutoff
                )
                .order_by(Touchpoint.occurred_at.asc(), Touchpoint.touchpoint_id.asc())
                .all()
            )

            if not eligible_touches:
                # Unattributed conversion: no eligible touchpoints found within lookback window
                continue

            evaluation_period = get_period(conv_time)

            if model_code == "FIRST_TOUCH":
                # Earliest eligible touchpoint receives 100% credit
                chosen_touch = eligible_touches[0]
                results_to_insert.append(AttributionResult(
                    result_id=f"ATT-{model_code[:2]}-{order.order_id}-{result_counter:04d}",
                    model_id=model_id,
                    opportunity_id=order.opportunity_id,
                    order_id=order.order_id,
                    campaign_id=chosen_touch.campaign_id,
                    channel_id=chosen_touch.channel_id,
                    touchpoint_id=chosen_touch.touchpoint_id,
                    attribution_weight=1.0,
                    attributed_revenue=round(order.amount * 1.0, 2),
                    touchpoint_timestamp=chosen_touch.occurred_at,
                    conversion_timestamp=conv_time,
                    evaluation_period=evaluation_period
                ))
                result_counter += 1

            elif model_code == "LAST_TOUCH":
                # Latest eligible touchpoint receives 100% credit
                chosen_touch = eligible_touches[-1]
                results_to_insert.append(AttributionResult(
                    result_id=f"ATT-{model_code[:2]}-{order.order_id}-{result_counter:04d}",
                    model_id=model_id,
                    opportunity_id=order.opportunity_id,
                    order_id=order.order_id,
                    campaign_id=chosen_touch.campaign_id,
                    channel_id=chosen_touch.channel_id,
                    touchpoint_id=chosen_touch.touchpoint_id,
                    attribution_weight=1.0,
                    attributed_revenue=round(order.amount * 1.0, 2),
                    touchpoint_timestamp=chosen_touch.occurred_at,
                    conversion_timestamp=conv_time,
                    evaluation_period=evaluation_period
                ))
                result_counter += 1

            elif model_code == "MULTI_TOUCH_LINEAR":
                # Equal weight (1/N) distributed across all N eligible touchpoints
                n = len(eligible_touches)
                weight = 1.0 / n
                total_attributed = 0.0

                for i, tp in enumerate(eligible_touches):
                    # Handle last touchpoint rounding adjustment so sum == order.amount exactly
                    if i == n - 1:
                        touch_rev = round(order.amount - total_attributed, 2)
                        touch_weight = round(1.0 - (weight * (n - 1)), 6)
                    else:
                        touch_rev = round(order.amount * weight, 2)
                        touch_weight = round(weight, 6)
                        total_attributed += touch_rev

                    results_to_insert.append(AttributionResult(
                        result_id=f"ATT-MT-{order.order_id}-{result_counter:04d}",
                        model_id=model_id,
                        opportunity_id=order.opportunity_id,
                        order_id=order.order_id,
                        campaign_id=tp.campaign_id,
                        channel_id=tp.channel_id,
                        touchpoint_id=tp.touchpoint_id,
                        attribution_weight=touch_weight,
                        attributed_revenue=touch_rev,
                        touchpoint_timestamp=tp.occurred_at,
                        conversion_timestamp=conv_time,
                        evaluation_period=evaluation_period
                    ))
                    result_counter += 1

        self.db.bulk_save_objects(results_to_insert)
        self.db.commit()
        return len(results_to_insert)
