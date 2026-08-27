export type TenantId = "delhi_pwd" | "rajasthan_pwd";

export type DemandType =
  | "pothole"
  | "streetlight"
  | "waterlogging"
  | "footpath"
  | "culvert"
  | "drainage"
  | "other";

export type Severity = "low" | "medium" | "high";
export type Lang = "hi" | "en" | "raj";
export type Channel = "web" | "whatsapp";
export type MediaType = "photo" | "voice" | "text";
export type EventSource = "SAMPLE" | "LIVE_WEB";
export type TicketStatus = "open" | "elevated" | "resolved";
export type ScoreMode = "full" | "partial";

export type Classification = {
  type: DemandType;
  severity: Severity;
  lang: Lang;
  summary: string;
  reason: string;
  confidence: number;
  mplads_eligible: boolean;
};

export type Ticket = {
  id: string;
  tenant_id: TenantId;
  lat: number;
  lng: number;
  text: string;
  lang: Lang;
  channel: Channel;
  media_type: MediaType;
  photo_sha256?: string;
  classification: Classification;
  cluster_id: string;
  source: EventSource;
  district: string;
  created_at: string;
  status: TicketStatus;
  ministry_note?: string;
};

export type ScoreComponent = {
  key: string;
  name: string;
  weight: number;
  value: number | null;
  used: boolean;
  note: string;
};

export type ScoreBreakdown = {
  mode: ScoreMode;
  priority_score: number;
  components: ScoreComponent[];
  vintage_notes: string[];
};

export type Cluster = {
  id: string;
  tenant_id: TenantId;
  type: DemandType;
  lat: number;
  lng: number;
  district: string;
  reporter_count: number;
  tickets: Ticket[];
  score: ScoreBreakdown;
  status: TicketStatus;
};
