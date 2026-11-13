import {
  DashboardSummary,
  TrendDataPoint,
  CampaignItem,
  CampaignDetail,
  ContactItem,
  CustomerJourney,
  AttributionCompareItem,
  AttributionCompareResponse,
  AnomalyDashboardData,
  ValidationReport,
  GeneratorStatus,
  ActorProfile,
  UserRole,
  ChronologicalPeriodsResponse
} from '../types';

const API_BASE = '/api';

let activeUserRole: UserRole = (localStorage.getItem('agy_user_role') as UserRole) || 'SYSTEM_ADMIN';
let activeUserId: string = localStorage.getItem('agy_user_id') || 'USR-ADM-005';

export function getActiveRole(): UserRole {
  return activeUserRole;
}

export function setActiveRole(role: UserRole, userId?: string) {
  activeUserRole = role;
  localStorage.setItem('agy_user_role', role);
  if (userId) {
    activeUserId = userId;
    localStorage.setItem('agy_user_id', userId);
  }
}

export async function requestWithAuth(url: string, options: RequestInit = {}): Promise<Response> {
  const headers = new Headers(options.headers || {});
  headers.set('X-User-Role', activeUserRole);
  headers.set('X-User-Id', activeUserId);
  return fetch(url, { ...options, headers });
}

export async function fetchHealth(): Promise<{ status: string; database: string }> {
  const res = await requestWithAuth(`${API_BASE}/health`);
  if (!res.ok) throw new Error('Failed to fetch health status');
  return res.json();
}

export async function fetchAuthMe(): Promise<ActorProfile> {
  const res = await requestWithAuth(`${API_BASE}/auth/me`);
  if (!res.ok) throw new Error('Failed to fetch current user profile');
  return res.json();
}

export async function fetchAvailableActors(): Promise<ActorProfile[]> {
  const res = await requestWithAuth(`${API_BASE}/auth/actors`);
  if (!res.ok) throw new Error('Failed to fetch available actors');
  return res.json();
}

export async function fetchDashboardSummary(): Promise<DashboardSummary> {
  const res = await requestWithAuth(`${API_BASE}/dashboard/summary`);
  if (!res.ok) throw new Error('Failed to fetch dashboard summary');
  return res.json();
}

export async function fetchDashboardTrends(): Promise<TrendDataPoint[]> {
  const res = await requestWithAuth(`${API_BASE}/dashboard/trends`);
  if (!res.ok) throw new Error('Failed to fetch dashboard trends');
  const data = await res.json();
  return data.monthly_trends;
}

export async function fetchCampaigns(params: {
  channel_id?: string;
  status?: string;
  search?: string;
  sort_by?: string;
  sort_order?: string;
  page?: number;
  limit?: number;
}): Promise<{ total: number; page: number; limit: number; items: CampaignItem[] }> {
  const q = new URLSearchParams();
  if (params.channel_id) q.set('channel_id', params.channel_id);
  if (params.status) q.set('status', params.status);
  if (params.search) q.set('search', params.search);
  if (params.sort_by) q.set('sort_by', params.sort_by);
  if (params.sort_order) q.set('sort_order', params.sort_order);
  if (params.page) q.set('page', String(params.page));
  if (params.limit) q.set('limit', String(params.limit));

  const res = await requestWithAuth(`${API_BASE}/campaigns?${q.toString()}`);
  if (!res.ok) throw new Error('Failed to fetch campaigns');
  return res.json();
}

export async function fetchCampaignDetail(campaignId: string): Promise<CampaignDetail> {
  const res = await requestWithAuth(`${API_BASE}/campaigns/${campaignId}`);
  if (!res.ok) throw new Error(`Failed to fetch campaign ${campaignId}`);
  return res.json();
}

export async function fetchContacts(search?: string, stage?: string): Promise<ContactItem[]> {
  const q = new URLSearchParams();
  if (search) q.set('search', search);
  if (stage) q.set('lifecycle_stage', stage);
  const res = await requestWithAuth(`${API_BASE}/contacts?${q.toString()}`);
  if (!res.ok) throw new Error('Failed to fetch contacts');
  return res.json();
}

export async function fetchCustomerJourney(contactId: string): Promise<CustomerJourney> {
  const res = await requestWithAuth(`${API_BASE}/contacts/${contactId}/journey`);
  if (!res.ok) throw new Error(`Failed to fetch journey for contact ${contactId}`);
  return res.json();
}

export async function fetchAttributionComparison(evaluationPeriod?: string): Promise<AttributionCompareResponse> {
  const url = evaluationPeriod && evaluationPeriod !== 'ALL'
    ? `${API_BASE}/attribution/compare?evaluation_period=${evaluationPeriod}`
    : `${API_BASE}/attribution/compare`;
  const res = await requestWithAuth(url);
  if (!res.ok) throw new Error('Failed to fetch attribution comparison');
  return res.json();
}

export async function runAttributionRecalculation(lookbackDays: number = 90): Promise<any> {
  const res = await requestWithAuth(`${API_BASE}/attribution/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ lookback_days: lookbackDays })
  });
  if (!res.ok) throw new Error('Failed to recalculate attribution');
  return res.json();
}

export async function fetchChannelAnalytics(modelId: string = 'MDL-MULTI-TOUCH'): Promise<any[]> {
  const res = await requestWithAuth(`${API_BASE}/analytics/channels?model_id=${modelId}`);
  if (!res.ok) throw new Error('Failed to fetch channel analytics');
  const data = await res.json();
  return data.channels;
}

export async function fetchAnomalies(type?: string, severity?: string): Promise<AnomalyDashboardData> {
  const q = new URLSearchParams();
  if (type) q.set('issue_type', type);
  if (severity) q.set('severity', severity);
  const res = await requestWithAuth(`${API_BASE}/anomalies?${q.toString()}`);
  if (!res.ok) throw new Error('Failed to fetch anomalies');
  return res.json();
}

export async function fetchValidationReport(): Promise<ValidationReport> {
  const res = await requestWithAuth(`${API_BASE}/validation/report`);
  if (!res.ok) throw new Error('Failed to fetch validation report');
  return res.json();
}

export async function runValidation(): Promise<ValidationReport> {
  const res = await requestWithAuth(`${API_BASE}/validation/run`, { method: 'POST' });
  if (!res.ok) throw new Error('Failed to run validation');
  return res.json();
}

export async function fetchGeneratorStatus(): Promise<GeneratorStatus> {
  const res = await requestWithAuth(`${API_BASE}/generator/status`);
  if (!res.ok) throw new Error('Failed to fetch generator status');
  return res.json();
}

export async function runGenerator(configName: string = 'STARTER', seed: number = 20261022): Promise<any> {
  const res = await requestWithAuth(`${API_BASE}/generator/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ config_name: configName, seed })
  });
  if (!res.ok) throw new Error('Failed to run data generator');
  return res.json();
}

export async function fetchExportsManifest(): Promise<any> {
  const res = await requestWithAuth(`${API_BASE}/exports/list`);
  if (!res.ok) throw new Error('Failed to fetch exports manifest');
  return res.json();
}

export async function fetchChronologicalPeriods(): Promise<ChronologicalPeriodsResponse> {
  const res = await requestWithAuth(`${API_BASE}/evaluation/chronological-periods`);
  if (!res.ok) throw new Error('Failed to fetch chronological evaluation periods');
  return res.json();
}
