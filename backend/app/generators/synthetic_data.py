"""Deterministic Synthetic Data Generator for Marketing Attribution Platform.
Strictly reproducible via fixed seed (20261022).
Implements master data, realistic multi-touch customer journeys, dependent entities,
derived attributes, and 5 mandatory labelled anomaly edge cases.

Supports two configurations:
- STARTER (50 campaigns, 1,000 contacts, 4,000 touchpoints, 200 opportunities)
- FULL BASELINE (500 campaigns, 50,000 contacts, 200,000 touchpoints, 10,000 opportunities)
"""
import random
import hashlib
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple, Set
from pathlib import Path

from sqlalchemy.orm import Session

from backend.app.generators.config import (
    RANDOM_SEED, BASE_CURRENCY, LOOKBACK_WINDOW_DAYS,
    DatasetConfig, STARTER_CONFIG, FULL_BASELINE_CONFIG, FULL_CONFIG,
    PERIOD_START, TEST_END, get_period
)
from backend.app.generators.ground_truth import GroundTruthTracker
from backend.app.models.entities import (
    Channel, Audience, Creative, Campaign, Contact, WebSession,
    Touchpoint, Lead, Opportunity, Order, CostRecord,
    CampaignChannel, CampaignAudience, CampaignCreative, ContactIdentity,
    AttributionModel, DataGenerationRun
)

