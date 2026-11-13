# Granular Relational Data Dictionary (12 Core Entities)
**Platform:** Marketing Attribution and ROI Analytics Platform  
**Standard Nomenclature:** Immutable Zero-Padded Prefixed Keys (e.g., `CMP-2026-000001`)  
**Base Currency:** Indian Rupees (`INR` / `₹`) | **Lookback Window:** 90 Days  

---

## Field-Level Specifications for All 12 Entities

### 1. `Campaign` (Master Marketing Initiatives)
Represents marketing campaigns deployed across acquisition channels with allocated budgets and execution dates.

| Field Name | Data Type | Req / Opt | Allowed Values | Units | Uniqueness | Validation Rule |
| :--- | :--- | :---: | :--- | :---: | :---: | :--- |
| `campaign_id` | `VARCHAR(50)` | Required | Format: `CMP-2026-[0-9]{6}` | Identifier | **Unique (PK)** | Immutable, 15-char string matching regex `^CMP-2026-\d{6}$`. |
| `name` | `VARCHAR(150)` | Required | Descriptive string | Text | Non-unique | Non-empty string; includes primary channel descriptor. |
| `channel_id` | `VARCHAR(50)` | Required | Must exist in `channels.channel_id` | Foreign Key | Non-unique | Referential integrity to valid parent channel record. |
| `budget` | `FLOAT` | Required | Positive float: `5000.0` to `150000.0` | INR (`₹`) | Non-unique | Must be non-negative: `budget >= 0.0`. |
| `currency` | `VARCHAR(10)` | Required | `INR` | ISO Currency | Non-unique | Must equal platform base currency `INR`. |
| `status` | `VARCHAR(20)` | Required | `ACTIVE`, `COMPLETED`, `PAUSED` | Status Enum | Non-unique | Must belong to allowed status domain enum. |
| `start_date` | `DATETIME` | Required | ISO 8601 Timestamp | UTC Date | Non-unique | Valid timestamp within period boundary `2026-01-01` to `2026-12-31`. |
| `end_date` | `DATETIME` | Optional | ISO 8601 Timestamp | UTC Date | Non-unique | When present, must satisfy `end_date >= start_date`. |
| `created_at` | `DATETIME` | Required | ISO 8601 Timestamp | UTC Date | Non-unique | Must be before or equal to `start_date`. |
| `updated_at` | `DATETIME` | Required | ISO 8601 Timestamp | UTC Date | Non-unique | Must be `>= created_at`. |

---

### 2. `Channel` (Acquisition Channels)
Represents discrete marketing communication channels across online and offline mediums.

| Field Name | Data Type | Req / Opt | Allowed Values | Units | Uniqueness | Validation Rule |
| :--- | :--- | :---: | :--- | :---: | :---: | :--- |
| `channel_id` | `VARCHAR(50)` | Required | Format: `CHN-[A-Z-]+` | Identifier | **Unique (PK)** | Root master identifier (e.g. `CHN-PAID-SEARCH`, `CHN-EVENT`). |
| `name` | `VARCHAR(100)` | Required | String title | Text | **Unique** | Descriptive name of the channel. |
| `channel_type` | `VARCHAR(20)` | Required | `ONLINE`, `OFFLINE` | Medium Enum | Non-unique | Enum check constraint. `OFFLINE` channels have `session_id=None`. |
| `cost_structure`| `VARCHAR(20)` | Required | `CPC`, `CPM`, `FLAT`, `COMMISSION`| Pricing Enum | Non-unique | Valid channel cost pricing structure enum. |
| `is_active` | `BOOLEAN` | Required | `TRUE`, `FALSE` | Boolean Flag | Non-unique | Channel routing availability flag. |
| `created_at` | `DATETIME` | Required | ISO 8601 Timestamp | UTC Date | Non-unique | Master creation timestamp. |

---

### 3. `Creative` (Ad Assets & Content Collateral)
Represents marketing creative assets, ad copy, message themes, and banner formats.

