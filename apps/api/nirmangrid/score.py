"""Priority score. Gemini never computes this number."""

from __future__ import annotations

import math
from datetime import datetime, timezone

from .schemas import Cluster, DemandType, ScoreBreakdown, ScoreComponent, Ticket

WEIGHTS = {
    "repeat": 0.25,
    "population": 0.20,
    "vulnerability": 0.10,
    "gap": 0.20,
    "investment": 0.15,
    "seasonal": 0.10,
}

# Census 2011 PCA district totals. Vintage must stay labelled 2011.
CENSUS_2011_POP = {
    "New Delhi": 142004,
    "South Delhi": 2731929,
    "East Delhi": 1709346,
    "Jaipur": 6626178,
    "Jodhpur": 3687165,
    "Barmer": 2603751,
}

MONSOON_MONTHS = {6, 7, 8, 9}
DRAINAGE_TYPES = {"waterlogging", "culvert", "drainage"}


def haversine_meters(a: dict, b: dict) -> float:
    r = 6_371_000
    d_lat = math.radians(b["lat"] - a["lat"])
    d_lng = math.radians(b["lng"] - a["lng"])
    la1 = math.radians(a["lat"])
    la2 = math.radians(b["lat"])
    h = math.sin(d_lat / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin(d_lng / 2) ** 2
    return 2 * r * math.asin(min(1.0, math.sqrt(h)))


def cluster_radius_meters(tenant_id: str) -> float:
    return 400.0 if tenant_id == "rajasthan_pwd" else 150.0


def _clamp01(n: float) -> float:
    return max(0.0, min(1.0, n))


def _max_pop(tenant_id: str) -> int:
    if tenant_id == "rajasthan_pwd":
        return max(CENSUS_2011_POP["Jaipur"], CENSUS_2011_POP["Jodhpur"], CENSUS_2011_POP["Barmer"])
    return max(
        CENSUS_2011_POP["New Delhi"],
        CENSUS_2011_POP["South Delhi"],
        CENSUS_2011_POP["East Delhi"],
    )


def _gap_value(kind: DemandType, tenant_id: str) -> float:
    if kind in {"culvert", "drainage"}:
        return 0.9
    if kind == "waterlogging":
        return 0.7
    if kind == "pothole":
        return 0.65 if tenant_id == "rajasthan_pwd" else 0.45
    if kind == "footpath":
        return 0.4
    if kind == "streetlight":
        return 0.25
    return 0.3


def _seasonal(kind: DemandType, at: datetime) -> float:
    if kind not in DRAINAGE_TYPES:
        return 0.0
    return 1.0 if at.month in MONSOON_MONTHS else 0.0


def score_cluster(
    tickets: list[Ticket],
    *,
    has_nfhs: bool = False,
    has_pmgsy_osm: bool = False,
    has_mplads: bool = False,
) -> ScoreBreakdown:
    lead = tickets[0]
    tenant_id = lead.tenant_id
    kind = lead.classification.type
    district = lead.district
    at = datetime.fromisoformat(lead.created_at.replace("Z", "+00:00"))

    reporters = min(len(tickets), 12)
    repeat = reporters / 12
    pop = CENSUS_2011_POP.get(district, 0)
    population = (pop / _max_pop(tenant_id)) if pop else None
    vulnerability = 0.5 if has_nfhs else None
    gap = _gap_value(kind, tenant_id)
    investment = 0.4 if has_mplads else 1.0
    seasonal = _seasonal(kind, at)

    components = [
        ScoreComponent(
            key="repeat",
            name="Repeat demand",
            weight=WEIGHTS["repeat"],
            value=repeat,
            used=True,
            note=f"{len(tickets)} SAMPLE reporters on this stretch, cap 12.",
        ),
        ScoreComponent(
            key="population",
            name="Population pressure",
            weight=WEIGHTS["population"],
            value=population,
            used=population is not None,
            note=f"Census 2011 PCA TOT_P for {district} = {pop:,}. Vintage 2011.",
        ),
        ScoreComponent(
            key="vulnerability",
            name="Vulnerability overlay",
            weight=WEIGHTS["vulnerability"],
            value=vulnerability,
            used=has_nfhs,
            note="NFHS-5 district composite."
            if has_nfhs
            else "NFHS-5 not loaded. Weight folds into population.",
        ),
        ScoreComponent(
            key="gap",
            name="Infrastructure gap",
            weight=WEIGHTS["gap"],
            value=gap,
            used=True,
            note="OSM + PMGSY snap."
            if has_pmgsy_osm
            else "Partial: category heuristic until OSM/PMGSY highways are loaded. Not a live PWD inventory.",
        ),
        ScoreComponent(
            key="investment",
            name="Investment already present",
            weight=WEIGHTS["investment"],
            value=investment,
            used=True,
            note="MPLADS snapshot joined on PC."
            if has_mplads
            else "Partial: no MPLADS/PMGSY work of this class in the loaded snapshot. Absence raises score.",
        ),
        ScoreComponent(
            key="seasonal",
            name="Seasonal urgency",
            weight=WEIGHTS["seasonal"],
            value=seasonal,
            used=True,
            note=f"Active for {kind} in monsoon months. Month={at.month}."
            if kind in DRAINAGE_TYPES
            else "Off — not a drainage/culvert/waterlogging class.",
        ),
    ]

    if not has_nfhs and population is not None:
        for c in components:
            if c.key == "population":
                c.weight += WEIGHTS["vulnerability"]

    used = [c for c in components if c.used and c.value is not None]
    weight_sum = sum(c.weight for c in used) or 1.0
    priority = sum(c.weight * _clamp01(c.value or 0) for c in used)
    mode = "full" if (has_nfhs and has_pmgsy_osm and has_mplads) else "partial"

    return ScoreBreakdown(
        mode=mode,
        priority_score=round(priority / weight_sum, 2),
        components=components,
        vintage_notes=[
            "Census population is 2011 PCA, not 2026.",
            "Citizen events on this map are SAMPLE, not real PWD Sewa tickets.",
            "OSM is not an official PWD inventory.",
        ],
    )


def to_cluster(cluster_id: str, tickets: list[Ticket]) -> Cluster:
    ordered = sorted(tickets, key=lambda t: t.created_at)
    lead = ordered[0]
    lat = sum(t.lat for t in ordered) / len(ordered)
    lng = sum(t.lng for t in ordered) / len(ordered)
    elevated = any(t.status == "elevated" for t in ordered)
    return Cluster(
        id=cluster_id,
        tenant_id=lead.tenant_id,
        type=lead.classification.type,
        lat=lat,
        lng=lng,
        district=lead.district,
        reporter_count=len(ordered),
        tickets=ordered,
        score=score_cluster(ordered),
        status="elevated" if elevated else "open",
    )
