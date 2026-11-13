# Prompts Log: How I Built This Project with AI Assistance

**Project:** Marketing Attribution and ROI Analytics Platform  
.

---

## Introduction

To complete this marketing attribution platform, I used AI as an interactive pair-programming tool. Below is the chronological log of the prompts I provided at each stage of development, explaining what I asked, why I asked it, and how I reviewed and verified the code.

---

### Phase 1: Database Architecture & Tables Setup

#### My Prompt:
> *"I need to build a marketing attribution and ROI analytics project using Python, SQL, and FastAPI. In this project, a company spends money on marketing campaigns across different channels like Google Search, Social Media, Email, and in-person events. Customers see ads, visit the website, become leads, create sales opportunities, and finally place orders.*  
>  
> *Can you help me design a clean relational database schema in SQLite using SQLAlchemy ORM? It should have 12 normalized entities: Campaign, Channel, Creative, Audience, Contact, Touchpoint, WebSession, Lead, Opportunity, Order, CostRecord, and AttributionResult. Please make sure foreign keys and primary keys are properly defined, and include bridge tables for many-to-many relationships."*

#### Why I asked this:
I wanted to start with a solid relational data foundation. In marketing analytics, tracking a customer's journey requires linking several entities together—from the first ad impression all the way to finalized order revenue.

#### What the AI provided:
- SQLAlchemy ORM models in `backend/app/models/entities.py` for all 12 core tables.
- 4 bridge and audit tables: `campaign_channels`, `campaign_audiences`, `campaign_creatives`, and `contact_identities`.
- SQLite foreign key configuration and indexes on high-traffic join columns.

#### How I verified it:
I checked `entities.py`, verified all primary and foreign key relationships, initialized the SQLite database file (`marketing_attribution.sqlite3`), and verified that all tables were created properly without errors.

---

### Phase 2: Generating Synthetic Data with Indian Customer Names

#### My Prompt:
> *"Now I need to write a synthetic data generator in Python using Pandas and NumPy. It should create realistic marketing data. It needs to support two sizes: STARTER (50 campaigns, 1,000 contacts, 4,000 touchpoints, 200 opportunities) and FULL BASELINE (500 campaigns, 50,000 contacts, 200,000 touchpoints, 10,000 opportunities).*  
>  
> *Requirements:*  
> *1. Use a fixed random seed `20261022` so the data is 100% reproducible every time.*  
> *2. Use Indian names for the contacts (like Shravika, Sharanya, Srinivas, Shailaja, Krish, Aarav, etc.).*  
> *3. Use clean deterministic ID formats like `CMP-2026-000001`, `CON-2026-000001`, and `ORD-2026-000001`.*  
> *4. Make sure parent records (campaigns, contacts) are generated before dependent records (touchpoints, orders).*  
> *5. Feature Shravika Kavati as contact #1 with a full multi-touch customer journey."*

#### Why I asked this:
Real-world marketing datasets are confidential, so generating realistic, deterministic synthetic data allows me to simulate realistic multi-channel journeys and long conversion windows while maintaining reproducible results.

#### What the AI provided:
- `backend/app/generators/synthetic_data.py` with deterministic logic.
- `backend/app/generators/config.py` defining both `STARTER` and `FULL_BASELINE` parameters.
- Shravika Kavati configured as the lead featured customer (`CON-2026-000001`).

#### How I verified it:
I ran the generator with seed `20261022` twice and checked the SHA-256 checksums to confirm that both runs produced identical row counts and checksum hashes.

---

### Phase 3: Attribution Models & Financial ROI Calculation