| Field Name | Data Type | Req / Opt | Allowed Values | Units | Uniqueness | Validation Rule |
| :--- | :--- | :---: | :--- | :---: | :---: | :--- |
| `creative_id` | `VARCHAR(50)` | Required | Format: `CRT-2026-[0-9]{6}` | Identifier | **Unique (PK)** | Immutable, zero-padded identifier. |
| `name` | `VARCHAR(150)` | Required | String title | Text | Non-unique | Creative display title including format and theme. |
| `creative_format`| `VARCHAR(30)` | Required | `BANNER`, `VIDEO`, `TEXT_AD`, `EMAIL_TEMPLATE`, `WEBINAR_DECK`, `PRODUCT_ONE_PAGER` | Format Enum | Non-unique | Must match allowed creative format domain. |
| `asset_url` | `VARCHAR(255)` | Required | Valid URL format: `https://...` | URI String | Non-unique | Valid HTTPS CDN asset reference. |
| `message_theme` | `VARCHAR(100)` | Required | String theme label | Text | Non-unique | Strategic theme (e.g. ROI Optimization, Scale Fast). |
| `created_at` | `DATETIME` | Required | ISO 8601 Timestamp | UTC Date | Non-unique | Creation date prior to campaign launch. |

---

### 4. `Audience` (Target Audience Segments)
Represents audience segments, firmographics, and targeting criteria.

| Field Name | Data Type | Req / Opt | Allowed Values | Units | Uniqueness | Validation Rule |
| :--- | :--- | :---: | :--- | :---: | :---: | :--- |
| `audience_id` | `VARCHAR(50)` | Required | Format: `AUD-2026-[0-9]{6}` | Identifier | **Unique (PK)** | Immutable, zero-padded identifier. |
| `name` | `VARCHAR(150)` | Required | Descriptive name | Text | Non-unique | Segment title. |
| `segment_type` | `VARCHAR(50)` | Required | `B2B_ENTERPRISE`, `SMB_GROWTH`, `FINTECH`, `HEALTHCARE`, `RETAIL_ECOMMERCE`, `DEVELOPER_TECH` | Segment Enum | Non-unique | Must match allowed firmographic classification enum. |
| `target_criteria`| `VARCHAR(255)`| Required | Textual specification | Text | Non-unique | Company size, vertical, and intent threshold criteria. |
| `created_at` | `DATETIME` | Required | ISO 8601 Timestamp | UTC Date | Non-unique | Creation date. |

---

### 5. `Contact` (Customer & Prospect Identities)
Represents prospect and customer profiles. Contact #1 `CON-2026-000001` is featured customer Shravika Kavati.

| Field Name | Data Type | Req / Opt | Allowed Values | Units | Uniqueness | Validation Rule |
| :--- | :--- | :---: | :--- | :---: | :---: | :--- |
| `contact_id` | `VARCHAR(50)` | Required | Format: `CON-2026-[0-9]{6}` | Identifier | **Unique (PK)** | Immutable, zero-padded identifier. |
| `first_name` | `VARCHAR(100)` | Required | String | Text | Non-unique | Non-empty string. |
| `last_name` | `VARCHAR(100)` | Required | String | Text | Non-unique | Non-empty string. |
| `email` | `VARCHAR(150)` | Required | Valid RFC 5322 Email Format | Email Address| **Unique** | Unique corporate/personal email address. |
| `phone` | `VARCHAR(50)` | Optional | Valid E.164 Phone Format | Phone String | Non-unique | Nullable or valid mobile format. |
| `lifecycle_stage`| `VARCHAR(30)` | Required | `SUBSCRIBER`, `LEAD`, `OPPORTUNITY`, `CUSTOMER` | Stage Enum | Non-unique | Monotonic lifecycle progression; derived from conversions. |
| `first_seen_at` | `DATETIME` | Required | ISO 8601 Timestamp | UTC Date | Non-unique | Origin timestamp; all touches must occur `>= first_seen_at`. |
| `created_at` | `DATETIME` | Required | ISO 8601 Timestamp | UTC Date | Non-unique | Equivalent to `first_seen_at`. |

---

### 6. `WebSession` (Digital Browsing Sessions)
Represents digital browsing visits capturing cookies, device types, and referrers.

