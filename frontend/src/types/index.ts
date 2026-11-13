export interface DashboardSummary {
  currency: string;
  total_campaigns: number;
  total_leads: number;
  total_opportunities: number;
  total_conversions: number;
  total_budget: number;
  total_campaign_spend: number;
  total_closed_revenue: number;
  attributed_revenue_multi_touch: number;
  unattributed_revenue: number;
  excluded_duplicate_revenue: number;
  excluded_duplicate_orders_count: number;
  currency_mismatch_count?: number;
  excluded_foreign_spend?: number;
  quarantined_currencies?: string[];
  is_reconciled?: boolean;
  overall_roi: number | null;
  cost_per_lead: number;
  cost_per_acquisition: number;
  revenue_by_model: Record<string, number>;
}

export interface TrendDataPoint {
  period: string;
  spend: number;
  revenue: number;
  conversions: number;
}

export interface CampaignItem {
  campaign_id: string;
  campaign_name: string;
  channel_id: string;
  status: string;
  status_display?: string;
  is_incomplete?: boolean;
  budget: number;
  actual_spend: number;
  attributed_revenue: number;
  leads: number;
  opportunities: number;
  conversions: number;
  roi: number | null;
  roi_status: string;
  cost_per_lead: number | null;
  cost_per_acquisition: number | null;
  start_date: string;
  end_date: string | null;
}

export interface CampaignDetail extends CampaignItem {
  name?: string;
  channel_name: string;
  touchpoints_count: number;
  leads_count: number;
  opportunities_count: number;
  conversions_count: number;
  creatives: Array<{ creative_id: string; name: string; format: string }>;
  audiences: Array<{ audience_id: string; name: string; segment: string }>;
}

export interface ContactItem {
  contact_id: string;
  name: string;
  email: string;
  lifecycle_stage: string;
  first_seen_at: string;
}

export interface JourneyEvent {
  event_id: string;
  event_type: 'TOUCHPOINT' | 'SESSION' | 'LEAD' | 'OPPORTUNITY' | 'ORDER';
  timestamp: string;
  title: string;
  description: string;
  channel?: string;
  campaign_id?: string;
  amount?: number;
  status?: string;
  is_anomaly?: boolean;
}

export interface CustomerJourney {
  contact_id: string;
  contact_name: string;
  email: string;
  lifecycle_stage: string;
  first_seen_at: string;
  total_events: number;
  events: JourneyEvent[];
}

export interface AttributionCompareItem {
  campaign_id: string;
  campaign_name: string;
  channel_name: string;
  spend: number;
  first_touch_revenue: number;
  last_touch_revenue: number;
  multi_touch_revenue: number;
  first_touch_roi: number | null;
  last_touch_roi: number | null;
  multi_touch_roi: number | null;
}

export interface AttributionCompareResponse {
  campaigns: AttributionCompareItem[];
  total_eligible_revenue: number;
  total_first_touch_revenue: number;
  total_last_touch_revenue: number;
  total_multi_touch_revenue: number;
  is_fully_reconciled: boolean;
}

export interface AnomalyIssueItem {
  issue_id: string;
  entity_type: string;
  entity_id: string;
  issue_type: string;
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  description: string;
  detection_timestamp: string;
  expected_decision: string;
  actual_decision: string;
  resolution_status: string;
  related_record_ids?: string;
}

export interface AnomalyDashboardData {
  total_anomalies: number;
  by_type: Record<string, number>;
  by_severity: Record<string, number>;
  evaluation_metrics: {
    evaluation_status: string;
    overall_metrics: {
      total_ground_truth: number;
      total_detected: number;
      true_positives: number;
      false_positives: number;
      false_negatives: number;
      precision: number;
      recall: number;
      f1_score: number;
    };
    by_anomaly_type: Record<string, {
      ground_truth_count: number;
      detected_count: number;
      true_positives: number;
      false_positives: number;
      false_negatives: number;
      precision: number;
      recall: number;
      f1_score: number;
    }>;
  };
  issues: AnomalyIssueItem[];
}

export interface ValidationReport {
  validation_timestamp: string;
  summary: {
    total_rules: number;
    rules_passed: number;
    rules_warned: number;
    rules_failed: number;
    total_records_checked: number;
    total_records_passed: number;
    total_records_failed: number;
  };
  rule_results: Array<{
    rule_code: string;
    rule_name: string;
    status: 'PASS' | 'WARN' | 'FAIL';
    records_checked: number;
    records_passed: number;
    records_failed: number;
    details: string[];
  }>;
}

export interface GeneratorStatus {
  last_run_id: string | null;
  config_name: string | null;
  seed: number | null;
  status: string;
  row_counts: Record<string, number>;
  completed_at: string | null;
}

export interface ChronologicalPeriodItem {
  period_code: string;
  name: string;
  start_date: string;
  end_date: string;
  duration_days: number;
  purpose: string;
  orders_count: number;
  order_revenue: number;
  attributed_revenue_multi_touch: number;
  touchpoints_count: number;
  campaign_spend: number;
  anomalies_detected: number;
}

export interface ChronologicalPeriodsResponse {
  status: string;
  total_periods: number;
  boundaries_summary: string;
  periods: ChronologicalPeriodItem[];
}

export type UserRole =
  | 'CUSTOMER_PROSPECT'
  | 'MARKETING_SALES_OPS'
  | 'SUPPORT_AGENT'
  | 'ANALYST'
  | 'SYSTEM_ADMIN';

export interface ActorProfile {
  user_id: string;
  name: string;
  email: string;
  role: UserRole;
  role_name: string;
  title: string;
  contact_id: string | null;
  avatar_badge: string;
  description: string;
  permissions: string[];
  allowed_pages: string[];
}
