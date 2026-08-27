"""Snap a pin to the nearest OSM/PMGSY way. OSM is not a PWD inventory."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from shapely import STRtree
from shapely.geometry import Point, shape

from .paths import repo_root

DEG_PER_M = 1 / 111_320


def _load_lines(path: Path, source: str) -> list[tuple]:
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    lines = []
    for feat in data.get("features", []):
        geom = feat.get("geometry")
        if not geom:
            continue
        try:
            g = shape(geom)
        except Exception:  # noqa: BLE001
            continue
        if g.is_empty:
            continue
        props = feat.get("properties") or {}
        name = props.get("name") or props.get("ref") or props.get("road_name") or f"unnamed {source} way"
        lines.append((g, name, source))
    return lines


@lru_cache(maxsize=1)
def _index():
    clean = repo_root() / "data" / "clean"
    lines: list[tuple] = []
    for path in sorted(clean.glob("*_highways.geojson")):
        lines.extend(_load_lines(path, "OSM"))
    pmgsy = clean / "rj_pmgsy_roads.geojson"
    if pmgsy.exists():
        lines.extend(_load_lines(pmgsy, "PMGSY"))
    geoms = [g for g, _, _ in lines]
    tree = STRtree(geoms) if geoms else None
    return lines, tree


def layers_loaded() -> dict:
    clean = repo_root() / "data" / "clean"
    return {
        "delhi_osm": (clean / "delhi_highways.geojson").exists(),
        "rajasthan_osm": (clean / "rj_highways.geojson").exists(),
        "pmgsy": (clean / "rj_pmgsy_roads.geojson").exists(),
    }


def nearest_way(lat: float, lng: float, max_meters: float = 150.0) -> dict | None:
    lines, tree = _index()
    if not tree:
        return None
    point = Point(lng, lat)
    buf = max_meters * DEG_PER_M
    idxs = tree.query(point.buffer(buf))
    best = None
    best_m = max_meters
    for i in idxs:
        geom, name, source = lines[int(i)]
        meters = float(geom.distance(point) / DEG_PER_M)
        if meters < best_m:
            best_m = meters
            snapped = geom.interpolate(geom.project(point))
            best = {
                "lat": snapped.y,
                "lng": snapped.x,
                "way_name": name,
                "offset_m": round(meters, 1),
                "source": source,
            }
    return best


def snap_to_highway(lat: float, lng: float, tenant_id: str = "delhi_pwd") -> dict | None:
    max_m = 150.0 if tenant_id == "rajasthan_pwd" else 80.0
    return nearest_way(lat, lng, max_meters=max_m)


def gap_from_layers(lat: float, lng: float, kind: str, tenant_id: str) -> tuple[float, bool, str]:
    """Return (gap_value, used_layers, note). High gap = missing all-weather access."""
    loaded = layers_loaded()
    used = loaded["delhi_osm"] or loaded["rajasthan_osm"] or loaded["pmgsy"]
    thresh = 400.0 if tenant_id == "rajasthan_pwd" else 80.0
    hit = nearest_way(lat, lng, max_meters=max(thresh, 800.0))
    if not used:
        heuristic = 0.9 if kind in {"culvert", "drainage"} else 0.45
        if kind == "pothole" and tenant_id == "rajasthan_pwd":
            heuristic = 0.65
        return heuristic, False, "Partial: no OSM/PMGSY highways loaded."
    if hit is None or hit["offset_m"] > thresh:
        return (
            0.92,
            True,
            f"No {hit['source'] if hit else 'OSM/PMGSY'} classified road within {int(thresh)} m. OSM is not a PWD inventory.",
        )
    if kind in {"culvert", "drainage", "waterlogging"}:
        return (
            0.72,
            True,
            f"Nearest {hit['source']} way '{hit['way_name']}' at {hit['offset_m']} m — drainage/culvert demand.",
        )
    return (
        0.38,
        True,
        f"Road present: {hit['source']} '{hit['way_name']}' at {hit['offset_m']} m. Condition demand, not a missing link.",
    )
