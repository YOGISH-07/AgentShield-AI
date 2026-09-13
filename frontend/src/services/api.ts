export const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL as string) || 'http://localhost:8000';

export interface HealthResponse {
  status: string;
  service: string;
  human_verification_required: boolean;
}

export interface OperationalStats {
  active_alerts: number;
  total_alerts: number;
  confirmed_incidents: number;
  dismissed_alerts: number;
  false_alarm_rate: number;
}

export interface AlertItem {
  id: number;
  alert_id: string;
  camera_id: string;
  timestamp_seconds: number;
  person_track_id: number;
  phone_track_id: number;
  risk_score: number;
  classification: string;
  reasons: string[];
  status: 'NEW' | 'UNDER_REVIEW' | 'CONFIRMED' | 'DISMISSED';
  created_at: string;
  reviewed_at?: string;
  resolved_at?: string;
  human_verification_required: boolean;
}

export interface IncidentItem {
  id: number;
  incident_id: string;
  alert_id: string;
  camera_id: string;
  timestamp_seconds: number;
  risk_score_at_alert: number;
  reasons: string[];
  verification_status: string;
  reviewer_action: string;
  created_at: string;
  human_verification_required: boolean;
}

export async function fetchHealth(): Promise<HealthResponse> {
  const res = await fetch(`${API_BASE_URL}/api/health`);
  if (!res.ok) throw new Error('Health check failed');
  return res.json();
}

export async function fetchStats(): Promise<OperationalStats> {
  const res = await fetch(`${API_BASE_URL}/api/stats`);
  if (!res.ok) throw new Error('Failed to fetch stats');
  return res.json();
}

export async function fetchAlerts(statusFilter?: string): Promise<AlertItem[]> {
  const url = statusFilter
    ? `${API_BASE_URL}/api/alerts?status=${encodeURIComponent(statusFilter)}`
    : `${API_BASE_URL}/api/alerts`;
  const res = await fetch(url);
  if (!res.ok) throw new Error('Failed to fetch alerts');
  return res.json();
}

export async function fetchIncidents(): Promise<IncidentItem[]> {
  const res = await fetch(`${API_BASE_URL}/api/incidents`);
  if (!res.ok) throw new Error('Failed to fetch incidents');
  return res.json();
}

export async function reviewAlert(alertId: string): Promise<AlertItem> {
  const res = await fetch(`${API_BASE_URL}/api/alerts/${encodeURIComponent(alertId)}/review`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ reviewer_action: 'Security Review Started' }),
  });
  if (!res.ok) throw new Error('Failed to start alert review');
  return res.json();
}

export async function confirmAlert(alertId: string): Promise<AlertItem> {
  const res = await fetch(`${API_BASE_URL}/api/alerts/${encodeURIComponent(alertId)}/confirm`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ reviewer_action: 'Confirmed Staff Verification' }),
  });
  if (!res.ok) throw new Error('Failed to confirm alert incident');
  return res.json();
}

export async function dismissAlert(alertId: string): Promise<AlertItem> {
  const res = await fetch(`${API_BASE_URL}/api/alerts/${encodeURIComponent(alertId)}/dismiss`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ reviewer_action: 'Dismissed Non-Critical' }),
  });
  if (!res.ok) throw new Error('Failed to dismiss alert');
  return res.json();
}

export async function resetDemo(): Promise<{ status: string; message: string }> {
  const res = await fetch(`${API_BASE_URL}/api/demo/reset`, {
    method: 'POST',
  });
  if (!res.ok) throw new Error('Failed to reset demo data');
  return res.json();
}

export function getVideoUrl(): string {
  return `${API_BASE_URL}/api/video/risk`;
}
