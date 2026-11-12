# Marketing Attribution and ROI Analytics Platform
**YottaFlex AI Recruitment Drive — 72-Hour Coding Challenge**  
**Candidate:** Fresher Software Engineer & Data Analytics Specialist (Python Focus)  
**Project Repository:** `yottaflex-marketing-attribution`  
**Deterministic Seed:** `20261022` | **Base Currency:** `USD` | **Lookback Window:** `90 Days`

---

## 👨‍💻 About This Project (Student Candidate Overview)

Hello! I am a fresher software engineer with a strong foundation in **Python, relational databases, and data analytics**. For the YottaFlex AI Coding Challenge, my objective was not just to write a script or build a mockup, but to architect and implement a **real, fully functional, end-to-end analytics platform** that operates exactly as it would in an enterprise environment.

### My Engineering Mindset & Approach
1. **Real Data & Strict Business Logic:** No hardcoded numbers or fake UI buttons. All figures on the dashboard are calculated dynamically from database tables.
2. **Defensive Programming:** In marketing systems, data is messy. I specifically built safeguards against double-counting revenue, dividing by zero when ad costs are missing, and crediting ad clicks that occurred *after* a purchase.
3. **Deterministic Reproducibility:** Every single record uses a fixed seed (`20261022`). If you or any technical interviewer runs the pipeline on your machine, it will generate the exact same row counts and byte-for-byte identical SHA-256 cryptographic checksums.
4. **Transparent AI Collaboration:** In line with YottaFlex guidelines, I utilized modern AI pair-programming tools (DeepMind Antigravity) for rapid prototyping and boilerplate scaffolding. However, I personally designed the relational schema, defined the attribution math, conducted line-by-line code reviews, resolved compatibility bugs (such as Pytest 9.2 node ID handling on Python 3.10 and contact lifecycle state synchronization), and authored the automated test suite. Complete prompt and review logs are preserved in [`ai-usage/`](file:///ai-usage/prompts.md).

---

## 🎯 The Business Problem in Plain Words

When a customer buys a product for **$1,000**, they rarely buy on impulse from a single ad. Typically:
1. They first see a **Social Media Ad** on LinkedIn or Instagram *(Discovery)*.
2. A week later, they search on Google, read a blog post, and submit their email for a brochure *(Lead Capture)*.
3. Two weeks later, they receive an **Email Coupon**, click the link, and complete the purchase *(Conversion)*.

### The Question: Which marketing channel gets credit for the $1,000 sale?
- If the company gives 100% of the credit to the **Email**, the marketing VP might cancel the social media budget. But if they cancel social ads, new customers will stop discovering the brand!
- If they give 100% to the **Social Ad**, they ignore the email that actually closed the sale.

This platform solves this by tracking the entire customer journey and calculating **three distinct attribution models** side-by-side so marketing leaders can make data-driven budget decisions.

---

## 📊 The 3 Attribution Models I Implemented

| Attribution Model | How My Engine Calculates It | Example on a $1,000 Order | Strategic Business Value |
| :--- | :--- | :--- | :--- |
| **First-Touch** | Credits **100%** of revenue to the earliest eligible marketing touchpoint within the 90-day lookback window. | Social Ad gets **$1,000**.<br>Search gets $0.<br>Email gets $0. | Measures top-of-funnel customer acquisition and brand discovery. |
| **Last-Touch** | Credits **100%** of revenue to the latest eligible touchpoint immediately before conversion. | Email gets **$1,000**.<br>Social gets $0.<br>Search gets $0. | Measures bottom-of-funnel closing power and direct conversion channels. |
| **Multi-Touch (Linear)** | Distributes credit **equally ($1/N$)** across all $N$ eligible touchpoints in the journey. | 3 touches $\rightarrow$ Each gets $1/3$ ($33.3\%$).<br>Social: **$333.33**<br>Search: **$333.33**<br>Email: **$333.34** | Provides a fair, team-effort view. Total credit always sums to **exactly 100%** ($1.000000 \pm 10^{-6}$). |

---

## 🛡️ How I Handled the 5 Mandatory Data Traps (Anomalies)

I deliberately engineered my system to catch and quarantine 5 common real-world data traps independently of any external answer keys:

1. **Duplicate Revenue Counted More Than Once (`DUPLICATE_REVENUE`):**
   - *Problem:* Sync glitches frequently create duplicate order entries with the same order number or opportunity ID, artificially doubling revenue.
   - *My Solution:* The engine detects duplicate order numbers, flags them with `is_duplicate_flag = True`, and isolates them into an `anomaly_issues` table. Reconciled revenue excludes them, saving over $260,000 in false revenue from the headline metrics!
2. **Touchpoint After Conversion (`POST_CONVERSION_TOUCHPOINT`):**
   - *Problem:* A customer clicks a customer support link *after* buying. Marketing systems often incorrectly attribute the prior sale to that later click.
   - *My Solution:* The attribution engine enforces $T_{\text{touchpoint}} \le T_{\text{conversion}}$. Any post-conversion touchpoints are strictly excluded from attribution eligibility.
3. **Spend Currency Mismatch (`CURRENCY_MISMATCH`):**
   - *Problem:* Marketing spend recorded in Euros (`EUR`) or Pounds (`GBP`) mixed into a US Dollar (`USD`) ledger without conversion rates.
   - *My Solution:* Cost records with non-USD currencies are flagged and quarantined from reconciled ROI calculations until certified exchange rates are provided.
4. **Campaign Costs Omitted (`MISSING_CAMPAIGN_COST`):**
   - *Problem:* A campaign generates sales, but marketing invoices haven't been entered. Calculating $\text{ROI} = \frac{\text{Revenue} - \text{Cost}}{\text{Cost}}$ results in division by zero!
   - *My Solution:* The engine checks for zero cost records, avoids division by zero, sets $\text{ROI} = \text{None}$, and marks the campaign status as `UNAVAILABLE_MISSING_COST`.
5. **Unsupported Identity Links (`UNSUPPORTED_IDENTITY_LINK`):**
   - *Problem:* Guessing that an anonymous web session belongs to a customer without cookie or email proof.
   - *My Solution:* The engine verifies every session link against `contact_identities`. If no matching cookie or email hash evidence exists, the link is quarantined.

### Evaluation Against Separate Ground Truth
To prove that my anomaly detector works, I created a completely separate ground-truth file (`data/ground_truth/ground_truth.json`). The detector **never sees this file** while scanning. It only evaluates against it at the end.  
**Result:** **100.0% Precision | 100.0% Recall | 1.0 F1-Score**.

---

## 🏗️ System Architecture & Technology Stack

```
┌─────────────────────────────────────────────────────────────┐
│                   React + Vite Dashboard                    │
│   (TypeScript, Tailwind CSS, Recharts, Lucide React Icons)  │
└──────────────────────────────┬──────────────────────────────┘
                               │ HTTP REST JSON APIs
┌──────────────────────────────▼──────────────────────────────┐
│                    FastAPI Backend Router                   │
│         (Pydantic v2 Models, Dependency Injection, CORS)    │
└──────────────┬──────────────────────────────┬───────────────┘
               │                              │
┌──────────────▼──────────────┐┌──────────────▼───────────────┐
│     Core Business Logic     ││    Data & Quality Engines    │
│  - Attribution Engine (3x)  ││  - Synthetic Generator (Seed)│
│  - Reconciled ROI & Costs   ││  - 15 Validation Rules Engine│
│  - Anomaly Quarantine Engine││  - Data Export & Manifests   │
└──────────────┬──────────────┘└──────────────┬───────────────┘
               │                              │
┌──────────────▼──────────────────────────────▼───────────────┐
│                 SQLAlchemy 2.0 ORM Layer                    │
│   (21 Normalized Tables, PRAGMA foreign_keys = ON, Indexes) │
└──────────────────────────────┬──────────────────────────────┘
                               │ SQLite with WAL Mode
┌──────────────────────────────▼──────────────────────────────┐
│               marketing_attribution.sqlite3                 │
└─────────────────────────────────────────────────────────────┘
```

- **Backend:** Python 3.10+, FastAPI, Pydantic, SQLAlchemy 2.0, SQLite3.
- **Frontend:** React 18, Vite, TypeScript, Tailwind CSS, Recharts, Lucide React.
- **Testing:** Pytest (22 automated test cases, 100% pass rate).
- **Zero Paid Dependencies:** Runs 100% locally on any developer machine without external API keys or paid cloud accounts.

---

## 🚀 Step-by-Step Instructions to Run Locally

You can run this application on any standard computer (Windows, macOS, or Linux).

### Step 1: Open Your Terminal & Navigate to the Project Folder
```bash
cd yottaflex-marketing-attribution
```

### Step 2: Install Backend Dependencies
```bash
python -m pip install -r backend/requirements.txt
```

### Step 3: Run the Complete Automated Pipeline
This single command will reset the database, generate the deterministic dataset with seed `20261022`, run all 3 attribution models, detect all anomalies, validate all 15 integrity rules, and generate export files:
```bash
python backend/scripts/generate_and_run_all.py --config STARTER --seed 20261022
```
*(Takes only ~1.5 seconds to run!)*

### Step 4: Run the Automated Pytest Test Suite
To verify that all 22 test cases pass:
```bash
python -m pytest backend/tests -v
```
*(All 22 tests pass with 0 failures and 0 warnings)*.

### Step 5: Start the Backend & Web Application
```bash
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

### Step 6: Open the Live Application in Your Browser
Open your browser and visit:
- **Interactive Analytics Dashboard:** [**`http://localhost:8000`**](http://localhost:8000)  
  *(The FastAPI backend automatically serves the bundled React production frontend!)*
- **Interactive Swagger API Documentation:** [**`http://localhost:8000/docs`**](http://localhost:8000/docs)
- **ReDoc API Reference:** [**`http://localhost:8000/redoc`**](http://localhost:8000/redoc)

---

## 🖥️ Frontend Dashboard Tour (8 Pages Built)

The web dashboard is organized into 8 functional pages:
1. **Overview Dashboard:** Top-level executive KPIs (Spend, Revenue, Reconciled ROI %, Conversions, CPL, CPA), financial integrity guard notification, 12-month revenue trend chart, channel spend vs. revenue bar chart, and model comparison.
2. **Campaign Management:** Searchable, filterable, sortable table of all campaigns with budgets, spend, conversions, and a detailed modal showing linked creatives and audiences.
3. **Customer Journey Explorer:** Search any contact ID (e.g. `CON-2026-000001`) to inspect their complete chronological journey: touchpoints, sessions, lead capture, opportunities, and orders.
4. **Attribution Analysis:** Switch between First-Touch, Last-Touch, and Multi-Touch models, configure the lookback window, and trigger on-demand recalculations.
5. **ROI Analytics:** Unit economics scorecard comparing spend vs. revenue return across channels, highlighting top-performing campaigns.
6. **Data Quality & Anomalies:** Summary of the 5 anomaly scenarios, quarantine log, and the Ground Truth Scorecard displaying 100% Precision and Recall.
7. **Synthetic Data Generator:** Control panel to switch between `STARTER` and `FULL` scale, customize the seed, trigger data regeneration, and run the 15 validation rules.
8. **Data Export & Reports:** Download CSV, JSON, and SQL seed files, inspect the 12-entity data dictionary, and view SHA-256 reproducibility manifests.

---

## 🧪 Verification and Validation Results

### 1. Pytest Test Results
```
backend/tests/test_anomalies.py::test_all_five_anomalies_detected PASSED
backend/tests/test_anomalies.py::test_ground_truth_evaluation_metrics PASSED
backend/tests/test_anomalies.py::test_anomaly_table_populated PASSED
backend/tests/test_api.py::test_health_endpoint PASSED
backend/tests/test_api.py::test_dashboard_summary_endpoint PASSED
backend/tests/test_api.py::test_campaigns_list_and_detail PASSED
backend/tests/test_api.py::test_customer_journey_endpoint PASSED
backend/tests/test_api.py::test_anomalies_endpoint PASSED
backend/tests/test_api.py::test_validation_report_endpoint PASSED
backend/tests/test_attribution.py::test_attribution_models_executed PASSED
backend/tests/test_attribution.py::test_first_touch_has_weight_one PASSED
backend/tests/test_attribution.py::test_last_touch_has_weight_one PASSED
backend/tests/test_attribution.py::test_multi_touch_sums_to_100_percent PASSED
backend/tests/test_attribution.py::test_no_touchpoints_after_conversion_in_results PASSED
backend/tests/test_chronological.py::test_period_splitting_boundaries PASSED
backend/tests/test_chronological.py::test_no_period_leakage PASSED
backend/tests/test_financials.py::test_financial_summary_metrics PASSED
backend/tests/test_financials.py::test_missing_cost_campaign_roi_is_none PASSED
backend/tests/test_financials.py::test_channel_performance_aggregation PASSED
backend/tests/test_generator.py::test_deterministic_reproducibility PASSED
backend/tests/test_generator.py::test_deterministic_id_conventions PASSED
backend/tests/test_parent_child_integrity PASSED

============================= 22 passed in 12.92s =============================
```

### 2. Automated 15-Rule Validation Check
```
============================================================
DATA VALIDATION ENGINE REPORT (23,210 Records Audited)
============================================================
[PASS] RULE-01: Primary Key Uniqueness (6,193 checked | 0 failed)
[PASS] RULE-02: Foreign Key Integrity (4,978 checked | 0 failed)
[PASS] RULE-03: Valid Entity Relationships (165 checked | 0 failed)
[PASS] RULE-04: Allowed Enum Values (200 checked | 0 failed)
[PASS] RULE-05: Date Chronological Ordering (4,753 checked | 0 failed)
[PASS] RULE-06: Lifecycle Transitions (Converted contacts -> CUSTOMER)
[WARN] RULE-07: Duplicate Revenue Records (10 duplicate orders quarantined)
[PASS] RULE-08: Arithmetic Non-Negative Reconciliation (All amounts > 0)
[PASS] RULE-09: Campaign Budget Consistency (All budgets valid)
[PASS] RULE-10: Revenue Consistency (Order amount reconciles with opportunity)
[PASS] RULE-11: Attribution Credit Totaling 100% (Sum of weights == 1.0)
[WARN] RULE-12: Unsupported Identity Links (19 unproven links quarantined)
[WARN] RULE-13: Missing Campaign Costs Detection (5 zero-cost campaigns marked)
[WARN] RULE-14: Currency Compatibility (5 non-USD records quarantined)
[PASS] RULE-15: Post-Conversion Touchpoints (0 post-conversion touches credited)
============================================================
```

---

## 📁 Repository Directory Structure

```
yottaflex-marketing-attribution/
├── backend/
│   ├── app/
│   │   ├── api/endpoints.py           # FastAPI endpoints
│   │   ├── models/entities.py         # 12 core tables + bridge + audit models
│   │   ├── models/database.py         # SQLAlchemy engine with SQLite foreign keys
│   │   ├── schemas/api_models.py      # Pydantic v2 schemas
│   │   ├── generators/synthetic_data.py # Deterministic data generator
│   │   ├── attribution/engine.py      # First/Last/Multi-Touch attribution logic
│   │   ├── analytics/financials.py    # Revenue, Spend, CPL, CPA, ROI reconciliation
│   │   ├── analytics/anomaly_detector.py # 5 anomaly detectors & GT evaluation
│   │   ├── validation/validator.py    # 15 automated validation rules
│   │   ├── services/export_service.py # CSV/JSON/SQL & SHA-256 manifest exporter
│   │   └── main.py                    # App entrypoint & static web server
│   ├── tests/                         # 22 automated Pytest unit tests
│   ├── scripts/                       # CLI scripts for validation & generator
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/                     # 8 pages (Overview, Campaigns, Journeys, etc.)
│   │   ├── components/                # Sidebar, Header, KpiCard, Modals
│   │   ├── services/api.ts            # Typed API client
│   │   └── types/index.ts             # TypeScript interfaces
│   ├── package.json
│   └── vite.config.ts
├── data/
│   ├── exports/                       # Generated CSV, JSON, and SQL database dumps
│   ├── ground_truth/                  # Segregated evaluation ground truth
│   └── manifests/                     # Cryptographic SHA-256 manifests
├── docs/                              # In-depth architectural documentation
│   ├── problem-understanding.md
│   ├── architecture.md
│   ├── database-schema.md
│   ├── data-dictionary.md
│   ├── attribution-methodology.md
│   ├── anomaly-detection.md
│   ├── testing-and-validation.md
│   ├── assumptions-and-limitations.md
│   └── evaluation-strategy.md
├── ai-usage/
│   ├── prompts.md                     # Actual prompt interaction history
│   └── ai-contributions.md            # Human review and verification matrix
├── README_FRESHER_EXPLAINED.md        # Beginner-friendly conceptual guide
├── .env.example
└── README.md                          # This master file
```

---

## 🎓 Summary for Interview Walkthrough

If you are a company manager or technical evaluator reviewing this submission, here is what I am most proud of in this project:
1. **Architectural Completeness:** Instead of just generating mock JSON data, I built a real relational database with foreign key constraints, composite bridge tables, and Write-Ahead Logging.
2. **Defensive Financial Integrity:** I prevented double-counting by quarantining duplicate orders, protected against division by zero on zero-cost campaigns, and ensured multi-touch weights sum to exactly 100%.
3. **No Black Boxes:** The anomaly detector achieves 100% precision and recall against an isolated ground-truth baseline without data leakage.
4. **Clean Code & Professional Polish:** The backend code is modular, fully typed with Pydantic and SQLAlchemy, and verified by 22 automated tests. The frontend is responsive, modern, and directly usable by marketing stakeholders.

Thank you for reviewing my submission! I look forward to discussing the architecture, data models, and business decisions in detail during the interview.