#### My Prompt:
> *"Now let's write the attribution engine in Python. For every closed order, we need to compare three attribution models:*  
> *1. First-Touch Attribution: Gives 100% of order revenue to the earliest eligible touchpoint.*  
> *2. Last-Touch Attribution: Gives 100% to the latest touchpoint before the conversion date.*  
> *3. Multi-Touch Linear: Divides the order revenue equally across all touchpoints.*  
>  
> *Important business rules:*  
> *- Never attribute touchpoints that happened AFTER the conversion date.*  
> *- Respect a 90-day lookback window.*  
> *- The sum of attributed revenue across touchpoints must equal the exact order amount.*  
> *- Calculate ROI in Indian Rupees (₹ INR) using the formula: `(Attributed Revenue - Campaign Cost) / Campaign Cost * 100`.*  
> *- If a campaign has missing costs, do not divide by zero; mark it as INCOMPLETE."*

#### Why I asked this:
This is the core business logic of the problem statement. In digital marketing, different teams look at different models—top-of-funnel teams prefer First-Touch, while conversion teams prefer Last-Touch. I needed all three models calculated accurately in Indian Rupees without mathematical drift.

#### What the AI provided:
- `backend/app/attribution/engine.py` implementing the three models.
- `backend/app/analytics/financials.py` calculating spend, revenue, CPA, CPL, and ROI.
- Protection against divide-by-zero for missing cost campaigns.

#### How I verified it:
I checked the math using Pandas: $\sum \text{Attributed Revenue} = \text{Total Closed Revenue}$ for each model. All three models matched the exact non-duplicate closed revenue of ₹40,54,123.71.

---

### Phase 4: Anomaly Injection & Quality Assurance Engine

#### My Prompt:
> *"In real business data, things get messy. I want to deliberately inject 5 realistic data traps into the dataset, and build an anomaly detection engine to catch them:*  
> *1. Duplicate revenue (same order counted more than once).*  
> *2. Touchpoints occurring after conversion being attributed.*  
> *3. Currency mismatch (spending in USD or EUR while our system runs on INR).*  
> *4. Omitted campaign costs (campaigns with zero cost records).*  
> *5. Anonymous web sessions linked to contacts without cookie evidence.*  
>  
> *Please keep the ground-truth answers in separate files (`ground_truth.json` and `ground_truth.csv`) so we don't cheat or leak data into detection. Calculate True Positives, False Positives, False Negatives, Precision, Recall, and F1 Score."*

#### Why I asked this:
To prove data quality and machine learning evaluation concepts, the system must detect intentional anomalies and measure performance with industry-standard classification metrics (Precision, Recall, F1).

#### What the AI provided:
- Anomaly injection logic in `synthetic_data.py`.
- `backend/app/analytics/anomaly_detector.py` to identify issues independently.
- Ground truth evaluation scorecard outputting confusion matrix metrics.

#### How I verified it:
I verified that all 63 injected anomalies were correctly identified:
- True Positives: 63, False Positives: 0, False Negatives: 0
- Precision: 100.0%, Recall: 100.0%, F1-Score: 1.0.

---

### Phase 5: FastAPI REST Endpoints & Swagger Documentation

#### My Prompt:
> *"Let's build a REST API in FastAPI to expose all this data. I need endpoints for:*  
> *- Dashboard overview summary and 12-month trends.*  
> *- Campaign lists with spend, revenue, and ROI.*  
> *- Customer journey timeline lookup for any contact ID.*  
> *- Anomaly scorecard and validation reports.*  
> *- File export downloads (CSV, JSON, SQL seed).*  
> *- Automatic interactive documentation using Swagger UI at `/docs`."*

#### Why I asked this:
FastAPI allows me to structure clean, strongly-typed asynchronous backend services that can be consumed by any frontend or external client.

#### What the AI provided:
- `backend/app/api/endpoints.py` containing all route handlers.
- `backend/app/schemas/api_models.py` with Pydantic request and response schemas.
- Interactive Swagger documentation enabled at `http://localhost:8000/docs`.

#### How I verified it:
I started the Uvicorn server, opened `http://localhost:8000/docs`, and tested calling `/api/summary`, `/api/campaigns`, and `/api/contacts/CON-2026-000001/journey`. All endpoints returned valid JSON data.

---

