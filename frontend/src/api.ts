const BASE = '/api'

function getToken() {
  return localStorage.getItem('token') || ''
}

function authHeaders() {
  return { 'Content-Type': 'application/json', Authorization: `Bearer ${getToken()}` }
}

async function req<T>(path: string, opts: RequestInit = {}): Promise<T> {
  const res = await fetch(`${BASE}${path}`, { headers: authHeaders(), ...opts })
  if (res.status === 401) {
    localStorage.removeItem('token')
    window.location.href = '/login'
    throw new Error('Unauthorized')
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || 'Request failed')
  }
  return res.json()
}

export const api = {
  login: (email: string, password: string) =>
    req<{ token: string; officer: Officer }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    }),

  me: () => req<Officer>('/me'),

  stats: () => req<Stats>('/stats'),

  applications: (params: Record<string, string>) => {
    const qs = new URLSearchParams(params).toString()
    return req<ApplicationListResponse>(`/applications?${qs}`)
  },

  application: (id: string) => req<ApplicationDetail>(`/applications/${id}`),

  analyse: (id: string, force = false) =>
    req<AiAnalysisResponse>(`/applications/${id}/analyse?force=${force}`, { method: 'POST' }),

  decide: (id: string, action: string, remark?: string) =>
    req<{ status: string }>(`/applications/${id}/decision`, {
      method: 'POST',
      body: JSON.stringify({ action, remark }),
    }),
}

// Types
export interface Officer {
  id: string
  email: string
  name: string
  name_kn: string
  psk_district: string
}

export interface Stats {
  pending: number
  due_soon: number
  overdue: number
  decided_today: number
}

export interface ApplicationRow {
  id: string
  app_no: string
  applicant_name: string
  applicant_name_kn: string
  application_type: string
  days_pending: number
  deadline_status: 'overdue' | 'due_soon' | 'on_track'
  priority: number
  flags: { missing_docs: number; fails: number; reviews: number }
  status: string
}

export interface ApplicationListResponse {
  data: ApplicationRow[]
  pagination: { page: number; limit: number; total: number }
}

export interface Document {
  type: string
  present: boolean
  fields: Record<string, string>
}

export interface RuleCheck {
  code: string
  status: 'pass' | 'fail' | 'review'
  message_kn: string
  message_en: string
  evidence: string
}

export interface AiAnalysisResult {
  summary_kn: string
  summary_en: string
  inconsistencies: Array<{ field: string; detail_kn: string; detail_en: string; severity: string }>
  suggested_decision: 'accept' | 'return' | 'reject'
  reasons: Array<{ text_kn: string; text_en: string; rule_code: string | null }>
  draft_remark_kn: string
  confidence: 'high' | 'medium' | 'low'
}

export interface AiAnalysisResponse {
  available: boolean
  result?: AiAnalysisResult
  cached: boolean
  model: string
  latency_ms: number
}

export interface AuditEvent {
  event: string
  detail: Record<string, unknown>
  created_at: string
  officer_id: string | null
}

export interface ApplicationDetail {
  id: string
  app_no: string
  applicant_name: string
  applicant_name_kn: string
  gender: string
  dob: string
  phone_masked: string
  aadhaar_masked: string
  application_type: string
  documents: Document[]
  status: string
  received_at: string
  appointment_date: string
  deadline_at: string
  days_pending: number
  deadline_status: 'overdue' | 'due_soon' | 'on_track'
  rule_checks: RuleCheck[]
  ai_analysis: AiAnalysisResponse | null
  audit: AuditEvent[]
}
