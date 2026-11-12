"""Deterministic Synthetic Data Generator for Marketing Attribution Platform.
Strictly reproducible via fixed seed (20261022).
Implements master data, realistic multi-touch customer journeys, dependent entities,
and 5 mandatory labelled anomaly edge cases.
"""
import random
import hashlib
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple
from pathlib import Path

from sqlalchemy.orm import Session

from backend.app.generators.config import (
    RANDOM_SEED, BASE_CURRENCY, DatasetConfig, STARTER_CONFIG, FULL_CONFIG,
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

    def generate(self) -> Dict[str, Any]:
        """Execute full deterministic generation pipeline."""
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

        # Step 2: Master Data
        channels = self._generate_channels()
        audiences = self._generate_audiences()
        creatives = self._generate_creatives()
        campaigns = self._generate_campaigns(channels, audiences, creatives)
        contacts = self._generate_contacts()

        # Step 3: Dependent Journeys & Conversion Records
        sessions, touchpoints, leads, opportunities, orders, costs = self._generate_customer_journeys(
            contacts, campaigns, channels, creatives
        )

        # Step 4: Export Ground Truth
        export_dir = Path(__file__).resolve().parent.parent.parent.parent / "data" / "ground_truth"
        gt_metadata = self.gt_tracker.export(export_dir)

        # Step 5: Calculate Summary Counts & Checksums
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

        # Compute deterministic checksum across generated counts & configuration
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

        print(f"Data generation [{self.config.name}] completed successfully in {(datetime.utcnow() - start_time).total_seconds():.2f}s.")
        return {
            "run_id": self.run_id,
            "status": "COMPLETED",
            "seed": self.seed,
            "config": self.config.name,
            "row_counts": row_counts,
            "checksum": data_checksum,
            "ground_truth": gt_metadata
        }

    def _create_attribution_models(self):
        """Seed core attribution model configurations if not present."""
        models = [
            AttributionModel(
                model_id="MDL-FIRST-TOUCH",
                model_code="FIRST_TOUCH",
                name="First-Touch Attribution",
                description="Attributes 100% credit to the first eligible marketing touchpoint within lookback window.",
                lookback_window_days=90,
                version="1.0.0",
                is_active=True
            ),
            AttributionModel(
                model_id="MDL-LAST-TOUCH",
                model_code="LAST_TOUCH",
                name="Last-Touch Attribution",
                description="Attributes 100% credit to the last eligible marketing touchpoint before conversion.",
                lookback_window_days=90,
                version="1.0.0",
                is_active=True
            ),
            AttributionModel(
                model_id="MDL-MULTI-TOUCH",
                model_code="MULTI_TOUCH_LINEAR",
                name="Multi-Touch Attribution (Linear / Equal-Weight)",
                description="Attributes equal credit (1/N) across all N eligible marketing touchpoints.",
                lookback_window_days=90,
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
        """Generate static marketing channels."""
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
                asset_url=f"https://assets.yottaflex.ai/creatives/{c_id}.png",
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

            # Bridge table links
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

        self.db.bulk_save_objects(campaigns)
        self.db.bulk_save_objects(campaign_channels)
        self.db.bulk_save_objects(campaign_audiences)
        self.db.bulk_save_objects(campaign_creatives)
        self.db.commit()
        return campaigns

    def _generate_contacts(self) -> List[Contact]:
        """Generate deterministic contact records."""
        contacts = []
        first_names = [
            "James", "Mary", "Robert", "Patricia", "John", "Jennifer", "Michael", "Linda",
            "William", "Elizabeth", "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica",
            "Thomas", "Sarah", "Charles", "Karen", "Christopher", "Nancy", "Daniel", "Lisa",
            "Matthew", "Betty", "Anthony", "Margaret", "Mark", "Sandra", "Donald", "Ashley",
            "Steven", "Kimberly", "Paul", "Emily", "Andrew", "Donna", "Joshua", "Michelle"
        ]
        last_names = [
            "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
            "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
            "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson",
            "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Walker"
        ]

        total_days = (TEST_END - PERIOD_START).days

        for i in range(1, self.config.num_contacts + 1):
            cid = f"CON-2026-{i:06d}"
            fn = first_names[i % len(first_names)]
            ln = last_names[(i // len(first_names)) % len(last_names)]
            email = f"user.{i:06d}.{fn.lower()}.{ln.lower()}@corpmail{i % 20}.com"
            phone = f"+1-555-{100 + (i % 900):03d}-{i % 10000:04d}"

            # First seen timestamp
            offset = self.rng.randint(0, total_days)
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

        # Bulk save
        self.db.bulk_save_objects(contacts)
        self.db.commit()
        return contacts

    def _generate_customer_journeys(
        self,
        contacts: List[Contact],
        campaigns: List[Campaign],
        channels: List[Channel],
        creatives: List[Creative]
    ) -> Tuple[List[WebSession], List[Touchpoint], List[Lead], List[Opportunity], List[Order], List[CostRecord]]:
        """Generate realistic journey events, conversions, costs, and inject anomalies."""
        sessions: List[WebSession] = []
        touchpoints: List[Touchpoint] = []
        leads: List[Lead] = []
        opportunities: List[Opportunity] = []
        orders: List[Order] = []
        costs: List[CostRecord] = []
        identities: List[ContactIdentity] = []

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

        # Step A: Generate Campaign Costs
        # Determine campaigns with omitted costs (Anomaly 4)
        missing_cost_camp_ids = set()
        if self.config.missing_cost_campaigns_count > 0:
            for c in campaigns[:self.config.missing_cost_campaigns_count]:
                missing_cost_camp_ids.add(c.campaign_id)
                self.gt_tracker.record(
                    case_id=f"GT-ANO4-{c.campaign_id}",
                    entity_type="CAMPAIGN",
                    entity_id=c.campaign_id,
                    anomaly_type="MISSING_CAMPAIGN_COST",
                    expected_decision="FLAG_MISSING_COST_MARK_ROI_UNAVAILABLE",
                    severity="HIGH",
                    description=f"Campaign {c.campaign_id} has marketing activity but zero recorded costs.",
                    related_ids=c.campaign_id
                )

        cost_id_counter = 1
        currency_mismatch_counter = 0

        for cmp in campaigns:
            if cmp.campaign_id in missing_cost_camp_ids:
                continue # Deliberately omit costs

            # Generate 3 to 12 cost records across campaign timeline
            num_costs = self.rng.randint(3, 8)
            time_span = max(1, (cmp.end_date - cmp.start_date).days)
            step_days = max(1, time_span // num_costs)
            spend_per_record = round(cmp.budget * self.rng.uniform(0.7, 1.1) / num_costs, 2)

            for ci in range(num_costs):
                cost_date = cmp.start_date + timedelta(days=ci * step_days)
                cost_curr = BASE_CURRENCY

                # Anomaly 3: Spend Currency Mismatch
                if (currency_mismatch_counter < self.config.currency_mismatch_count and 
                    ci == 0 and self.rng.random() < 0.2):
                    cost_curr = "EUR" if currency_mismatch_counter % 2 == 0 else "GBP"
                    cid_str = f"CST-2026-{cost_id_counter:06d}"
                    currency_mismatch_counter += 1
                    self.gt_tracker.record(
                        case_id=f"GT-ANO3-{cid_str}",
                        entity_type="COST_RECORD",
                        entity_id=cid_str,
                        anomaly_type="CURRENCY_MISMATCH",
                        expected_decision="FLAG_CURRENCY_MISMATCH_EXCLUDE_FROM_ROI",
                        severity="MEDIUM",
                        description=f"Cost record {cid_str} has currency '{cost_curr}' which differs from base currency '{BASE_CURRENCY}'.",
                        related_ids=cmp.campaign_id
                    )

                cst = CostRecord(
                    cost_id=f"CST-2026-{cost_id_counter:06d}",
                    campaign_id=cmp.campaign_id,
                    channel_id=cmp.channel_id,
                    recorded_date=cost_date,
                    amount=spend_per_record,
                    currency=cost_curr,
                    cost_type="MEDIA_SPEND" if ci % 2 == 0 else "AGENCY_FEE",
                    created_at=cost_date
                )
                costs.append(cst)
                cost_id_counter += 1

        # Step B: Generate Customer Journeys
        # Target: distribute touchpoints across contacts
        avg_touches_per_contact = max(1, self.config.num_touchpoints // self.config.num_contacts)
        touch_id_counters: Dict[str, int] = {}
        session_counter = 1
        lead_counter = 1
        opp_counter = 1
        order_counter = 1
        identity_counter = 1

        # Anomaly counters
        post_conversion_anomalies_created = 0
        duplicate_revenue_anomalies_created = 0
        unsupported_identity_anomalies_created = 0

        # Select a subset of contacts who convert
        num_converted_contacts = self.config.num_opportunities
        converting_contact_indices = set(self.rng.sample(range(len(contacts)), min(num_converted_contacts, len(contacts))))

        # Process each contact's journey
        for idx, contact in enumerate(contacts):
            is_converting = idx in converting_contact_indices
            num_touches = self.rng.randint(1, avg_touches_per_contact * 2 + 1)
            touch_id_counters[contact.contact_id] = 0

            # 1. Identity generation (Cookie, Email hash, Device)
            cookie_id = f"CK-{contact.contact_id[-6:]}-{self.rng.randint(1000, 9999)}"
            email_hash = hashlib.sha256(contact.email.encode("utf-8")).hexdigest()[:24]

            # Store identity evidence unless we want to inject Anomaly 5
            is_unsupported_identity_contact = False
            if (unsupported_identity_anomalies_created < self.config.unsupported_identity_links_count and 
                self.rng.random() < 0.15):
                is_unsupported_identity_contact = True # Omit identity record for this contact!

            if not is_unsupported_identity_contact:
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

            # 2. Web Sessions & Touchpoints
            current_time = contact.first_seen_at
            contact_touches = []

            for t_idx in range(num_touches):
                campaign = campaigns[self.rng.randint(0, len(campaigns) - 1)]
                channel = channel_map[campaign.channel_id]
                creative = creatives[self.rng.randint(0, len(creatives) - 1)]
                touch_def = touch_types.get(channel.channel_id, ("CLICK", "ONLINE", 1.0))

                # Session
                sess_id = f"SES-2026-{session_counter:06d}"
                session_start = current_time
                session_end = session_start + timedelta(minutes=self.rng.randint(2, 35))
                
                # Check for Anomaly 5: Anonymous Session Linked Without Evidence
                if is_unsupported_identity_contact:
                    unsupported_identity_anomalies_created += 1
                    self.gt_tracker.record(
                        case_id=f"GT-ANO5-{sess_id}",
                        entity_type="WEB_SESSION",
                        entity_id=sess_id,
                        anomaly_type="UNSUPPORTED_IDENTITY_LINK",
                        expected_decision="QUARANTINE_IDENTITY_LINK",
                        severity="MEDIUM",
                        description=f"Session {sess_id} linked to contact {contact.contact_id} without any supporting identity evidence in contact_identities.",
                        related_ids=contact.contact_id
                    )

                sess = WebSession(
                    session_id=sess_id,
                    contact_id=contact.contact_id,
                    anonymous_cookie_id=cookie_id,
                    started_at=session_start,
                    ended_at=session_end,
                    device_type="DESKTOP" if self.rng.random() < 0.6 else "MOBILE",
                    landing_page=f"/campaigns/{campaign.campaign_id}",
                    referrer=f"https://{channel.channel_id.lower().replace('chn-', '')}.com",
                    is_authenticated=True,
                    created_at=session_start
                )
                sessions.append(sess)
                session_counter += 1

                # Touchpoint
                touch_id_counters[contact.contact_id] += 1
                t_count = touch_id_counters[contact.contact_id]
                touch_id = f"TOUCH-{contact.contact_id}-{t_count:06d}"

                tp = Touchpoint(
                    touchpoint_id=touch_id,
                    contact_id=contact.contact_id,
                    campaign_id=campaign.campaign_id,
                    channel_id=channel.channel_id,
                    creative_id=creative.creative_id,
                    session_id=sess.session_id if touch_def[1] == "ONLINE" else None,
                    touch_type=touch_def[0],
                    channel_medium=touch_def[1],
                    occurred_at=session_start,
                    interaction_cost=touch_def[2],
                    created_at=session_start
                )
                touchpoints.append(tp)
                contact_touches.append(tp)

                # Move forward in time (realistic journey gap: 1 to 14 days)
                current_time += timedelta(days=self.rng.randint(1, 14), hours=self.rng.randint(1, 10))
                if current_time > TEST_END:
                    break

            # 3. Conversion events (Lead -> Opportunity -> Order)
            if is_converting and contact_touches:
                first_touch = contact_touches[0]
                last_touch = contact_touches[-1]
                
                # Lead creation
                lead_id = f"LEAD-2026-{lead_counter:06d}"
                lead_created = first_touch.occurred_at + timedelta(hours=self.rng.randint(2, 48))
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

                # Opportunity creation
                opp_id = f"OPP-2026-{opp_counter:06d}"
                opp_stage = "CLOSED_WON" if self.rng.random() < 0.8 else "CLOSED_LOST"
                opp_amount = round(self.rng.uniform(1500.0, 45000.0), 2)
                conversion_time = max(lead_created, last_touch.occurred_at) + timedelta(days=self.rng.randint(2, 20))
                
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

                # Order creation for CLOSED_WON
                if opp_stage == "CLOSED_WON":
                    contact.lifecycle_stage = "CUSTOMER"
                    ord_id = f"ORD-2026-{order_counter:06d}"
                    ord_num = f"YF-ORD-{order_counter:08d}"
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

                    # Check for Anomaly 1: Duplicate Revenue Counted More Than Once
                    if (duplicate_revenue_anomalies_created < self.config.duplicate_revenue_count and 
                        self.rng.random() < 0.25):
                        dup_ord_id = f"ORD-2026-{order_counter:06d}"
                        dup_order = Order(
                            order_id=dup_ord_id,
                            opportunity_id=opp.opportunity_id, # Duplicate reference to same opportunity!
                            contact_id=contact.contact_id,
                            order_number=ord_num, # Same order number!
                            order_date=conversion_time + timedelta(hours=1),
                            amount=opp_amount,
                            currency=BASE_CURRENCY,
                            status="COMPLETED",
                            is_duplicate_flag=True, # Ground truth flagged
                            created_at=conversion_time + timedelta(hours=1)
                        )
                        orders.append(dup_order)
                        order_counter += 1
                        duplicate_revenue_anomalies_created += 1

                        self.gt_tracker.record(
                            case_id=f"GT-ANO1-{dup_ord_id}",
                            entity_type="ORDER",
                            entity_id=dup_ord_id,
                            anomaly_type="DUPLICATE_REVENUE",
                            expected_decision="REJECT_DUPLICATE_REVENUE",
                            severity="CRITICAL",
                            description=f"Duplicate order {dup_ord_id} references existing order number {ord_num} and opportunity {opp.opportunity_id}.",
                            related_ids=f"{ord_id},{opp.opportunity_id}"
                        )

                    # Check for Anomaly 2: Touchpoint After Conversion
                    if (post_conversion_anomalies_created < self.config.post_conversion_touches_count and 
                        self.rng.random() < 0.35):
                        post_conv_touch_id = f"TOUCH-{contact.contact_id}-{touch_id_counters[contact.contact_id]+1:06d}"
                        touch_id_counters[contact.contact_id] += 1
                        post_time = conversion_time + timedelta(days=self.rng.randint(2, 30))
                        post_touch = Touchpoint(
                            touchpoint_id=post_conv_touch_id,
                            contact_id=contact.contact_id,
                            campaign_id=campaigns[self.rng.randint(0, len(campaigns)-1)].campaign_id,
                            channel_id=channels[self.rng.randint(0, len(channels)-1)].channel_id,
                            creative_id=creatives[self.rng.randint(0, len(creatives)-1)].creative_id,
                            session_id=None,
                            touch_type="CLICK",
                            channel_medium="ONLINE",
                            occurred_at=post_time, # After conversion!
                            interaction_cost=2.50,
                            created_at=post_time
                        )
                        touchpoints.append(post_touch)
                        post_conversion_anomalies_created += 1

                        self.gt_tracker.record(
                            case_id=f"GT-ANO2-{post_conv_touch_id}",
                            entity_type="TOUCHPOINT",
                            entity_id=post_conv_touch_id,
                            anomaly_type="POST_CONVERSION_TOUCHPOINT",
                            expected_decision="EXCLUDE_FROM_ATTRIBUTION",
                            severity="HIGH",
                            description=f"Touchpoint {post_conv_touch_id} occurred at {post_time.isoformat()} which is strictly after conversion at {conversion_time.isoformat()}.",
                            related_ids=f"{order.order_id},{opp.opportunity_id}"
                        )

        # Batch insert into database
        print(f"Persisting {len(costs)} cost records...")
        self.db.bulk_save_objects(costs)
        print(f"Persisting {len(identities)} contact identity records...")
        self.db.bulk_save_objects(identities)
        print(f"Persisting {len(sessions)} web sessions...")
        self.db.bulk_save_objects(sessions)
        print(f"Persisting {len(touchpoints)} touchpoints...")
        self.db.bulk_save_objects(touchpoints)
        print(f"Persisting {len(leads)} leads...")
        self.db.bulk_save_objects(leads)
        print(f"Persisting {len(opportunities)} opportunities...")
        self.db.bulk_save_objects(opportunities)
        print(f"Persisting {len(orders)} orders...")
        self.db.bulk_save_objects(orders)

        # Update converted contacts to CUSTOMER stage in database
        converted_contact_ids = {o.contact_id for o in orders if not o.is_duplicate_flag}
        if converted_contact_ids:
            self.db.query(Contact).filter(Contact.contact_id.in_(converted_contact_ids)).update(
                {"lifecycle_stage": "CUSTOMER"}, synchronize_session=False
            )

        self.db.commit()

        return sessions, touchpoints, leads, opportunities, orders, costs
