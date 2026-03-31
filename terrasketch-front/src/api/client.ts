const API_BASE = 'http://localhost:8000/api';

function getToken(): string | null {
  return localStorage.getItem('access_token') || sessionStorage.getItem('admin_token');
}

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  };
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || err.error || `HTTP ${res.status}`);
  }
  return res.json();
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body: unknown) =>
    request<T>(path, { method: 'POST', body: JSON.stringify(body) }),
  patch: <T>(path: string, body: unknown) =>
    request<T>(path, { method: 'PATCH', body: JSON.stringify(body) }),
  delete: <T>(path: string) => request<T>(path, { method: 'DELETE' }),

  /** Auth helpers */
  login: (email: string, password: string) =>
    request<{ access: string; refresh: string; user: AppUser }>('/auth/login/', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    }),
};

export interface AppUser {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  role: string;
  is_verified: boolean;
  created_at: string;
}

export interface Project {
  id: string;
  name: string;
  status: string;
  budget_tier: string | null;
  address: string;
  city: string;
  created_at: string;
  updated_at: string;
}

export interface DashboardStats {
  total_projects: number;
  projects_by_status: Record<string, number>;
  recent_activity: unknown[];
}

export interface GenerationJob {
  job_id: string;
  status: string;
  progress_pct: number;
  current_step: string | null;
}

export interface AIPlan {
  id: string;
  version: number;
  plan_json: unknown;
  generated_at: string;
  ai_model: string;
  input_tokens: number;
  output_tokens: number;
}