| Field Name | Data Type | Req / Opt | Allowed Values | Units | Uniqueness | Validation Rule |
| :--- | :--- | :---: | :--- | :---: | :---: | :--- |
| `session_id` | `VARCHAR(50)` | Required | Format: `SES-2026-[0-9]{6}` | Identifier | **Unique (PK)** | Immutable, zero-padded identifier. |
| `contact_id` | `VARCHAR(50)` | Optional | FK &rarr; `contacts.contact_id` | Foreign Key | Non-unique | Nullable for anonymous sessions; validated via identity links. |
| `anonymous_cookie_id`| `VARCHAR(100)`| Required| Format: `CK-[0-9]+` | Cookie Token | Non-unique | Stored in `contact_identities` unless injecting Anomaly 5. |
| `started_at` | `DATETIME` | Required | ISO 8601 Timestamp | UTC Date | Non-unique | Session start timestamp. |
| `ended_at` | `DATETIME` | Required | ISO 8601 Timestamp | UTC Date | Non-unique | Must strictly satisfy `ended_at >= started_at`. |
| `device_type` | `VARCHAR(20)` | Required | `DESKTOP`, `MOBILE`, `TABLET` | Device Enum | Non-unique | Allowed client device type enum. |
| `landing_page` | `VARCHAR(255)` | Required | URI path: `/campaigns/...` | Path String | Non-unique | Entry landing page URL. |
| `referrer` | `VARCHAR(255)` | Optional | URL format: `https://...` | URI String | Non-unique | Referring web property. |
| `is_authenticated`| `BOOLEAN` | Required | `TRUE`, `FALSE` | Boolean Flag | Non-unique | User authentication status. |
| `created_at` | `DATETIME` | Required | ISO 8601 Timestamp | UTC Date | Non-unique | Timestamp equal to `started_at`. |

---

### 7. `Touchpoint` (Marketing Interactions)
Discrete online and offline marketing interactions. Offline touches have `channel_medium="OFFLINE"` and `session_id=None`.

| Field Name | Data Type | Req / Opt | Allowed Values | Units | Uniqueness | Validation Rule |
| :--- | :--- | :---: | :--- | :---: | :---: | :--- |
| `touchpoint_id` | `VARCHAR(100)`| Required | Format: `TOUCH-CON-2026-[0-9]{6}-[0-9]{6}` | Identifier | **Unique (PK)** | Immutable key referencing contact ID. |
| `contact_id` | `VARCHAR(50)` | Required | FK &rarr; `contacts.contact_id` | Foreign Key | Non-unique | Referential integrity to valid contact. |
| `campaign_id` | `VARCHAR(50)` | Required | FK &rarr; `campaigns.campaign_id` | Foreign Key | Non-unique | Referential integrity to valid campaign. |
| `channel_id` | `VARCHAR(50)` | Required | FK &rarr; `channels.channel_id` | Foreign Key | Non-unique | Referential integrity to valid channel. |
| `creative_id` | `VARCHAR(50)` | Optional | FK &rarr; `creatives.creative_id` | Foreign Key | Non-unique | Nullable or valid creative link. |
| `session_id` | `VARCHAR(50)` | Optional | FK &rarr; `web_sessions.session_id`| Foreign Key | Non-unique | Required for `ONLINE`; **must be NULL** for `OFFLINE`. |
| `touch_type` | `VARCHAR(30)` | Required | `CLICK`, `EMAIL_OPEN`, `IMPRESSION`, `WEBINAR`, `IN_PERSON`, `TRADE_SHOW` | Type Enum | Non-unique | Interaction type enum. |
| `channel_medium`| `VARCHAR(20)` | Required | `ONLINE`, `OFFLINE` | Medium Enum | Non-unique | Medium classification. |
| `occurred_at` | `DATETIME` | Required | ISO 8601 Timestamp | UTC Date | Non-unique | Must precede order conversion to receive attribution credit. |
| `interaction_cost`| `FLOAT` | Required | Positive float: `0.0` to `200.0` | INR (`₹`) | Non-unique | Non-negative interaction cost (`>= 0.0`). |
| `created_at` | `DATETIME` | Required | ISO 8601 Timestamp | UTC Date | Non-unique | Timestamp equal to `occurred_at`. |

---

### 8. `Lead` (Inquiries & Form Submissions)
Marketing qualified leads derived from early-stage journey touchpoints.

| Field Name | Data Type | Req / Opt | Allowed Values | Units | Uniqueness | Validation Rule |
| :--- | :--- | :---: | :--- | :---: | :---: | :--- |
| `lead_id` | `VARCHAR(50)` | Required | Format: `LEAD-2026-[0-9]{6}` | Identifier | **Unique (PK)** | Immutable, zero-padded identifier. |
| `contact_id` | `VARCHAR(50)` | Required | FK &rarr; `contacts.contact_id` | Foreign Key | Non-unique | Referential integrity to contact. |
| `campaign_id` | `VARCHAR(50)` | Required | FK &rarr; `campaigns.campaign_id` | Foreign Key | Non-unique | Derived from initial driving campaign. |
| `lead_source` | `VARCHAR(50)` | Required | FK &rarr; `channels.channel_id` | Foreign Key | Non-unique | Derived from initial touchpoint channel. |
| `status` | `VARCHAR(30)` | Required | `NEW`, `QUALIFIED`, `CONTACTED`, `UNQUALIFIED` | Status Enum | Non-unique | Allowed lead lifecycle status. |
| `created_at` | `DATETIME` | Required | ISO 8601 Timestamp | UTC Date | Non-unique | Derived: `first_touch.occurred_at + lag`. |

