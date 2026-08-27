import { createHash } from "node:crypto";
import { classifyDemand, geminiReady } from "../../../lib/gemini";
import {
  addTicket,
  assignClusterId,
  districtForPoint,
  newTicketId,
} from "../../../lib/store";
import type { Lang, TenantId } from "../../../../../packages/schema/src";

export const dynamic = "force-dynamic";
export const maxDuration = 60;

type Body = {
  tenant_id?: TenantId;
  lat?: number;
  lng?: number;
  text?: string;
  lang?: Lang;
  photo?: { mimeType: string; base64: string };
};

export async function POST(req: Request) {
  const body = (await req.json()) as Body;
  const lat = Number(body.lat);
  const lng = Number(body.lng);
  if (!Number.isFinite(lat) || !Number.isFinite(lng)) {
    return Response.json({ error: "lat and lng are required" }, { status: 400 });
  }
  if (!geminiReady()) {
    return Response.json(
      {
        error:
          "GEMINI_API_KEY is not set. Classify cannot run. This is not a stub.",
      },
      { status: 503 },
    );
  }

  const tenant_id: TenantId = body.tenant_id === "rajasthan_pwd" ? "rajasthan_pwd" : "delhi_pwd";
  const text = (body.text || "").slice(0, 2000);
  const photo = body.photo;
  const photo_sha256 = photo?.base64
    ? createHash("sha256").update(photo.base64).digest("hex")
    : undefined;

  const classification = await classifyDemand({
    text,
    mimeType: photo?.mimeType,
    imageBase64: photo?.base64,
  });

  const id = newTicketId();
  const ticket = {
    id,
    tenant_id,
    lat,
    lng,
    text,
    lang: body.lang || classification.lang,
    channel: "web" as const,
    media_type: (photo ? "photo" : "text") as "photo" | "text",
    photo_sha256,
    classification,
    cluster_id: "pending",
    source: "LIVE_WEB" as const,
    district: districtForPoint(tenant_id, lat, lng),
    created_at: new Date().toISOString(),
    status: "open" as const,
  };
  ticket.cluster_id = assignClusterId(ticket);
  addTicket(ticket);

  return Response.json({
    ticket_id: ticket.id,
    cluster_id: ticket.cluster_id,
    classification: ticket.classification,
    district: ticket.district,
    sla_hours: tenant_id === "delhi_pwd" ? 72 : 96,
    banner: "Filed on NirmanGrid. SAMPLE events already sit on this map. This live web ticket is not a PWD Sewa complaint.",
  });
}
