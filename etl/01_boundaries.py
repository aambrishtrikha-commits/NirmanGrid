"""D01 — Datameet Census 2011 district polygons for NCT of Delhi and Rajasthan.

Datameet publishes shapefiles, not GeoJSON. This script downloads the .shp set,
filters DL + RJ, writes GeoJSON. Does not invent PWD circle shapefiles.
Licence: CC BY 4.0 / CC BY 2.5 India. Cite Datameet.
"""

from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "datameet"
OUT = ROOT / "data" / "clean" / "boundaries"
BASE = "https://raw.githubusercontent.com/datameet/maps/master/Districts/Census_2011/2011_Dist"
PARTS = (".shp", ".shx", ".dbf", ".prj")
KEEP_STATES = {"nct of delhi", "delhi", "rajasthan"}


def download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "NirmanGrid/0.1 (hackathon ETL)"})
    with urllib.request.urlopen(req, timeout=180) as resp, dest.open("wb") as fh:
        fh.write(resp.read())


def state_of(rec: dict) -> str:
    for key in ("ST_NM", "st_nm", "STATE", "STNAME"):
        if rec.get(key):
            return str(rec[key]).strip().lower()
    return ""


def main() -> int:
    try:
        import shapefile
    except ImportError:
        print("pip install pyshp", file=sys.stderr)
        return 1

    RAW.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    for ext in PARTS:
        dest = RAW / f"2011_Dist{ext}"
        if not dest.exists():
            print(f"Downloading 2011_Dist{ext}")
            download(BASE + ext, dest)

    reader = shapefile.Reader(str(RAW / "2011_Dist"))
    fields = [f[0] for f in reader.fields[1:]]
    kept = []
    for sr in reader.shapeRecords():
        props = {fields[i]: sr.record[i] for i in range(len(fields))}
        if state_of(props) not in KEEP_STATES:
            continue
        geom = sr.shape.__geo_interface__
        kept.append({"type": "Feature", "properties": props, "geometry": geom})

    if not kept:
        print("No Delhi/Rajasthan features. Field names:", fields, file=sys.stderr)
        return 1

    dest = OUT / "districts_dl_rj.geojson"
    dest.write_text(
        json.dumps(
            {
                "type": "FeatureCollection",
                "name": "nirmangrid-districts-dl-rj",
                "attribution": "Datameet maps, Census 2011 districts. Vintage 2011. CC BY.",
                "features": kept,
            }
        ),
        encoding="utf-8",
    )
    print(f"Wrote {len(kept)} districts -> {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