---

### 9. `Opportunity` (Sales Pipeline Deals)
Negotiation deals with expected revenue and target close dates.

| Field Name | Data Type | Req / Opt | Allowed Values | Units | Uniqueness | Validation Rule |
| :--- | :--- | :---: | :--- | :---: | :---: | :--- |
| `opportunity_id`| `VARCHAR(50)`| Required | Format: `OPP-2026-[0-9]{6}` | Identifier | **Unique (PK)** | Immutable, zero-padded identifier. |
| `contact_id` | `VARCHAR(50)` | Required | FK &rarr; `contacts.contact_id` | Foreign Key | Non-unique | Referential integrity to contact. |
| `lead_id` | `VARCHAR(50)` | Optional | FK &rarr; `leads.lead_id` | Foreign Key | Non-unique | Derived link to predecessor lead. |
| `campaign_id` | `VARCHAR(50)` | Required | FK &rarr; `campaigns.campaign_id` | Foreign Key | Non-unique | Driving campaign. |
| `stage` | `VARCHAR(30)` | Required | `PROSPECTING`, `QUALIFICATION`, `PROPOSAL`, `NEGOTIATION`, `CLOSED_WON`, `CLOSED_LOST` | Stage Enum | Non-unique | Allowed pipeline stage enum. |
| `expected_revenue`| `FLOAT` | Required | Positive float: `1500.0` to `50000.0` | INR (`₹`) | Non-unique | Non-negative deal value (`>= 0.0`). |
| `close_date` | `DATETIME` | Optional | ISO 8601 Timestamp | UTC Date | Non-unique | Required when `stage` starts with `CLOSED`. |
| `created_at` | `DATETIME` | Required | ISO 8601 Timestamp | UTC Date | Non-unique | Must be `>= lead.created_at`. |
| `updated_at` | `DATETIME` | Required | ISO 8601 Timestamp | UTC Date | Non-unique | Final update timestamp. |

---

### 10. `Order` (Closed Transactions & Recognized Revenue)
Commercial transactions recognizing finalized revenue. Flagged duplicate orders are quarantined.

| Field Name | Data Type | Req / Opt | Allowed Values | Units | Uniqueness | Validation Rule |
| :--- | :--- | :---: | :--- | :---: | :---: | :--- |
| `order_id` | `VARCHAR(50)` | Required | Format: `ORD-2026-[0-9]{6}` | Identifier | **Unique (PK)** | Immutable, zero-padded identifier. |
| `opportunity_id`| `VARCHAR(50)`| Required | FK &rarr; `opportunities.opportunity_id`| Foreign Key | Non-unique | Must link to `CLOSED_WON` opportunity. |
| `contact_id` | `VARCHAR(50)` | Required | FK &rarr; `contacts.contact_id` | Foreign Key | Non-unique | Converted customer. |
| `order_number` | `VARCHAR(50)` | Required | Format: `ATT-ORD-[0-9]{8}` | Order String | Non-unique (due to Anomaly 1) | Deduplication check: duplicates flagged with `is_duplicate_flag=True`. |
| `order_date` | `DATETIME` | Required | ISO 8601 Timestamp | UTC Date | Non-unique | Conversion timestamp; derived from `opportunity.close_date`. |
| `amount` | `FLOAT` | Required | Strictly positive float: `amount > 0` | INR (`₹`) | Non-unique | Derived from `opportunity.expected_revenue`. |
| `currency` | `VARCHAR(10)` | Required | `INR` | ISO Currency | Non-unique | Base platform currency. |
| `status` | `VARCHAR(30)` | Required | `COMPLETED`, `CANCELLED`, `REFUNDED`| Status Enum | Non-unique | Transaction state. |
| `is_duplicate_flag`| `BOOLEAN` | Required | `TRUE`, `FALSE` | Boolean Flag | Non-unique | When `TRUE`, excluded from attribution and financial totals. |
| `created_at` | `DATETIME` | Required | ISO 8601 Timestamp | UTC Date | Non-unique | Creation timestamp. |

