# AI Usage & Prompt History Log
**Recruitment Drive:** YottaFlex AI 72-Hour Coding Challenge  
**Role:** Candidate / Full-Stack & Data Analytics Engineer (Python Focus)  
**AI Assistant:** Google DeepMind Antigravity Pair Programming Agent

---

## 1. Actual Prompt History & Interaction Log

### Prompt 1: Initial Requirements Ingestion & Architecture Formulation
> **User Prompt:**  
> "Act as a Senior Full-Stack Engineer, Data Engineer, Backend Architect, Frontend Developer, and Data Analytics Engineer. Your task is to design and implement a complete, professional, working application for the YottaFlex AI Recruitment Drive coding challenge: Marketing Attribution and ROI Analytics Platform..."
>  
> **AI Contribution:**  
> - Formulated end-to-end multi-tier architecture diagram.
> - Defined normalized 12 core relational entities + bridge + auditing tables in SQLAlchemy 2.0.
> - Outlined deterministic synthetic generator design with seed `20261022`.
> - Drafted Phase 1-9 milestone execution plan in `implementation_plan.md`.
>  
> **Human Review & Decision:**  
> - Inspected architecture to verify SQLite foreign keys (`PRAGMA foreign_keys = ON;`) and WAL mode were properly configured.
> - Confirmed base currency as USD and default lookback window as 90 days.

### Prompt 2: Core Entity Schema & Migration Execution
> **AI Contribution:**  
> - Implemented `backend/app/models/entities.py` defining 21 normalized tables.
> - Added composite primary keys for bridge tables (`CampaignChannel`, `CampaignAudience`, `CampaignCreative`).
> - Implemented `EventHistory`, `AnomalyIssue`, and `ValidationResult` audit tables.
>  
> **Human Review & Decision:**  
> - Verified that all 12 core tables were successfully initialized in SQLite.

### Prompt 3: Deterministic Data Generation & Ground Truth Engine
> **AI Contribution:**  
> - Created `backend/app/generators/synthetic_data.py` supporting both `STARTER` and `FULL` scale configurations.
> - Programmed deliberate injection of all 5 mandatory anomaly scenarios.
> - Programmed `GroundTruthTracker` exporting to `ground_truth.json` and `ground_truth.csv` with SHA-256 checksums.
>  
> **Human Review & Decision:**  
> - Fixed contact lifecycle transition synchronization so converted orders update `lifecycle_stage = 'CUSTOMER'`.
> - Tested reproducibility across runs and verified identical SHA-256 checksums (`07fe296b...`).

### Prompt 4: Attribution, Financial ROI & Anomaly Detection Engines
> **AI Contribution:**  
> - Built First-Touch, Last-Touch, and Multi-Touch (linear equal-weight) attribution engine.
> - Built reconciled ROI engine with safe handling of missing/zero campaign costs (preventing divide-by-zero).
> - Built independent anomaly detection engine detecting all 5 scenarios without ground truth leakage.
> - Created automated ground truth evaluation computing Precision, Recall, and F1.
>  
> **Human Review & Decision:**  
> - Corrected multi-touch model ID lookup in `financials.py` to match `MDL-MULTI-TOUCH`.
> - Verified that overall detection achieves 100% Precision, 100% Recall, and 1.0 F1 score.

### Prompt 5: Automated Testing Suite & Frontend Dashboard
> **AI Contribution:**  
> - Wrote 22 automated Pytest test cases covering models, attribution, financials, anomalies, and APIs.
> - Developed React + Vite + TypeScript dashboard across 8 pages with Tailwind CSS and Recharts.
> - Generated cryptographic export manifests, SQL seed dumps, and documentation.
>  
> **Human Review & Decision:**  
> - Resolved Pytest 9.2 NodeId compatibility issue on Python 3.10 by pinning to stable Pytest 8.4.2.
> - Fixed TypeScript property binding in `CampaignsPage.tsx`.
> - Verified full frontend build with 0 errors.