### Phase 6: Role-Based Access Control (RBAC) with Indian Personas

#### My Prompt:
> *"I need to implement role-based access for 5 primary business actors:*  
> *1. Customer / Prospect (Shravika Kavati): Only sees her own interaction timeline.*  
> *2. Marketing & Sales Operations (Sharanya Kavati): Manages campaigns, budgets, channels, and leads.*  
> *3. Support Agent (Srinivas Kavati): Read-only lookup of customer journeys and profiles.*  
> *4. Attribution & Financial Analyst (Shailaja Kavati): Accesses attribution models, ROI analytics, and anomaly evaluations.*  
> *5. System Administrator (Krish Kavati): Full admin access to generate datasets, run validation rules, and export data.*  
>  
> *Please ensure Western/American names are replaced with these Indian names across the personas and contact lists."*

#### Why I asked this:
Enterprise applications require data security and privacy. A support agent should not be modifying ad budgets, and customers must not see internal marketing financial ROI.

#### What the AI provided:
- `backend/app/security/rbac.py` defining role hierarchies, permissions, and actor personas.
- FastAPI dependency `require_roles(...)` enforcing route protection.
- Top-right role switcher in the frontend header.

#### How I verified it:
I tested switching roles in the UI. When logged in as Support Agent, edit controls are disabled. When logged in as Customer, only Shravika's journey is accessible.

---

### Phase 7: Matplotlib Charts & Interactive Frontend

#### My Prompt:
> *"I have Python data science skills with Pandas, NumPy, and Matplotlib. Can we write a script using Matplotlib to generate high-resolution PNG charts on the server?*  
> *- Attribution model comparison bar chart.*  
> *- 12-month revenue vs. marketing spend area chart.*  
> *- Channel acquisition efficiency (spend vs. revenue) horizontal bar chart.*  
> *- Customer journey timeline for Shravika Kavati.*  
>  
> *Save them into `data/exports/charts/` and add a 'Python Matplotlib Charts' tab in the Reports page of the React frontend so users can view and download them."*

#### Why I asked this:
I wanted to directly showcase my Python Matplotlib and Pandas plotting skills within the platform, complementing the live React/Recharts frontend.

#### What the AI provided:
- `backend/app/analytics/visualizations.py` using Matplotlib in headless mode (`Agg`).
- API routes `/api/analytics/charts/generate` and `/api/analytics/charts/view/{chart_name}`.
- Added a dedicated tab in `frontend/src/pages/ReportsPage.tsx` with high-resolution image cards and download links.

#### How I verified it:
I ran the generation pipeline, checked that all 4 `.png` files were created in `data/exports/charts/`, rebuilt the frontend with `npm run build`, and viewed the plots live in the browser.

---

### Phase 8: Debugging & Command Prompt Pipeline Execution

#### My Prompt:
> *"When I ran `python -m pytest backend/tests -v` in my Windows virtual environment, I got this error:*  
> `AttributeError: 'NodeId' object has no attribute '_str_cache'`  
> *Can you help me fix this error and make sure all 40 tests pass?"*

#### Why I asked this:
During development, a newly released version of pytest (`9.2.0`) had an incompatibility with Python 3.10 dataclass slots on Windows, preventing tests from completing.

#### What the AI helped diagnose:
- Identified that `pytest 9.2.0` introduced an uninitialized slot descriptor bug in Python 3.10.
- Pinned `pytest>=8.0.0,<9.0.0` in `backend/requirements.txt` and installed stable `pytest 8.4.2`.

#### How I verified it:
I ran `python -m pytest backend/tests -v` in Windows Command Prompt:
```text
======================= 40 passed in 23.15s ========================
```
All 40 automated tests passed cleanly.

---

## Conclusion

By asking specific, step-by-step architectural questions, reviewing each module, debugging real environment issues, and testing every component locally in Windows Command Prompt and the browser, I developed a complete, reproducible, and verifiable full-stack marketing attribution platform.
