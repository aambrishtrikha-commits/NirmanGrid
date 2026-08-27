from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

TenantId = Literal["delhi_pwd", "rajasthan_pwd"]
DemandType = Literal[
    "pothole",
    "streetlight",
    "waterlogging",
    "footpath",
    "culvert",
    "drainage",
    "other",
]
Severity = Literal["low", "medium", "high"]
Lang = Literal["hi", "en", "raj"]
Channel = Literal["web", "whatsapp"]
MediaType = Literal["photo", "voice", "text"]
EventSource = Literal["SAMPLE", "LIVE_WEB"]
TicketStatus = Literal["open", "elevated", "resolved"]
ScoreMode = Literal["full", "partial"]


class Classification(BaseModel):
    type: DemandType
    severity: Severity
    lang: Lang
    summary: str
    reason: str
    confidence: float = Field(ge=0, le=1)
    mplads_eligible: bool = False


class Ticket(BaseModel):
    id: str
    tenant_id: TenantId
    lat: float
    lng: float
    text: str
    lang: Lang
    channel: Channel = "web"
    media_type: MediaType = "photo"
    photo_sha256: str | None = None
    classification: Classification
    cluster_id: str
    source: EventSource
    district: str
    created_at: str
    status: TicketStatus = "open"
    ministry_note: str | None = None


class ScoreComponent(BaseModel):
    key: str
    name: str
    weight: float
    value: float | None
    used: bool
    note: str


class ScoreBreakdown(BaseModel):
    mode: ScoreMode
    priority_score: float
    components: list[ScoreComponent]
    vintage_notes: list[str]


class Cluster(BaseModel):
    id: str
    tenant_id: TenantId
    type: DemandType
    lat: float
    lng: float
    district: str
    reporter_count: int
    tickets: list[Ticket]
    score: ScoreBreakdown
    status: TicketStatus


class PhotoIn(BaseModel):
    mimeType: str
    base64: str


class IngestIn(BaseModel):
    tenant_id: TenantId = "delhi_pwd"
    lat: float
    lng: float
    text: str = ""
    lang: Lang | None = None
    photo: PhotoIn | None = None


class ElevateIn(BaseModel):
    cluster_id: str
