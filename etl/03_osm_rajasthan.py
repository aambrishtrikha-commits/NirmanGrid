"""OSM highways for Jaipur, Jodhpur, Barmer.

Geofabrik Western Zone PBF is week-2 optional. This Overpass extract is the
working path. OSM is not an official PWD inventory. Attribute ODbL.
"""

from __future__ import annotations

import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "clean" / "rj_highways.geojson"

# Tight district/city bboxes so Overpass answers.
BOXES = {
    "Jaipur": (26.75, 75.60, 27.05, 76.05),
    "Jodhpur": (26.15, 72.88, 26.42, 73.18),
    "Barmer": (25.65, 71.30, 25.85, 71.50),
}

ENDPOINTS = [
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass-api.de/api/interpreter",
]


def query_for(south: float, west: float, north: float, east: float) -> str:
    return f"""
[out:json][timeout:60];
way["highway"~"^(motorway|trunk|primary|secondary|tertiary)$"]({south},{west},{north},{east});
out geom;
"""


def overpass(q: str) -> dict:
    body = urllib.parse.urlencode({"data": q}).encode("utf-8")
    last: Exception | None = None
    for url in ENDPOINTS:
        print(f"Overpass {url}")
        req = urllib.request.Request(
            url,
            data=body,
            headers={
                "User-Agent": "NirmanGrid/0.1 (hackathon ETL)",
                "Content-Type": "application/x-www-form-urlencoded",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=90) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as exc:  # noqa: BLE001
            last = exc
            print(f"  failed: {exc}")
    raise last or RuntimeError("Overpass failed")


def elements_to_features(elements: list[dict], district: str) -> list[dict]:
    feats = []
    for el in elements:
        if el.get("type") != "way":
            continue
        geom = el.get("geometry") or []
        if len(geom) < 2:
            continue
        tags = el.get("tags") or {}
        feats.append(
            {
                "type": "Feature",
                "properties": {
                    "osm_id": el.get("id"),
                    "highway": tags.get("highway"),
                    "name": tags.get("name"),
                    "ref": tags.get("ref"),
                    "district": district,
                    "source": "OpenStreetMap",
                    "licence": "ODbL",
                },
                "geometry": {
                    "type": "LineString",
                    "coordinates": [[pt["lon"], pt["lat"]] for pt in geom],
                },
            }
        )
    return feats


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    features: list[dict] = []
    if OUT.exists():
        try:
            features = json.loads(OUT.read_text(encoding="utf-8")).get("features") or []
            print(f"Resuming with {len(features)} existing ways")
        except Exception:  # noqa: BLE001
            features = []
    have = {f.get("properties", {}).get("district") for f in features}
    for district, box in BOXES.items():
        if district in have and any(
            f.get("properties", {}).get("district") == district for f in features
        ):
            print(f"Skip {district}, already extracted")
            continue
        print(f"Extract {district} {box}")
        try:
            raw = overpass(query_for(*box))
        except Exception as exc:  # noqa: BLE001
            print(f"  skip {district}: {exc}")
            continue
        part = elements_to_features(raw.get("elements") or [], district)
        print(f"  {len(part)} ways")
        features.extend(part)
        _write(features)
    if not features:
        print("No Rajasthan highway features.", file=sys.stderr)
        return 1
    _write(features)
    print(f"Wrote {len(features)} ways -> {OUT} ({OUT.stat().st_size / 1e6:.1f} MB)")
    return 0


def _write(features: list[dict]) -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(
            {
                "type": "FeatureCollection",
                "name": "rj_highways",
                "attribution": "© OpenStreetMap contributors, ODbL. Not an official PWD inventory.",
                "features": features,
            }
        ),
        encoding="utf-8",
    )


if __name__ == "__main__":
    raise SystemExit(main())
