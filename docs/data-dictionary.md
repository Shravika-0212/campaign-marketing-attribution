# Relational Data Dictionary
**Platform:** Marketing Attribution and ROI Analytics Platform  
**Standard Nomenclature:** Immutable Zero-Padded Prefixed Keys (e.g., `CMP-2026-000001`)

---

## 1. Primary Entity Field Specifications

| Entity | Field Name | Data Type | Nullable | Primary / Foreign Key | Allowed Values / Formats | Validation Rule |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Channel** | `channel_id` | VARCHAR(50) | NO | Primary Key | `CHN-[A-Z0-9-]+` | Unique channel identifier |
| | `name` | VARCHAR(100) | NO | None | String | Must be unique |
| | `channel_type` | VARCHAR(20) | NO | None | `ONLINE`, `OFFLINE` | Enum validation |
| | `cost_structure` | VARCHAR(20) | NO | None | `CPC`, `CPM`, `FLAT`, `COMMISSION` | Enum validation |
| | `is_active` | BOOLEAN | NO | None | `TRUE`, `FALSE` | Channel status |
| **Campaign** | `campaign_id` | VARCHAR(50) | NO | Primary Key | `CMP-2026-[0-9]{6}` | Immutable unique PK |
| | `name` | VARCHAR(150) | NO | None | String | Campaign title |
| | `channel_id` | VARCHAR(50) | NO | FK &rarr; `channels` | Existing `channel_id` | Referential integrity |
| | `budget` | FLOAT | NO | None | $\ge 0.0$ | Positive budget |
| | `currency` | VARCHAR(10) | NO | None | `USD` | Base currency |
| | `status` | VARCHAR(20) | NO | None | `ACTIVE`, `COMPLETED` | Lifecycle status |
| | `start_date` | DATETIME | NO | None | ISO 8601 | Temporal boundary |
| | `end_date` | DATETIME | YES | None | ISO 8601 | $\ge$ `start_date` |
| **Contact** | `contact_id` | VARCHAR(50) | NO | Primary Key | `CON-2026-[0-9]{6}` | Immutable unique PK |
| | `first_name` | VARCHAR(100) | NO | None | String | Non-empty |
| | `last_name` | VARCHAR(100) | NO | None | String | Non-empty |
| | `email` | VARCHAR(150) | NO | None | Email format | Strictly unique |
| | `lifecycle_stage` | VARCHAR(30) | NO | None | `SUBSCRIBER`, `LEAD`, `CUSTOMER` | Monotonic progression |
| | `first_seen_at` | DATETIME | NO | None | ISO 8601 | Journey origin |
| **Touchpoint**| `touchpoint_id` | VARCHAR(100)| NO | Primary Key | `TOUCH-{contact-id}-[0-9]{6}` | Immutable unique PK |
| | `contact_id` | VARCHAR(50) | YES | FK &rarr; `contacts` | Existing `contact_id` | Nullable for anon sessions |
| | `campaign_id` | VARCHAR(50) | NO | FK &rarr; `campaigns` | Existing `campaign_id` | Valid marketing origin |
| | `channel_id` | VARCHAR(50) | NO | FK &rarr; `channels` | Existing `channel_id` | Channel mapping |
| | `touch_type` | VARCHAR(30) | NO | None | `CLICK`, `IMPRESSION`, `EMAIL_OPEN`, `WEBINAR`, `IN_PERSON`, `CALL` | Interaction type |
| | `channel_medium`| VARCHAR(20) | NO | None | `ONLINE`, `OFFLINE` | Medium classification |
| | `occurred_at` | DATETIME | NO | None | ISO 8601 | Must precede conversion for credit |
| | `interaction_cost`| FLOAT | NO | None | $\ge 0.0$ | Non-negative cost |
| **Opportunity**| `opportunity_id`| VARCHAR(50)| NO | Primary Key | `OPP-2026-[0-9]{6}` | Immutable unique PK |
| | `contact_id` | VARCHAR(50) | NO | FK &rarr; `contacts` | Existing `contact_id` | Linked prospect |
| | `lead_id` | VARCHAR(50) | YES | FK &rarr; `leads` | Existing `lead_id` | Form origin link |
| | `campaign_id` | VARCHAR(50) | NO | FK &rarr; `campaigns` | Existing `campaign_id` | Primary driving campaign |
| | `stage` | VARCHAR(30) | NO | None | `PROSPECTING`, `QUALIFICATION`, `PROPOSAL`, `NEGOTIATION`, `CLOSED_WON`, `CLOSED_LOST` | Pipeline state |
| | `expected_revenue`| FLOAT | NO | None | $\ge 0.0$ | Projected revenue |
| **Order** | `order_id` | VARCHAR(50) | NO | Primary Key | `ORD-2026-[0-9]{6}` | Immutable unique PK |
| | `opportunity_id`| VARCHAR(50)| NO | FK &rarr; `opportunities`| Existing `opportunity_id`| Must be `CLOSED_WON` |
| | `contact_id` | VARCHAR(50) | NO | FK &rarr; `contacts` | Existing `contact_id` | Converted customer |
| | `order_number` | VARCHAR(50) | NO | None | Unique order string | Deduplication check |
| | `order_date` | DATETIME | NO | None | ISO 8601 | Conversion timestamp |
| | `amount` | FLOAT | NO | None | $> 0.0$ | Recognized closed revenue |
| | `currency` | VARCHAR(10) | NO | None | `USD` | Standard currency |
| | `status` | VARCHAR(30) | NO | None | `COMPLETED` | Valid transaction |
| | `is_duplicate_flag`| BOOLEAN | NO | None | `TRUE`, `FALSE` | Anomaly quarantine flag |
| **Attribution**| `result_id` | VARCHAR(50) | NO | Primary Key | `ATT-[FT/LT/MT]-[0-9]+` | Unique result ID |
| | `model_id` | VARCHAR(50) | NO | FK &rarr; `attribution_models`| `MDL-[A-Z-]+` | Model configuration |
| | `order_id` | VARCHAR(50) | NO | FK &rarr; `orders` | Valid non-duplicate order | Revenue source |
| | `campaign_id` | VARCHAR(50) | NO | FK &rarr; `campaigns` | Valid campaign | Credited initiative |
| | `attribution_weight`| FLOAT | NO | None | $0.0 \le w \le 1.0$ | Credit fraction |
| | `attributed_revenue`| FLOAT | NO | None | $w \times \text{amount}$ | Fractional revenue |
| | `evaluation_period`| VARCHAR(20)| NO | None | `TRAIN`, `VALIDATION`, `TEST` | Chronological slice |
