"""Anomaly Detection Engine for Marketing Attribution & ROI Platform.
Implements detection for all 5 mandatory anomaly scenarios independently of ground truth labels:
1. Duplicate Revenue (Orders counted more than once)
2. Post-Conversion Touchpoints (Touches after order date)
3. Spend Currency Mismatch (Incompatible currencies vs USD)
4. Missing Campaign Costs (Zero costs recorded for active campaigns)
5. Unsupported Identity Links (Anonymous sessions linked without evidence)

Includes evaluation against separate ground truth to compute Precision, Recall, and F1.
"""
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Set, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.app.models.entities import (
    AnomalyIssue, Order, Touchpoint, CostRecord, Campaign,
    WebSession, ContactIdentity
)
from backend.app.generators.config import BASE_CURRENCY

class AnomalyDetectionEngine:
    def __init__(self, db: Session):
        self.db = db

    def run_detection(self) -> Dict[str, Any]:
        """Detect all 5 anomaly types independently from raw database records."""
        # Clear existing detected anomalies to allow idempotent runs
        self.db.query(AnomalyIssue).delete()
        self.db.commit()

        issues: List[AnomalyIssue] = []
        issue_counter = 1

        # ==========================================
        # Scenario 1: Duplicate Revenue
        # ==========================================
        # Detect orders sharing the same order_number or duplicate orders for same opportunity
        dup_order_groups = (
            self.db.query(Order.order_number, func.count(Order.order_id))
            .filter(Order.status == "COMPLETED")
            .group_by(Order.order_number)
            .having(func.count(Order.order_id) > 1)
            .all()
        )
        for ord_num, count in dup_order_groups:
            matching_orders = (
                self.db.query(Order)
                .filter(Order.order_number == ord_num)
                .order_by(Order.created_at.asc())
                .all()
            )
            # The first order is legitimate; subsequent ones are duplicates
            for dup in matching_orders[1:]:
                issues.append(AnomalyIssue(
                    issue_id=f"ANO-2026-{issue_counter:06d}",
                    entity_type="ORDER",
                    entity_id=dup.order_id,
                    issue_type="DUPLICATE_REVENUE",
                    severity="CRITICAL",
                    description=f"Duplicate order {dup.order_id} references existing order_number {ord_num}. Revenue duplicate risk: ₹{dup.amount:.2f}",
                    expected_decision="REJECT_DUPLICATE_REVENUE",
                    actual_decision="EXCLUDED_FROM_FINANCIAL_TOTALS",
                    resolution_status="QUARANTINED",
                    related_record_ids=f"{matching_orders[0].order_id},{dup.opportunity_id}"
                ))
                issue_counter += 1

        # ==========================================
        # Scenario 2: Post-Conversion Touchpoints
        # ==========================================
        # Detect touchpoints for contacts occurring strictly after order_date
        completed_orders = (
            self.db.query(Order)
            .filter(Order.status == "COMPLETED", Order.is_duplicate_flag == False)
            .all()
        )
        for order in completed_orders:
            post_touches = (
                self.db.query(Touchpoint)
                .filter(
                    Touchpoint.contact_id == order.contact_id,
                    Touchpoint.occurred_at > order.order_date
                )
                .all()
            )
            for pt in post_touches:
                issues.append(AnomalyIssue(
                    issue_id=f"ANO-2026-{issue_counter:06d}",
                    entity_type="TOUCHPOINT",
                    entity_id=pt.touchpoint_id,
                    issue_type="POST_CONVERSION_TOUCHPOINT",
                    severity="HIGH",
                    description=f"Touchpoint {pt.touchpoint_id} occurred at {pt.occurred_at} after conversion timestamp {order.order_date}.",
                    expected_decision="EXCLUDE_FROM_ATTRIBUTION",
                    actual_decision="EXCLUDED_FROM_ATTRIBUTION_MODEL",
                    resolution_status="QUARANTINED",
                    related_record_ids=f"{order.order_id},{order.opportunity_id}"
                ))
                issue_counter += 1

        # ==========================================
        # Scenario 3: Spend Currency Mismatch
        # ==========================================
        currency_mismatches = (
            self.db.query(CostRecord)
            .filter(CostRecord.currency != BASE_CURRENCY)
            .all()
        )
        for cr in currency_mismatches:
            issues.append(AnomalyIssue(
                issue_id=f"ANO-2026-{issue_counter:06d}",
                entity_type="COST_RECORD",
                entity_id=cr.cost_id,
                issue_type="CURRENCY_MISMATCH",
                severity="MEDIUM",
                description=f"Cost record {cr.cost_id} uses currency '{cr.currency}', incompatible with base currency '{BASE_CURRENCY}'.",
                expected_decision="FLAG_CURRENCY_MISMATCH_EXCLUDE_FROM_ROI",
                actual_decision="FLAGGED_AND_EXCLUDED_FROM_RECONCILED_COSTS",
                resolution_status="QUARANTINED",
                related_record_ids=cr.campaign_id
            ))
            issue_counter += 1

        # ==========================================
        # Scenario 4: Missing Campaign Costs
        # ==========================================
        all_campaigns = self.db.query(Campaign).all()
        for cmp in all_campaigns:
            cost_count = (
                self.db.query(func.count(CostRecord.cost_id))
                .filter(CostRecord.campaign_id == cmp.campaign_id)
                .scalar()
            )
            if cost_count == 0:
                issues.append(AnomalyIssue(
                    issue_id=f"ANO-2026-{issue_counter:06d}",
                    entity_type="CAMPAIGN",
                    entity_id=cmp.campaign_id,
                    issue_type="MISSING_CAMPAIGN_COST",
                    severity="HIGH",
                    description=f"Campaign {cmp.campaign_id} ('{cmp.name}') has zero cost records. Spend data is missing.",
                    expected_decision="FLAG_MISSING_COST_MARK_ROI_UNAVAILABLE",
                    actual_decision="ROI_MARKED_UNAVAILABLE",
                    resolution_status="QUARANTINED",
                    related_record_ids=cmp.campaign_id
                ))
                issue_counter += 1

        # ==========================================
        # Scenario 5: Unsupported Identity Links
        # ==========================================
        # Detect web sessions with contact_id where no identity evidence exists for that cookie
        sessions_with_contacts = (
            self.db.query(WebSession)
            .filter(WebSession.contact_id.isnot(None))
            .all()
        )
        for sess in sessions_with_contacts:
            has_evidence = (
                self.db.query(ContactIdentity)
                .filter(
                    ContactIdentity.contact_id == sess.contact_id,
                    ContactIdentity.identity_value == sess.anonymous_cookie_id
                )
                .first()
            )
            if not has_evidence:
                issues.append(AnomalyIssue(
                    issue_id=f"ANO-2026-{issue_counter:06d}",
                    entity_type="WEB_SESSION",
                    entity_id=sess.session_id,
                    issue_type="UNSUPPORTED_IDENTITY_LINK",
                    severity="MEDIUM",
                    description=f"WebSession {sess.session_id} is linked to contact {sess.contact_id} without matching cookie {sess.anonymous_cookie_id} evidence in contact_identities.",
                    expected_decision="QUARANTINE_IDENTITY_LINK",
                    actual_decision="SESSION_LINK_QUARANTINED",
                    resolution_status="QUARANTINED",
                    related_record_ids=sess.contact_id
                ))
                issue_counter += 1

        # Save all detected issues
        self.db.bulk_save_objects(issues)
        self.db.commit()

        # Compute breakdown by type & severity
        type_counts = {}
        severity_counts = {}
        for issue in issues:
            type_counts[issue.issue_type] = type_counts.get(issue.issue_type, 0) + 1
            severity_counts[issue.severity] = severity_counts.get(issue.severity, 0) + 1

        return {
            "status": "COMPLETED",
            "total_anomalies_detected": len(issues),
            "by_issue_type": type_counts,
            "by_severity": severity_counts
        }

    def evaluate_against_ground_truth(self) -> Dict[str, Any]:
        """Compare detected anomalies against separate ground truth to measure Precision, Recall, and F1."""
        gt_path = Path(__file__).resolve().parent.parent.parent.parent / "data" / "ground_truth" / "ground_truth.json"
        if not gt_path.exists():
            return {"error": "Ground truth file not found. Please run data generator first."}

        with open(gt_path, "r", encoding="utf-8") as f:
            gt_data = json.load(f)

        # Ground truth set: (entity_type, entity_id, anomaly_type)
        gt_set: Set[Tuple[str, str, str]] = {
            (item["entity_type"], item["entity_id"], item["anomaly_type"])
            for item in gt_data
        }

        # Detected set: (entity_type, entity_id, issue_type)
        detected_issues = self.db.query(AnomalyIssue).all()
        detected_set: Set[Tuple[str, str, str]] = {
            (issue.entity_type, issue.entity_id, issue.issue_type)
            for issue in detected_issues
        }

        tp_set = gt_set.intersection(detected_set)
        fp_set = detected_set - gt_set
        fn_set = gt_set - detected_set

        tp = len(tp_set)
        fp = len(fp_set)
        fn = len(fn_set)

        precision = tp / (tp + fp) if (tp + fp) > 0 else 1.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 1.0
        f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

        # Detailed breakdown by anomaly type
        by_type_eval = {}
        for anomaly_type in [
            "DUPLICATE_REVENUE", "POST_CONVERSION_TOUCHPOINT", "CURRENCY_MISMATCH",
            "MISSING_CAMPAIGN_COST", "UNSUPPORTED_IDENTITY_LINK"
        ]:
            type_gt = {x for x in gt_set if x[2] == anomaly_type}
            type_det = {x for x in detected_set if x[2] == anomaly_type}
            type_tp = len(type_gt.intersection(type_det))
            type_fp = len(type_det - type_gt)
            type_fn = len(type_gt - type_det)
            t_prec = type_tp / (type_tp + type_fp) if (type_tp + type_fp) > 0 else 1.0
            t_rec = type_tp / (type_tp + type_fn) if (type_tp + type_fn) > 0 else 1.0
            t_f1 = (2 * t_prec * t_rec) / (t_prec + t_rec) if (t_prec + t_rec) > 0 else 0.0

            by_type_eval[anomaly_type] = {
                "ground_truth_count": len(type_gt),
                "detected_count": len(type_det),
                "true_positives": type_tp,
                "false_positives": type_fp,
                "false_negatives": type_fn,
                "precision": round(t_prec, 4),
                "recall": round(t_rec, 4),
                "f1_score": round(t_f1, 4)
            }

        return {
            "evaluation_status": "SUCCESS",
            "overall_metrics": {
                "total_ground_truth": len(gt_set),
                "total_detected": len(detected_set),
                "true_positives": tp,
                "false_positives": fp,
                "false_negatives": fn,
                "precision": round(precision, 4),
                "recall": round(recall, 4),
                "f1_score": round(f1, 4)
            },
            "by_anomaly_type": by_type_eval
        }
