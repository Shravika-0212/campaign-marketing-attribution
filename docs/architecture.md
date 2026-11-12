# System Architecture & Technical Design
**Platform:** Marketing Attribution and ROI Analytics Platform  
**Author:** Senior Full-Stack & Analytics Engineer (Python Focus)

---

## 1. Architectural Blueprint

The platform is designed following a modular, layered clean architecture:

```
┌─────────────────────────────────────────────────────────────┐
│                   React + Vite Dashboard                    │
│   (TypeScript, Tailwind CSS, Recharts, Lucide React Icons)  │
└──────────────────────────────┬──────────────────────────────┘
                               │ HTTP / JSON REST APIs
┌──────────────────────────────▼──────────────────────────────┐
│                    FastAPI Backend Router                   │
│      (CORS Middleware, Pydantic v2 Request/Response Validation)│
└──────────────┬──────────────────────────────┬───────────────┘
               │                              │
┌──────────────▼──────────────┐┌──────────────▼───────────────┐
│     Core Business Engines   ││   Data & Validation Engines  │
│  - Attribution Engine       ││  - Synthetic Generator (Seed)│
│  - Financial & ROI Engine   ││  - 15 Validation Rules Engine│
│  - Anomaly Detection Engine ││  - Export & Manifest Service │
└──────────────┬──────────────┘└──────────────┬───────────────┘
               │                              │
┌──────────────▼──────────────────────────────▼───────────────┐
│                 SQLAlchemy 2.0 ORM Layer                    │
│   (Normalized Relational Entities, Indexes, Bridge Tables)  │
└──────────────────────────────┬──────────────────────────────┘
                               │ PRAGMA foreign_keys = ON; WAL
┌──────────────────────────────▼──────────────────────────────┐
│                   SQLite Embedded Database                  │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Component Design & Layer Responsibilities

### A. Presentation Layer (`frontend/src/`)
- Built using **React 18**, **Vite**, **TypeScript**, and **Tailwind CSS**.
- Pure client-side data binding consuming REST endpoints (`/api/*`).
- Interactive visualizations powered by **Recharts** (Area charts, bar charts, conversion funnels).
- 8 dedicated pages:
  1. `OverviewPage`: Executive KPIs, trend charts, model comparisons, financial integrity guard.
  2. `CampaignsPage`: Sortable, filterable campaign table with detail drawer.
  3. `JourneyPage`: Contact search and chronological interactive timeline.
  4. `AttributionPage`: Model comparison analysis, lookback window parameterization.
  5. `RoiPage`: Unit economics (CPL, CPA, ROI), channel efficiency scorecard.
  6. `AnomaliesPage`: 5 anomaly scenarios, ground truth evaluation scorecard (Precision/Recall/F1).
  7. `GeneratorPage`: Dataset scale selection (`STARTER` vs `FULL`), seed control, 15 validation rules runner.
  8. `ReportsPage`: CSV, JSON, SQL seed downloads, data dictionary, cryptographic manifests.

### B. Application & API Layer (`backend/app/api/` & `backend/app/schemas/`)
- Built with **FastAPI** and **Pydantic v2**.
- Automatic schema validation and OpenAPI `/docs` and `/redoc` documentation generation.
- Stateless HTTP handlers utilizing SQLAlchemy session dependency injection (`get_db`).

### C. Domain & Processing Engines (`backend/app/`)
- **Attribution Engine (`backend/app/attribution/engine.py`):**
  - First-Touch: $100\%$ weight to earliest touchpoint within lookback window.
  - Last-Touch: $100\%$ weight to latest touchpoint before conversion.
  - Multi-Touch: Linear equal-weight ($1/N$) credit totaling $1.000000$ per converted order.
  - Lookback window enforcement (default 90 days).
  - Strict exclusion of post-conversion touchpoints.
- **Financial Reconciliation Engine (`backend/app/analytics/financials.py`):**
  - Deduplicated revenue recognition from completed order records.
  - Base currency filtering (`USD`).
  - Safe zero-cost / missing cost handling (ROI marked `None / Unavailable`, preventing divide-by-zero errors).
  - CPL and CPA calculations.
- **Anomaly Detection Engine (`backend/app/analytics/anomaly_detector.py`):**
  - Independent rule-based detection for all 5 mandatory scenarios.
  - Population of `anomaly_issues` table.
  - Ground truth evaluation computing Precision, Recall, and F1-Score.
- **Data Validation Engine (`backend/app/validation/validator.py`):**
  - Automated evaluation across 15 relational, lifecycle, and arithmetic rules.
- **Data Generator (`backend/app/generators/synthetic_data.py`):**
  - Deterministic generation initialized with seed `20261022`.
  - Batch persistence using `session.bulk_save_objects`.
