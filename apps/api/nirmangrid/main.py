from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from . import store
from .gemini import classify_demand, gemini_ready, transcribe_voice, write_ministry_note
from .schemas import ElevateIn, IngestIn, TenantId, Ticket
from .snap import layers_loaded, snap_to_highway
from .tenants import TENANTS, district_for_point

app = FastAPI(title="NirmanGrid API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(HTTPException)
async def http_error(_request: Request, exc: HTTPException):
    return JSONResponse({"error": exc.detail}, status_code=exc.status_code)


@app.get("/api/health")
def health():
    tickets = store.all_tickets()
    sample = [t for t in tickets if t.source == "SAMPLE"]
    return {
        "ok": True,
        "service": "nirmangrid-api",
        "engine": "python",
        "gemini": gemini_ready(),
        "sample_events": len(sample),
        "sample_delhi": sum(1 for t in sample if t.tenant_id == "delhi_pwd"),
        "sample_rajasthan": sum(1 for t in sample if t.tenant_id == "rajasthan_pwd"),
        "live_events": sum(1 for t in tickets if t.source == "LIVE_WEB"),
        "layers": layers_loaded(),
        "highways_loaded": any(layers_loaded().values()),
    }


@app.get("/api/tickets")
def tickets(tenant: Optional[TenantId] = None):
    rows = store.all_tickets(tenant)
    payload = []
    for t in rows:
        d = t.model_dump()
        if d.get("photo_sha256"):
            d["photo_sha256"] = "redacted"
        payload.append(d)
    return {"tickets": payload, "sample_banner": True}


@app.get("/api/clusters")
def clusters(tenant: Optional[TenantId] = None, id: Optional[str] = None):
    if id:
        cluster = store.get_cluster(id)
        if not cluster:
            raise HTTPException(404, "not found")
        return {"cluster": cluster.model_dump()}
    return {"clusters": [c.model_dump() for c in store.all_clusters(tenant)]}


@app.post("/api/ingest")
async def ingest(body: IngestIn):
    if not gemini_ready():
        raise HTTPException(
            status_code=503,
            detail="GEMINI_API_KEY is not set. Classify cannot run. This is not a stub.",
        )
    photo = body.photo
    audio = body.audio
    photo_sha = hashlib.sha256(photo.base64.encode("utf-8")).hexdigest() if photo else None
    text = body.text[:2000]
    transcript = None
    if audio:
        transcript = transcribe_voice(audio.base64, audio.mimeType)
        spoken = transcript.get("transcript") or ""
        text = spoken if not text else f"{text}\n{spoken}".strip()
    classification = classify_demand(
        text,
        photo.mimeType if photo else None,
        photo.base64 if photo else None,
        audio.mimeType if audio else None,
        audio.base64 if audio else None,
    )
    snapped = snap_to_highway(body.lat, body.lng, body.tenant_id)
    lat = snapped["lat"] if snapped else body.lat
    lng = snapped["lng"] if snapped else body.lng
    media: str = "text"
    if photo and audio:
        media = "photo"
    elif audio:
        media = "voice"
    elif photo:
        media = "photo"
    pending = Ticket(
        id=store.new_ticket_id(),
        tenant_id=body.tenant_id,
        lat=lat,
        lng=lng,
        text=text,
        lang=body.lang or classification.lang,
        channel="web",
        media_type=media,  # type: ignore[arg-type]
        photo_sha256=photo_sha,
        classification=classification,
        cluster_id="pending",
        source="LIVE_WEB",
        district=district_for_point(body.tenant_id, lat, lng),
        created_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        status="open",
    )
    pending.cluster_id = store.assign_cluster_id(pending)
    store.add_ticket(pending)
    return {
        "ticket_id": pending.id,
        "cluster_id": pending.cluster_id,
        "classification": pending.classification.model_dump(),
        "district": pending.district,
        "snap": snapped,
        "transcript": transcript,
        "sla_hours": TENANTS[body.tenant_id]["sla_hours"],
        "banner": "Filed on NirmanGrid. SAMPLE events already sit on this map. This live web ticket is not a PWD Sewa complaint.",
    }


@app.post("/api/elevate")
async def elevate(body: ElevateIn):
    cluster = store.get_cluster(body.cluster_id)
    if not cluster:
        raise HTTPException(404, "not found")
    if not gemini_ready():
        raise HTTPException(503, "GEMINI_API_KEY is not set. Ministry note cannot be written.")
    note = write_ministry_note(cluster)
    updated = store.elevate_cluster(body.cluster_id, note)
    return {
        "cluster": updated.model_dump() if updated else None,
        "ministry_note": note,
        "citizen_update": "Demand elevated to planning shelf — not merely registered.",
    }