---

### 11. `CostRecord` (Media Spend & Production Expenditures)
Expenditure records representing marketing costs, reconciled against campaign budgets.

| Field Name | Data Type | Req / Opt | Allowed Values | Units | Uniqueness | Validation Rule |
| :--- | :--- | :---: | :--- | :---: | :---: | :--- |
| `cost_id` | `VARCHAR(50)` | Required | Format: `CST-2026-[0-9]{6}` | Identifier | **Unique (PK)** | Immutable, zero-padded identifier. |
| `campaign_id` | `VARCHAR(50)` | Required | FK &rarr; `campaigns.campaign_id` | Foreign Key | Non-unique | Referential integrity to campaign. |
| `channel_id` | `VARCHAR(50)` | Required | FK &rarr; `channels.channel_id` | Foreign Key | Non-unique | Referential integrity to channel. |
| `recorded_date` | `DATETIME` | Required | ISO 8601 Timestamp | UTC Date | Non-unique | Must fall between campaign start and end dates. |
| `amount` | `FLOAT` | Required | Strictly positive: `amount > 0` | Currency Units | Non-unique | Non-negative expenditure amount. |
| `currency` | `VARCHAR(10)` | Required | Standard: `INR`; Anomaly: `USD`, `EUR` | ISO Currency | Non-unique | Incompatible currencies flagged under Anomaly 3. |
| `cost_type` | `VARCHAR(30)` | Required | `MEDIA_SPEND`, `AGENCY_FEE`, `PRODUCTION` | Cost Enum | Non-unique | Allowed expenditure classification enum. |
| `created_at` | `DATETIME` | Required | ISO 8601 Timestamp | UTC Date | Non-unique | Creation timestamp. |

---

### 12. `AttributionResult` (Attributed Revenue Allocation)
Calculated attribution weights and revenue credits allocated across models.

| Field Name | Data Type | Req / Opt | Allowed Values | Units | Uniqueness | Validation Rule |
| :--- | :--- | :---: | :--- | :---: | :---: | :--- |
| `result_id` | `VARCHAR(50)` | Required | Format: `ATT-[FT/LT/MT]-[0-9]+` | Identifier | **Unique (PK)** | Immutable unique identifier. |
| `model_id` | `VARCHAR(50)` | Required | FK &rarr; `attribution_models` (`MDL-FIRST-TOUCH`, `MDL-LAST-TOUCH`, `MDL-MULTI-TOUCH`) | Foreign Key | Non-unique | Attribution model reference. |
| `opportunity_id`| `VARCHAR(50)`| Required | FK &rarr; `opportunities.opportunity_id`| Foreign Key | Non-unique | Predecessor opportunity. |
| `order_id` | `VARCHAR(50)` | Required | FK &rarr; `orders.order_id` | Foreign Key | Non-unique | Valid completed, non-duplicate order. |
| `campaign_id` | `VARCHAR(50)` | Required | FK &rarr; `campaigns.campaign_id` | Foreign Key | Non-unique | Credited campaign. |
| `channel_id` | `VARCHAR(50)` | Required | FK &rarr; `channels.channel_id` | Foreign Key | Non-unique | Credited channel. |
| `touchpoint_id` | `VARCHAR(100)`| Required | FK &rarr; `touchpoints.touchpoint_id` | Foreign Key | Non-unique | Credited touchpoint; must satisfy `occurred_at <= order_date`. |
| `attribution_weight`| `FLOAT`| Required | Float: $0.0 \le w \le 1.0$ | Weight Fraction| Non-unique | Per-order sum: $\sum w = 1.0 \pm 10^{-4}$. |
| `attributed_revenue`| `FLOAT`| Required | Float: $w \times \text{order.amount}$ | INR (`₹`) | Non-unique | Per-model total revenue equals valid closed order revenue. |
| `touchpoint_timestamp`| `DATETIME`| Required | ISO 8601 Timestamp | UTC Date | Non-unique | Touchpoint occurrence time. |
| `conversion_timestamp`| `DATETIME`| Required | ISO 8601 Timestamp | UTC Date | Non-unique | Order conversion time; must satisfy `touch_time <= conv_time`. |
| `evaluation_period`| `VARCHAR(20)`| Required | `TRAIN`, `VALIDATION`, `TEST` | Period Enum | Non-unique | Determined strictly by `conversion_timestamp`. |
