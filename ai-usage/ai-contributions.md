# Detailed AI Contributions & Human Verification Matrix
**Candidate:** Fresher / Full-Stack & Data Analytics Engineer (Python Focus)  
**Challenge:** YottaFlex AI 72-Hour Coding Drive

---

## 1. Breakdown of Contributions

| Component | AI Role / Contribution | Human Review & Developer Verification | Modifications / Bug Fixes |
| :--- | :--- | :--- | :--- |
| **Database Architecture** | Generated SQLAlchemy 2.0 ORM schemas for all 21 tables. | Reviewed normalization, constraints, composite PKs, and WAL mode SQLite event listeners. | Confirmed table creation via SQLite inspector. |
| **Synthetic Data Generator** | Implemented multi-stage generation, journey simulation, deterministic IDs, and seed `20261022`. | Verified business logic flow (Campaign &rarr; Touchpoint &rarr; Session &rarr; Lead &rarr; Opportunity &rarr; Order). | Synchronized contact stage transition to `CUSTOMER` upon order conversion. |
| **Attribution Engine** | Wrote First-Touch, Last-Touch, and Multi-Touch linear engines with lookback window filtering. | Verified mathematical property that sum of attribution weights equals $1.000000 \pm 10^{-6}$. | Adjusted residual cent rounding absorption on final touchpoint. |
| **Financial & ROI Engine** | Wrote reconciliation calculations for budget vs spend, CPL, CPA, and ROI. | Ensured no division by zero for campaigns with zero or missing costs. | Fixed model prefix matching to query `MDL-MULTI-TOUCH` directly. |
| **Anomaly Detection Engine** | Implemented independent rule detection for 5 mandatory anomaly types without ground truth leakage. | Verified isolation of quarantined records into `anomaly_issues`. | Fixed ground truth logging so every unsupported session is registered. |
| **Ground Truth Evaluation** | Programmed Precision, Recall, and F1 calculations. | Audited confusion matrix (TP, FP, FN) against known injected cases. | Verified 1.0 F1 score across all 5 anomaly types. |
| **FastAPI REST API** | Implemented endpoints for dashboard, campaigns, journeys, attribution, anomalies, validation, and exports. | Inspected HTTP status codes, error handling, and Pydantic request models. | Upgraded `regex` parameter to `pattern` for Pydantic v2 compliance. |
| **React + TypeScript Frontend** | Built modern SaaS UI with 8 pages, Recharts charts, and Lucide icons. | Verified responsiveness, navigation, state management, and real API consumption. | Corrected `CampaignDetail` property interface binding in `CampaignsPage.tsx`. |
| **Automated Pytest Suite** | Generated 22 automated test cases. | Executed full test suite locally. | Downgraded Pytest from buggy 9.2.0 to stable 8.4.2 for Python 3.10 compatibility. |
