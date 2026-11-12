# Testing & Validation Engine Documentation
**Platform:** Marketing Attribution and ROI Analytics Platform  
**Test Suite:** Pytest + FastAPI TestClient (22 automated test cases)

---

## 1. Automated Test Suite Overview

All core business engines, data generation, models, endpoints, and integrity checks are backed by automated tests located in `backend/tests/`:

1. `test_generator.py`:
   - Fixed seed (`20261022`) deterministic reproducibility check.
   - Deterministic ID formatting (`CMP-2026-000001`, `CON-2026-000001`, `TOUCH-CON-000001-000001`).
   - Referential parent-child foreign key integrity.
2. `test_attribution.py`:
   - Execution across First-Touch, Last-Touch, and Multi-Touch.
   - Verification that First-Touch and Last-Touch credit weights equal $1.0$.
   - Verification that Multi-Touch linear weights sum to exactly $1.000000$ per converted order.
   - Verification that zero post-conversion touchpoints receive attribution credit.
3. `test_financials.py`:
   - Closed revenue, spend, and overall ROI calculations.
   - Verification that zero-cost / missing-cost campaigns have `ROI = None` and status `UNAVAILABLE_MISSING_COST`.
   - Reconciled channel aggregation.
4. `test_anomalies.py`:
   - Verification that all 5 mandatory anomaly types are detected.
   - Mathematical verification of Precision = 1.0, Recall = 1.0, F1 = 1.0 against ground truth.
   - Verification that quarantined records populate `anomaly_issues`.
5. `test_api.py`:
   - Health check (`/api/health`).
   - Dashboard summary metrics (`/api/dashboard/summary`).
   - Campaign list, pagination, and detail views (`/api/campaigns`).
   - Customer journey explorer timeline (`/api/contacts/{id}/journey`).
   - Anomalies and validation report endpoints.
6. `test_chronological.py`:
   - Validation that Train, Validation, and Test period boundaries are chronological.
   - Verification of zero data leakage across period splits.

---

## 2. The 15 Automated Validation Rules

The Validation Engine (`backend/app/validation/validator.py`) inspects all 23,000+ generated records against 15 strict criteria:

| Rule Code | Rule Description | Threshold / Constraint | Result |
| :--- | :--- | :--- | :--- |
| **RULE-01** | Primary Key Uniqueness | Zero duplicate keys across all core tables | **PASS** |
| **RULE-02** | Foreign Key Integrity | Zero orphaned foreign key references | **PASS** |
| **RULE-03** | Valid Entity Relationships | All orders reference existing contacts and opps | **PASS** |
| **RULE-04** | Allowed Enum Values | All stages, types, statuses within allowed sets | **PASS** |
| **RULE-05** | Date Chronological Ordering | `session.ended_at >= session.started_at` | **PASS** |
| **RULE-06** | Lifecycle Transitions | Converted contacts transition to `CUSTOMER` | **PASS** |
| **RULE-07** | Duplicate Revenue Records | Duplicate orders flagged & quarantined | **WARN (Quarantined)** |
| **RULE-08** | Non-Negative Arithmetic | Revenue and spend amounts $> 0.0$ | **PASS** |
| **RULE-09** | Budget Consistency | All campaign budgets $> 0.0$ | **PASS** |
| **RULE-10** | Revenue Consistency | Order amounts reconcile with opportunity revenue | **PASS** |
| **RULE-11** | Attribution Credit Sum | Multi-touch weights sum to $100\%$ per order | **PASS** |
| **RULE-12** | Unsupported Identity Links | Sessions without identity proof quarantined | **WARN (Quarantined)** |
| **RULE-13** | Missing Campaign Costs | Zero-cost campaigns detected & marked unavailable | **WARN (Quarantined)** |
| **RULE-14** | Currency Compatibility | Non-USD spend records quarantined | **WARN (Quarantined)** |
| **RULE-15** | Post-Conversion Exclusion | Zero post-conversion touches receive attribution | **PASS** |
