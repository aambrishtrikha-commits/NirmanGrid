"""D08 — Delhi OSM highways.

Prefer a local BBBike PBF at data/raw/NewDelhi.osm.pbf if present.
Otherwise pull a bounded Overpass extract of highway=* ways for NCT of Delhi.
OSM is not an official PWD inventory. Attribute OSM / ODbL.
"""

from __future__ import annotations

import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "clean" / "delhi_highways.geojson"
RAW_PBF = ROOT / "data" / "raw" / "NewDelhi.osm.pbf"

# NCT of Delhi-ish bbox
SOUTH, WEST, NORTH, EAST = 28.40, 76.84, 28.88, 77.35

ENDPOINTS = [
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass-api.de/api/interpreter",
]
QUERY = f"""
[out:json][timeout:60];
way["highway"~"^(motorway|trunk|primary|secondary|tertiary)$"]({SOUTH},{WEST},{NORTH},{EAST});
out geom;
"""


def overpass() -> dict:
    body = urllib.parse.urlencode({"data": QUERY}).encode("utf-8")
    last_error: Exception | None = None
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
            last_error = exc
            print(f"  failed: {exc}")
    raise last_error or RuntimeError("Overpass failed")


def elements_to_geojson(elements: list[dict]) -> dict:
    features = []
    for el in elements:
        if el.get("type") != "way":
            continue
        geom = el.get("geometry") or []
        if len(geom) < 2:
            continue
        coords = [[pt["lon"], pt["lat"]] for pt in geom]
        tags = el.get("tags") or {}
        features.append(
            {
                "type": "Feature",
                "properties": {
                    "osm_id": el.get("id"),
                    "highway": tags.get("highway"),
                    "name": tags.get("name"),
                    "ref": tags.get("ref"),
                    "surface": tags.get("surface"),
                    "source": "OpenStreetMap",
                    "licence": "ODbL",
                },
                "geometry": {"type": "LineString", "coordinates": coords},
            }
        )
    return {
        "type": "FeatureCollection",
        "name": "delhi_highways",
        "attribution": "© OpenStreetMap contributors, ODbL. Not an official PWD inventory.",
        "features": features,
    }


def from_pbf(path: Path) -> dict:
    try:
        import osmium  # type: ignore
    except ImportError as exc:
        raise SystemExit(
            "Local PBF found but osmium is not installed. pip install osmium "
            "or delete the PBF and use Overpass."
        ) from exc

    ways: list[dict] = []

    class Highways(osmium.SimpleHandler):
        def way(self, w):
            if "highway" not in w.tags or len(w.nodes) < 2:
                return
            coords = []
            for n in w.nodes:
                if not n.location.valid():
                    return
                coords.append([n.lon, n.lat])
            ways.append(
                {
                    "type": "Feature",
                    "properties": {
                        "osm_id": w.id,
                        "highway": w.tags.get("highway"),
                        "name": w.tags.get("name"),
                        "ref": w.tags.get("ref"),
                        "surface": w.tags.get("surface"),
                        "source": "OpenStreetMap",
                        "licence": "ODbL",
                    },
                    "geometry": {"type": "LineString", "coordinates": coords},
                }
            )

    Highways().apply_file(str(path), locations=True)
    return {
        "type": "FeatureCollection",
        "name": "delhi_highways",
        "attribution": "© OpenStreetMap contributors, ODbL. Not an official PWD inventory.",
        "features": ways,
    }


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    if RAW_PBF.exists():
        print(f"Filtering local PBF {RAW_PBF}")
        geojson = from_pbf(RAW_PBF)
    else:
        print("No local PBF. Querying Overpass for Delhi highway=* …")
        raw = overpass()
        geojson = elements_to_geojson(raw.get("elements") or [])
    if not geojson["features"]:
        print("No highway features returned.", file=sys.stderr)
        return 1
    OUT.write_text(json.dumps(geojson), encoding="utf-8")
    size_mb = OUT.stat().st_size / 1_000_000
    print(f"Wrote {len(geojson['features'])} ways -> {OUT} ({size_mb:.1f} MB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
