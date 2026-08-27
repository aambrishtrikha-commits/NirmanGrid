"""Snap a pin to the nearest OSM highway if data/clean/delhi_highways.geojson exists."""

from __future__ import annotations

import json
from functools import lru_cache

from shapely.geometry import LineString, Point, shape

from .paths import repo_root


@lru_cache(maxsize=1)
def _highways():
    path = repo_root() / "data" / "clean" / "delhi_highways.geojson"
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    lines = []
    for feat in data.get("features", []):
        geom = shape(feat["geometry"])
        if geom.is_empty:
            continue
        props = feat.get("properties") or {}
        lines.append((geom, props.get("name") or props.get("ref") or "unnamed OSM way"))
    return lines


def snap_to_highway(lat: float, lng: float, max_meters: float = 80.0) -> dict | None:
    lines = _highways()
    if not lines:
        return None
    point = Point(lng, lat)
    best = None
    best_m = max_meters
    for geom, name in lines:
        dist_deg = geom.distance(point)
        meters = dist_deg * 111_320
        if meters < best_m:
            best_m = meters
            snapped = geom.interpolate(geom.project(point))
            best = {
                "lat": snapped.y,
                "lng": snapped.x,
                "way_name": name,
                "offset_m": round(meters, 1),
                "source": "OSM",
            }
    return best
