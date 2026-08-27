"""PMGSY GeoSadak rural roads for Jaipur, Jodhpur, Barmer.

Downloads Datameet Rajasthan.zip. District IDs in the file are numeric, so we
spatially filter against Census 2011 Datameet polygons (already labelled 2011).
Not a live GeoSadak API.
"""

from __future__ import annotations

import json
import sys
import urllib.request
import zipfile
from pathlib import Path

from shapely.geometry import shape
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "pmgsy"
OUT = ROOT / "data" / "clean" / "rj_pmgsy_roads.geojson"
BND = ROOT / "data" / "clean" / "boundaries" / "districts_dl_rj.geojson"
URL = "https://github.com/datameet/pmgsy-geosadak/raw/master/data/Road_DRRP/Rajasthan.zip"
KEEP = {"Jaipur", "Jodhpur", "Barmer"}


def download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    print(f"Downloading {url}")
    req = urllib.request.Request(url, headers={"User-Agent": "NirmanGrid/0.1 (hackathon ETL)"})
    with urllib.request.urlopen(req, timeout=300) as resp, dest.open("wb") as fh:
        while True:
            chunk = resp.read(1024 * 256)
            if not chunk:
                break
            fh.write(chunk)


def district_union():
    data = json.loads(BND.read_text(encoding="utf-8"))
    geoms = []
    for feat in data["features"]:
        props = feat.get("properties") or {}
        if props.get("DISTRICT") in KEEP and props.get("ST_NM") == "Rajasthan":
            geoms.append(shape(feat["geometry"]))
    if not geoms:
        raise SystemExit("Need Jaipur/Jodhpur/Barmer polygons in districts_dl_rj.geojson")
    return unary_union(geoms)


def main() -> int:
    try:
        import shapefile
    except ImportError:
        print("pip install pyshp", file=sys.stderr)
        return 1

    RAW.mkdir(parents=True, exist_ok=True)
    zpath = RAW / "Rajasthan.zip"
    if not zpath.exists() or zpath.stat().st_size < 1000:
        download(URL, zpath)

    extract_dir = RAW / "extracted"
    extract_dir.mkdir(exist_ok=True)
    with zipfile.ZipFile(zpath) as zf:
        zf.extractall(extract_dir)

    mask = district_union()
    kept = []
    for shp in extract_dir.rglob("*.shp"):
        reader = shapefile.Reader(str(shp))
        try:
            fields = [f[0] for f in reader.fields[1:]]
            for sr in reader.shapeRecords():
                props = {fields[i]: sr.record[i] for i in range(len(fields))}
                geom = sr.shape.__geo_interface__
                g = shape(geom)
                if g.is_empty or not g.intersects(mask):
                    continue
                props["source"] = "PMGSY GeoSadak"
                props["licence"] = "Government Open Data License — India"
                kept.append({"type": "Feature", "properties": props, "geometry": geom})
        finally:
            reader.close()

    if not kept:
        print("No PMGSY ways intersecting Jaipur/Jodhpur/Barmer polygons.", file=sys.stderr)
        return 1

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(
            {
                "type": "FeatureCollection",
                "name": "rj_pmgsy_roads",
                "attribution": "MoRD PMGSY GeoSadak via Datameet. Spatial filter on Census 2011 districts. Not a live portal join.",
                "features": kept,
            }
        ),
        encoding="utf-8",
    )
    print(f"Wrote {len(kept)} PMGSY ways -> {OUT} ({OUT.stat().st_size / 1e6:.1f} MB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