class SyntheticDataGenerator:
    def __init__(self, db: Session, config: DatasetConfig = STARTER_CONFIG, seed: int = RANDOM_SEED):
        self.db = db
        self.config = config
        self.seed = seed
        self.rng = random.Random(seed)
        self.gt_tracker = GroundTruthTracker()
        self.run_id = f"RUN-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{config.name}"

    def _bulk_save_chunked(self, objects: list, chunk_size: int = 5000):
        """Save objects in chunks to prevent memory bloat and SQLite statement limits."""
        if not objects:
            return
        for i in range(0, len(objects), chunk_size):
            chunk = objects[i:i + chunk_size]
            self.db.bulk_save_objects(chunk)
            self.db.commit()

    def generate(self) -> Dict[str, Any]:
        """Execute full deterministic generation pipeline.
        Sequence:
        1. Attribution Models
        2. Master parent entities (Channels, Audiences, Creatives, Campaigns, Bridge Tables, Contacts)
        3. Phase 1: Valid Baseline Generation (Identities, Costs, Journeys, Conversions)
        4. Phase 2: Explicit Labelled Anomaly Injection
        5. Separate Ground Truth Export (JSON & CSV)
        6. Summary Checksums & Run Record
        """
        print(f"Starting deterministic data generation [{self.config.name}] with seed {self.seed}...")
        start_time = datetime.utcnow()

        # Record generation run start
        run_record = DataGenerationRun(
            run_id=self.run_id,
            config_name=self.config.name,
            seed=self.seed,
            status="RUNNING",
            started_at=start_time
        )
        self.db.add(run_record)
        self.db.commit()

        # Step 1: Default Attribution Models
        self._create_attribution_models()

        # Step 2: Master Parent Data (Generated before dependent records)
        channels = self._generate_channels()
        audiences = self._generate_audiences()
        creatives = self._generate_creatives()
        campaigns = self._generate_campaigns(channels, audiences, creatives)
        contacts = self._generate_contacts()

        # Step 3: Dependent Records (Phase 1: Valid Baseline -> Phase 2: Anomaly Injection)
        sessions, touchpoints, leads, opportunities, orders, costs = self._generate_customer_journeys(
            contacts, campaigns, channels, creatives
        )

        # Step 4: Export Ground Truth (Separated from feature tables)
        export_dir = Path(__file__).resolve().parent.parent.parent.parent / "data" / "ground_truth"
        gt_metadata = self.gt_tracker.export(export_dir)

        # Step 5: Calculate Summary Counts & SHA-256 Checksums
        row_counts = {
            "channels": len(channels),
            "audiences": len(audiences),
            "creatives": len(creatives),
            "campaigns": len(campaigns),
            "contacts": len(contacts),
            "web_sessions": len(sessions),
            "touchpoints": len(touchpoints),
            "leads": len(leads),
            "opportunities": len(opportunities),
            "orders": len(orders),
            "cost_records": len(costs),
            "ground_truth_anomalies": gt_metadata["total_anomalies_recorded"]
        }

        # Deterministic checksum across row counts and configuration parameters
        checksum_payload = f"{self.config.name}_{self.seed}_{json.dumps(row_counts, sort_keys=True)}"
        data_checksum = hashlib.sha256(checksum_payload.encode("utf-8")).hexdigest()

        # Update run record
        run_record.status = "COMPLETED"
        run_record.completed_at = datetime.utcnow()
        run_record.row_counts_json = json.dumps(row_counts, indent=2)
        run_record.checksums_json = json.dumps({
            "dataset_sha256": data_checksum,
            **gt_metadata
        }, indent=2)
        self.db.commit()

        duration = (datetime.utcnow() - start_time).total_seconds()
        print(f"Data generation [{self.config.name}] completed successfully in {duration:.2f}s.")
        return {
            "run_id": self.run_id,
            "status": "COMPLETED",
            "seed": self.seed,
            "config": self.config.name,
            "row_counts": row_counts,
            "checksum": data_checksum,
            "ground_truth": gt_metadata,
            "duration_seconds": round(duration, 2)
        }

    def _create_attribution_models(self):
        """Seed core attribution model configurations if not present."""
        models = [
            AttributionModel(
                model_id="MDL-FIRST-TOUCH",
                model_code="FIRST_TOUCH",
                name="First-Touch Attribution",
                description="Attributes 100% credit to the first eligible marketing touchpoint within lookback window.",
                lookback_window_days=LOOKBACK_WINDOW_DAYS,
                version="1.0.0",
                is_active=True
            ),
            AttributionModel(
                model_id="MDL-LAST-TOUCH",
                model_code="LAST_TOUCH",
                name="Last-Touch Attribution",
                description="Attributes 100% credit to the last eligible marketing touchpoint before conversion.",
                lookback_window_days=LOOKBACK_WINDOW_DAYS,
                version="1.0.0",
                is_active=True
            ),
            AttributionModel(
                model_id="MDL-MULTI-TOUCH",
                model_code="MULTI_TOUCH_LINEAR",
                name="Multi-Touch Attribution (Linear / Equal-Weight)",
                description="Attributes equal credit (1/N) across all N eligible marketing touchpoints.",
                lookback_window_days=LOOKBACK_WINDOW_DAYS,
                version="1.0.0",
                is_active=True
            )
        ]
        for m in models:
            existing = self.db.query(AttributionModel).filter_by(model_id=m.model_id).first()
            if not existing:
                self.db.add(m)
        self.db.commit()

    def _generate_channels(self) -> List[Channel]:
        """Generate static marketing channels (6 Online, 2 Offline)."""
        channel_defs = [
            ("CHN-PAID-SEARCH", "Paid Search (Google/Bing Ads)", "ONLINE", "CPC"),
            ("CHN-ORGANIC", "Organic Search (SEO)", "ONLINE", "FLAT"),
            ("CHN-EMAIL", "Email Marketing", "ONLINE", "FLAT"),
            ("CHN-SOCIAL", "Paid Social (LinkedIn/Meta)", "ONLINE", "CPC"),
            ("CHN-DISPLAY", "Display & Programmatic Ads", "ONLINE", "CPM"),
            ("CHN-EVENT", "Trade Shows & Webinars", "OFFLINE", "FLAT"),
            ("CHN-REFERRAL", "Partner & Affiliate Referral", "ONLINE", "COMMISSION"),
            ("CHN-DIRECT", "Direct Mail & Field Outreach", "OFFLINE", "FLAT"),
        ]
        channels = []
        for cid, name, ctype, cstruct in channel_defs:
            c = Channel(
                channel_id=cid,
                name=name,
                channel_type=ctype,
                cost_structure=cstruct,
                is_active=True,
                created_at=datetime(2025, 12, 1)
            )
            self.db.merge(c)
            channels.append(c)
        self.db.commit()
        return channels

    def _generate_audiences(self) -> List[Audience]:
        """Generate target audiences."""
        audiences = []
        types = ["B2B_ENTERPRISE", "SMB_GROWTH", "FINTECH", "HEALTHCARE", "RETAIL_ECOMMERCE", "DEVELOPER_TECH"]
        for i in range(1, self.config.num_audiences + 1):
            aid = f"AUD-2026-{i:06d}"
            stype = types[(i - 1) % len(types)]
            aud = Audience(
                audience_id=aid,
                name=f"Audience Segment - {stype.replace('_', ' ').title()} #{i}",
                segment_type=stype,
                target_criteria=f"Targeting companies size {10 * i}-{500 * i} in {stype}",
                created_at=datetime(2025, 12, 10)
            )
            self.db.merge(aud)
            audiences.append(aud)
        self.db.commit()
        return audiences

    def _generate_creatives(self) -> List[Creative]:
        """Generate marketing creatives."""
        creatives = []
        formats = ["BANNER", "VIDEO", "TEXT_AD", "EMAIL_TEMPLATE", "WEBINAR_DECK", "PRODUCT_ONE_PAGER"]
        themes = ["ROI Optimization", "Scale Fast", "AI Automation", "Security First", "Enterprise Efficiency"]
        for i in range(1, self.config.num_creatives + 1):
            c_id = f"CRT-2026-{i:06d}"
            fmt = formats[(i - 1) % len(formats)]
            theme = themes[(i - 1) % len(themes)]
            c = Creative(
                creative_id=c_id,
                name=f"Creative {fmt.title()} - {theme} (V{i})",
                creative_format=fmt,
                asset_url=f"https://cdn.marketingplatform.io/creatives/{c_id}.png",
                message_theme=theme,
                created_at=datetime(2025, 12, 15)
            )
            self.db.merge(c)
            creatives.append(c)
        self.db.commit()
        return creatives

    def _generate_campaigns(
        self, channels: List[Channel], audiences: List[Audience], creatives: List[Creative]
    ) -> List[Campaign]:
        """Generate master campaigns with channels, budgets, and bridge tables."""
        campaigns = []
        campaign_channels = []
        campaign_audiences = []
        campaign_creatives = []

        total_days = (TEST_END - PERIOD_START).days

        for i in range(1, self.config.num_campaigns + 1):
            cmp_id = f"CMP-2026-{i:06d}"
            primary_channel = channels[(i - 1) % len(channels)]
            
            # Start date distributed throughout the year
            start_offset = self.rng.randint(0, max(0, total_days - 60))
            start_date = PERIOD_START + timedelta(days=start_offset)
            duration_days = self.rng.randint(30, 180)
            end_date = min(TEST_END, start_date + timedelta(days=duration_days))

            budget = round(self.rng.uniform(5000.0, 150000.0), 2)
            status = "COMPLETED" if end_date < datetime(2026, 11, 1) else "ACTIVE"

            cmp = Campaign(
                campaign_id=cmp_id,
                name=f"Campaign {i:04d} - {primary_channel.name.split('(')[0].strip()}",
                channel_id=primary_channel.channel_id,
                budget=budget,
                currency=BASE_CURRENCY,
                status=status,
                start_date=start_date,
                end_date=end_date,
                created_at=start_date - timedelta(days=7),
                updated_at=start_date
            )
            campaigns.append(cmp)

            # Primary Channel Bridge Record
            campaign_channels.append(CampaignChannel(
                campaign_id=cmp_id,
                channel_id=primary_channel.channel_id,
                is_primary=True
            ))

            # Additional supporting channel (multi-channel campaign)
            sec_channel = channels[self.rng.randint(0, len(channels) - 1)]
            if sec_channel.channel_id != primary_channel.channel_id:
                campaign_channels.append(CampaignChannel(
                    campaign_id=cmp_id,
                    channel_id=sec_channel.channel_id,
                    is_primary=False
                ))

            # Associate 1-2 audiences
            aud = audiences[self.rng.randint(0, len(audiences) - 1)]
            campaign_audiences.append(CampaignAudience(
                campaign_id=cmp_id,
                audience_id=aud.audience_id
            ))

            # Associate 1-2 creatives
            crt = creatives[self.rng.randint(0, len(creatives) - 1)]
            campaign_creatives.append(CampaignCreative(
                campaign_id=cmp_id,
                creative_id=crt.creative_id
            ))

        self._bulk_save_chunked(campaigns)
        self._bulk_save_chunked(campaign_channels)
        self._bulk_save_chunked(campaign_audiences)
        self._bulk_save_chunked(campaign_creatives)
        return campaigns

    def _generate_contacts(self) -> List[Contact]:
        """Generate deterministic contact records."""
        contacts = []
        first_names = [
            "Sharanya", "Srinivas", "Shailaja", "Krish", "Shravika", "Aarav", "Ananya", "Rohan",
            "Pooja", "Aditya", "Sneha", "Rahul", "Priya", "Vikram", "Neha", "Arjun",
            "Kavya", "Suresh", "Divya", "Kiran", "Manish", "Deepika", "Rajesh", "Swati",
            "Naveen", "Meera", "Gautam", "Sunita", "Harish", "Anita", "Vikas", "Sangeeta",
            "Pranav", "Bhavna", "Kunal", "Tanvi", "Alok", "Pallavi", "Sachin", "Ritu"
        ]
        last_names = [
            "Kavati", "Sharma", "Verma", "Patel", "Reddy", "Rao", "Nair", "Iyer",
            "Mehta", "Singh", "Kumar", "Gupta", "Deshmukh", "Joshi", "Bose", "Choudhury",
            "Pillai", "Bhat", "Chatterjee", "Mishra", "Agarwal", "Saxena", "Pandey", "Ghosh",
            "Kulkarni", "Chauhan", "Bhattacharya", "Menon", "Trivedi", "Banerjee", "Sengupta", "Das"
        ]

        total_days = (TEST_END - PERIOD_START).days

        for i in range(1, self.config.num_contacts + 1):
            cid = f"CON-2026-{i:06d}"
            if i == 1:
                # Featured Customer Journey: Shravika Kavati
                fn = "Shravika"
                ln = "Kavati"
                email = "shravika.kavati@gmail.com"
                phone = "+91-98765-43210"
            else:
                fn = first_names[i % len(first_names)]
                ln = last_names[(i // len(first_names)) % len(last_names)]
                email = f"user.{i:06d}.{fn.lower()}.{ln.lower()}@corpmail{i % 20}.com"
                phone = f"+91-98765-{10000 + (i % 89999):05d}"

            # First seen timestamp
            offset = self.rng.randint(0, max(0, total_days - 60))
            first_seen = PERIOD_START + timedelta(days=offset, hours=self.rng.randint(8, 20))

            contact = Contact(
                contact_id=cid,
                first_name=fn,
                last_name=ln,
                email=email,
                phone=phone,
                lifecycle_stage="SUBSCRIBER",
                first_seen_at=first_seen,
                created_at=first_seen
            )
            contacts.append(contact)

        self._bulk_save_chunked(contacts)
        return contacts

    def _generate_customer_journeys(
        self,
        contacts: List[Contact],
        campaigns: List[Campaign],
        channels: List[Channel],
        creatives: List[Creative]
    ) -> Tuple[List[WebSession], List[Touchpoint], List[Lead], List[Opportunity], List[Order], List[CostRecord]]:
        """Two-phase generation:
        Phase 1: Pure valid baseline records (Identities, Costs, Journeys, Conversions).
        Phase 2: Explicit labelled anomaly injection (5 scenarios logged to GroundTruthTracker).
        """
        channel_map = {c.channel_id: c for c in channels}
        touch_types = {
            "CHN-PAID-SEARCH": ("CLICK", "ONLINE", 1.85),
            "CHN-ORGANIC": ("CLICK", "ONLINE", 0.0),
            "CHN-EMAIL": ("EMAIL_OPEN", "ONLINE", 0.15),
            "CHN-SOCIAL": ("CLICK", "ONLINE", 2.40),
            "CHN-DISPLAY": ("IMPRESSION", "ONLINE", 0.45),
            "CHN-EVENT": ("WEBINAR", "OFFLINE", 120.0),
            "CHN-REFERRAL": ("CLICK", "ONLINE", 15.0),
            "CHN-DIRECT": ("IN_PERSON", "OFFLINE", 75.0),
        }

        # =====================================================================
        # PHASE 1: GENERATE CLEAN VALID BASELINE RECORDS
        # =====================================================================

        # 1. Baseline Cost Records (All in base currency INR, distributed across campaign duration)
        costs: List[CostRecord] = []
        cost_id_counter = 1
        for cmp in campaigns:
            num_costs = self.rng.randint(3, 8)
            time_span = max(1, (cmp.end_date - cmp.start_date).days)
            step_days = max(1, time_span // num_costs)
            spend_per_record = round(cmp.budget * self.rng.uniform(0.7, 1.1) / num_costs, 2)

            for ci in range(num_costs):
                cost_date = cmp.start_date + timedelta(days=ci * step_days)
                cst = CostRecord(
                    cost_id=f"CST-2026-{cost_id_counter:06d}",
                    campaign_id=cmp.campaign_id,
                    channel_id=cmp.channel_id,
                    recorded_date=cost_date,
                    amount=spend_per_record,
                    currency=BASE_CURRENCY,
                    cost_type="MEDIA_SPEND" if ci % 2 == 0 else "AGENCY_FEE",
                    created_at=cost_date
                )
                costs.append(cst)
                cost_id_counter += 1

        # 2. Baseline Contact Identities
        identities: List[ContactIdentity] = []
        identity_counter = 1
        contact_cookies: Dict[str, str] = {}

        for contact in contacts:
            cookie_id = f"CK-{contact.contact_id[-6:]}-{self.rng.randint(1000, 9999)}"
            contact_cookies[contact.contact_id] = cookie_id
            email_hash = hashlib.sha256(contact.email.encode("utf-8")).hexdigest()[:24]

            # Cookie Identity Evidence
            identities.append(ContactIdentity(
                identity_id=f"IDN-2026-{identity_counter:06d}",
                contact_id=contact.contact_id,
                identity_type="COOKIE",
                identity_value=cookie_id,
                evidence_source="FORM_SUBMISSION",
                first_observed_at=contact.first_seen_at,
                created_at=contact.first_seen_at
            ))
            identity_counter += 1

            # Email Hash Identity Evidence
            identities.append(ContactIdentity(
                identity_id=f"IDN-2026-{identity_counter:06d}",
                contact_id=contact.contact_id,
                identity_type="EMAIL_HASH",
                identity_value=email_hash,
                evidence_source="ACCOUNT_SIGNUP",
                first_observed_at=contact.first_seen_at,
                created_at=contact.first_seen_at
            ))
            identity_counter += 1

        # 3. Baseline Customer Journeys & Conversions
        sessions: List[WebSession] = []
        touchpoints: List[Touchpoint] = []
        leads: List[Lead] = []
        opportunities: List[Opportunity] = []
        orders: List[Order] = []

        session_counter = 1
        lead_counter = 1
        opp_counter = 1
        order_counter = 1
        touch_seq_counters: Dict[str, int] = {c.contact_id: 0 for c in contacts}

        # Select exactly config.num_opportunities converting contacts (Contact #1 Shravika Kavati always converts!)
        num_converted = min(self.config.num_opportunities, len(contacts))
        other_indices = [i for i in range(1, len(contacts))]
        sample_size = max(0, num_converted - 1)
        converted_indices = set([0] + self.rng.sample(other_indices, min(sample_size, len(other_indices))))

        # Touchpoint target budget
        target_touchpoints = self.config.num_touchpoints
        converted_contacts_count = len(converted_indices)
        non_converted_contacts_count = len(contacts) - converted_contacts_count

        # Estimate average touches per group to hit total target touchpoints
        # Converted contacts have longer multi-touch journeys (e.g. 5 to 8 touches)
        # Non-converted contacts have 1 to 4 touches
        for idx, contact in enumerate(contacts):
            is_converting = idx in converted_indices
            cookie_id = contact_cookies[contact.contact_id]

            # Number of touches in this contact journey
            if is_converting:
                num_touches = self.rng.randint(4, 8)
            else:
                num_touches = self.rng.randint(1, 4)

            # Multi-campaign customer journey: Select 1 to 3 distinct campaigns
            num_camp_choices = min(len(campaigns), self.rng.randint(2, 3) if is_converting else self.rng.randint(1, 2))
            journey_campaigns = self.rng.sample(campaigns, num_camp_choices)

            # Journey progression timing (Long conversion windows modeled: up to 80 days)
            current_time = contact.first_seen_at
            contact_touches = []

            for t_idx in range(num_touches):
                campaign = journey_campaigns[t_idx % len(journey_campaigns)]
                channel = channel_map[campaign.channel_id]
                creative = creatives[self.rng.randint(0, len(creatives) - 1)]
                touch_def = touch_types.get(channel.channel_id, ("CLICK", "ONLINE", 1.0))

                sess_ref_id = None
                # Offline touchpoint handling: channels like Events & Direct Mail have NO web session
                if touch_def[1] == "ONLINE":
                    sess_id = f"SES-2026-{session_counter:06d}"
                    sess_cookie = f"CK-{contact.contact_id[-6:]}-{session_counter:06d}"
                    session_start = current_time
                    session_duration_mins = self.rng.randint(2, 35)
                    session_end = session_start + timedelta(minutes=session_duration_mins)

                    sess = WebSession(
                        session_id=sess_id,
                        contact_id=contact.contact_id,
                        anonymous_cookie_id=sess_cookie,
                        started_at=session_start,
                        ended_at=session_end,
                        device_type="DESKTOP" if self.rng.random() < 0.6 else "MOBILE",
                        landing_page=f"/campaigns/{campaign.campaign_id}",
                        referrer=f"https://{channel.channel_id.lower().replace('chn-', '')}.com",
                        is_authenticated=True,
                        created_at=session_start
                    )
                    sessions.append(sess)
                    sess_ref_id = sess.session_id

                    # Record supporting cookie identity in identities
                    identities.append(ContactIdentity(
                        identity_id=f"IDN-2026-{identity_counter:06d}",
                        contact_id=contact.contact_id,
                        identity_type="COOKIE",
                        identity_value=sess_cookie,
                        evidence_source="WEB_SESSION",
                        first_observed_at=session_start,
                        created_at=session_start
                    ))
                    identity_counter += 1
                    session_counter += 1

                touch_seq_counters[contact.contact_id] += 1
                t_seq = touch_seq_counters[contact.contact_id]
                touch_id = f"TOUCH-{contact.contact_id}-{t_seq:06d}"

                tp = Touchpoint(
                    touchpoint_id=touch_id,
                    contact_id=contact.contact_id,
                    campaign_id=campaign.campaign_id,
                    channel_id=channel.channel_id,
                    creative_id=creative.creative_id,
                    session_id=sess_ref_id,
                    touch_type=touch_def[0],
                    channel_medium=touch_def[1],
                    occurred_at=current_time,
                    interaction_cost=touch_def[2],
                    created_at=current_time
                )
                touchpoints.append(tp)
                contact_touches.append(tp)

                # Advance journey timestamp: realistic interval of 1 to 14 days
                current_time += timedelta(days=self.rng.randint(1, 14), hours=self.rng.randint(1, 10))
                if current_time > TEST_END:
                    break

            # Conversion Pipeline (Lead -> Opportunity -> Order)
            if is_converting and contact_touches:
                first_touch = contact_touches[0]
                last_touch = contact_touches[-1]

                # Derived Lead Record
                lead_id = f"LEAD-2026-{lead_counter:06d}"
                lead_created = first_touch.occurred_at + timedelta(hours=self.rng.randint(2, 24))
                lead = Lead(
                    lead_id=lead_id,
                    contact_id=contact.contact_id,
                    campaign_id=first_touch.campaign_id,
                    lead_source=first_touch.channel_id,
                    status="QUALIFIED",
                    created_at=lead_created
                )
                leads.append(lead)
                lead_counter += 1

                # Derived Opportunity Record
                opp_id = f"OPP-2026-{opp_counter:06d}"
                # Contact 0 (Shravika Kavati) and majority close won
                opp_stage = "CLOSED_WON" if (idx == 0 or self.rng.random() < 0.85) else "CLOSED_LOST"
                opp_amount = round(self.rng.uniform(1500.0, 45000.0), 2)
                
                # Ensure conversion occurs shortly after last touchpoint, but strictly <= 85 days from first touch
                conversion_time = last_touch.occurred_at + timedelta(days=self.rng.randint(1, 10), hours=self.rng.randint(1, 8))
                if (conversion_time - first_touch.occurred_at).days > 85:
                    conversion_time = first_touch.occurred_at + timedelta(days=85)

                opp = Opportunity(
                    opportunity_id=opp_id,
                    contact_id=contact.contact_id,
                    lead_id=lead.lead_id,
                    campaign_id=last_touch.campaign_id,
                    stage=opp_stage,
                    expected_revenue=opp_amount,
                    close_date=conversion_time if opp_stage.startswith("CLOSED") else None,
                    created_at=lead_created + timedelta(days=2),
                    updated_at=conversion_time
                )
                opportunities.append(opp)
                opp_counter += 1

                # Derived Order Record for CLOSED_WON opportunities
                if opp_stage == "CLOSED_WON":
                    contact.lifecycle_stage = "CUSTOMER"
                    ord_id = f"ORD-2026-{order_counter:06d}"
                    ord_num = f"ATT-ORD-{order_counter:08d}"
                    order = Order(
                        order_id=ord_id,
                        opportunity_id=opp.opportunity_id,
                        contact_id=contact.contact_id,
                        order_number=ord_num,
                        order_date=conversion_time,
                        amount=opp_amount,
                        currency=BASE_CURRENCY,
                        status="COMPLETED",
                        is_duplicate_flag=False,
                        created_at=conversion_time
                    )
                    orders.append(order)
                    order_counter += 1

        # =====================================================================
        # PHASE 2: EXPLICIT LABELLED ANOMALY INJECTION
        # =====================================================================

        # Anomaly 1: Duplicate Revenue (Duplicate orders referencing same order number & opportunity)
        eligible_orders_for_dup = [o for o in orders if o.contact_id != "CON-2026-000001"]
        dup_targets = eligible_orders_for_dup[:self.config.duplicate_revenue_count]
        for orig_order in dup_targets:
            dup_ord_id = f"ORD-2026-{order_counter:06d}"
            order_counter += 1
            dup_order = Order(
                order_id=dup_ord_id,
                opportunity_id=orig_order.opportunity_id,
                contact_id=orig_order.contact_id,
                order_number=orig_order.order_number,
                order_date=orig_order.order_date + timedelta(hours=1),
                amount=orig_order.amount,
                currency=BASE_CURRENCY,
                status="COMPLETED",
                is_duplicate_flag=True,
                created_at=orig_order.order_date + timedelta(hours=1)
            )
            orders.append(dup_order)

            self.gt_tracker.record(
                case_id=f"GT-ANO1-{dup_ord_id}",
                entity_type="ORDER",
                entity_id=dup_ord_id,
                anomaly_type="DUPLICATE_REVENUE",
                expected_decision="REJECT_DUPLICATE_REVENUE",
                severity="CRITICAL",
                description=f"Duplicate order {dup_ord_id} references existing order number {orig_order.order_number} and opportunity {orig_order.opportunity_id}.",
                related_ids=f"{orig_order.order_id},{orig_order.opportunity_id}"
            )

        # Anomaly 2: Post-Conversion Touchpoints (Touches strictly after conversion order date)
        valid_orders = [o for o in orders if not o.is_duplicate_flag]
        post_touch_targets = valid_orders[:self.config.post_conversion_touches_count]
        for v_order in post_touch_targets:
            touch_seq_counters[v_order.contact_id] += 1
            t_seq = touch_seq_counters[v_order.contact_id]
            post_conv_touch_id = f"TOUCH-{v_order.contact_id}-{t_seq:06d}"
            post_time = v_order.order_date + timedelta(days=self.rng.randint(2, 30))

            post_touch = Touchpoint(
                touchpoint_id=post_conv_touch_id,
                contact_id=v_order.contact_id,
                campaign_id=campaigns[self.rng.randint(0, len(campaigns) - 1)].campaign_id,
                channel_id=channels[self.rng.randint(0, len(channels) - 1)].channel_id,
                creative_id=creatives[self.rng.randint(0, len(creatives) - 1)].creative_id,
                session_id=None,
                touch_type="CLICK",
                channel_medium="ONLINE",
                occurred_at=post_time,
                interaction_cost=2.50,
                created_at=post_time
            )
            touchpoints.append(post_touch)

            self.gt_tracker.record(
                case_id=f"GT-ANO2-{post_conv_touch_id}",
                entity_type="TOUCHPOINT",
                entity_id=post_conv_touch_id,
                anomaly_type="POST_CONVERSION_TOUCHPOINT",
                expected_decision="EXCLUDE_FROM_ATTRIBUTION",
                severity="HIGH",
                description=f"Touchpoint {post_conv_touch_id} occurred at {post_time.isoformat()} which is strictly after conversion at {v_order.order_date.isoformat()}.",
                related_ids=f"{v_order.order_id},{v_order.opportunity_id}"
            )

        # Anomaly 4: Missing Campaign Costs (Select specific campaigns and remove all their costs)
        missing_cost_camp_ids: Set[str] = set()
        if self.config.missing_cost_campaigns_count > 0:
            for cmp in campaigns[:self.config.missing_cost_campaigns_count]:
                missing_cost_camp_ids.add(cmp.campaign_id)
                self.gt_tracker.record(
                    case_id=f"GT-ANO4-{cmp.campaign_id}",
                    entity_type="CAMPAIGN",
                    entity_id=cmp.campaign_id,
                    anomaly_type="MISSING_CAMPAIGN_COST",
                    expected_decision="FLAG_MISSING_COST_MARK_ROI_UNAVAILABLE",
                    severity="HIGH",
                    description=f"Campaign {cmp.campaign_id} has marketing activity but zero recorded costs.",
                    related_ids=cmp.campaign_id
                )

        # Filter out cost records belonging to missing cost campaigns
        costs = [c for c in costs if c.campaign_id not in missing_cost_camp_ids]

        # Anomaly 3: Spend Currency Mismatch (Incompatible currencies vs base INR)
        # Select cost records from campaigns that retain their costs
        eligible_costs = [c for c in costs if c.cost_type == "MEDIA_SPEND"]
        mismatch_targets = eligible_costs[:self.config.currency_mismatch_count]
        for m_idx, cst in enumerate(mismatch_targets):
            cst.currency = "USD" if m_idx % 2 == 0 else "EUR"
            self.gt_tracker.record(
                case_id=f"GT-ANO3-{cst.cost_id}",
                entity_type="COST_RECORD",
                entity_id=cst.cost_id,
                anomaly_type="CURRENCY_MISMATCH",
                expected_decision="FLAG_CURRENCY_MISMATCH_EXCLUDE_FROM_ROI",
                severity="MEDIUM",
                description=f"Cost record {cst.cost_id} has currency '{cst.currency}' which differs from base currency '{BASE_CURRENCY}'.",
                related_ids=cst.campaign_id
            )

        # Anomaly 5: Unsupported Identity Links (Anonymous session linked without evidence in contact_identities)
        eligible_sessions = [s for s in sessions if s.contact_id != "CON-2026-000001"]
        unsupported_sessions = eligible_sessions[:self.config.unsupported_identity_links_count]
        unsupported_cookies_to_remove = set()

        for s in unsupported_sessions:
            unsupported_cookies_to_remove.add(s.anonymous_cookie_id)
            self.gt_tracker.record(
                case_id=f"GT-ANO5-{s.session_id}",
                entity_type="WEB_SESSION",
                entity_id=s.session_id,
                anomaly_type="UNSUPPORTED_IDENTITY_LINK",
                expected_decision="QUARANTINE_IDENTITY_LINK",
                severity="MEDIUM",
                description=f"Session {s.session_id} linked to contact {s.contact_id} without any supporting identity evidence in contact_identities.",
                related_ids=s.contact_id
            )

        # Remove matching cookie identity evidence from identities list
        identities = [
            idn for idn in identities
            if not (idn.identity_type == "COOKIE" and idn.identity_value in unsupported_cookies_to_remove)
        ]

        # =====================================================================
        # CHUNKED BULK PERSISTENCE
        # =====================================================================
        print(f"Persisting {len(costs)} cost records...")
        self._bulk_save_chunked(costs)

        print(f"Persisting {len(identities)} contact identity records...")
        self._bulk_save_chunked(identities)

        print(f"Persisting {len(sessions)} web sessions...")
        self._bulk_save_chunked(sessions)

        print(f"Persisting {len(touchpoints)} touchpoints...")
        self._bulk_save_chunked(touchpoints)

        print(f"Persisting {len(leads)} leads...")
        self._bulk_save_chunked(leads)

        print(f"Persisting {len(opportunities)} opportunities...")
        self._bulk_save_chunked(opportunities)

        print(f"Persisting {len(orders)} orders...")
        self._bulk_save_chunked(orders)

        # Update lifecycle_stage for converted contacts
        converted_contact_ids = {o.contact_id for o in orders if not o.is_duplicate_flag}
        if converted_contact_ids:
            self.db.query(Contact).filter(Contact.contact_id.in_(converted_contact_ids)).update(
                {"lifecycle_stage": "CUSTOMER"}, synchronize_session=False
            )
            self.db.commit()

        return sessions, touchpoints, leads, opportunities, orders, costs
