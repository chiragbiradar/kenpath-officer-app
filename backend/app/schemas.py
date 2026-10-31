from typing import Literal

from pydantic import BaseModel


# ── Auth ─────────────────────────────────────────────────────────────────────
class LoginRequest(BaseModel):
    email: str
    password: str


class OfficerOut(BaseModel):
    id: str
    email: str
    name: str
    name_kn: str
    psk_district: str


class LoginResponse(BaseModel):
    token: str
    officer: OfficerOut


# ── Rules ─────────────────────────────────────────────────────────────────────
class RuleCheck(BaseModel):
    code: str
    status: Literal["pass", "fail", "review"]
    message_kn: str
    message_en: str
    evidence: str = ""


# ── AI ────────────────────────────────────────────────────────────────────────
class Inconsistency(BaseModel):
    field: str
    detail_kn: str
    detail_en: str
    severity: Literal["high", "medium", "low"]


class Reason(BaseModel):
    text_kn: str
    text_en: str
    rule_code: str | None = None


class AiAnalysisResult(BaseModel):
    summary_kn: str
    summary_en: str
    inconsistencies: list[Inconsistency]
    suggested_decision: Literal["accept", "return", "reject"]
    reasons: list[Reason]
    draft_remark_kn: str
    confidence: Literal["high", "medium", "low"]


class AiAnalysisResponse(BaseModel):
    available: bool
    result: AiAnalysisResult | None = None
    cached: bool = False
    model: str = ""
    latency_ms: int = 0


# ── Applications ──────────────────────────────────────────────────────────────
class ApplicationFlags(BaseModel):
    missing_docs: int
    fails: int
    reviews: int


class ApplicationRow(BaseModel):
    id: str
    app_no: str
    applicant_name: str
    applicant_name_kn: str
    application_type: str
    days_pending: int
    deadline_status: Literal["overdue", "due_soon", "on_track"]
    priority: int
    flags: ApplicationFlags
    status: str


class Pagination(BaseModel):
    page: int
    limit: int
    total: int


class ApplicationListResponse(BaseModel):
    data: list[ApplicationRow]
    pagination: Pagination


class DocumentField(BaseModel):
    name: str | None = None
    dob: str | None = None
    address_district: str | None = None
    address_state: str | None = None
    expiry_date: str | None = None
    appointment_id: str | None = None
    appointment_date: str | None = None


class Document(BaseModel):
    type: str
    present: bool
    fields: DocumentField = DocumentField()


class AuditEventOut(BaseModel):
    event: str
    detail: dict
    created_at: str
    officer_id: str | None = None


class ApplicationDetail(BaseModel):
    id: str
    app_no: str
    applicant_name: str
    applicant_name_kn: str
    gender: str
    dob: str
    phone_masked: str
    aadhaar_masked: str
    application_type: str
    documents: list[Document]
    status: str
    received_at: str
    appointment_date: str
    deadline_at: str
    days_pending: int
    deadline_status: Literal["overdue", "due_soon", "on_track"]
    rule_checks: list[RuleCheck]
    ai_analysis: AiAnalysisResponse | None = None
    audit: list[AuditEventOut]


# ── Stats ─────────────────────────────────────────────────────────────────────
class StatsResponse(BaseModel):
    pending: int
    due_soon: int
    overdue: int
    decided_today: int


# ── Decision ──────────────────────────────────────────────────────────────────
class DecisionRequest(BaseModel):
    action: Literal["accept", "return", "reject"]
    remark: str | None = None
