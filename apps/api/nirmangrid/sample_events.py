from __future__ import annotations

import csv
import json
import math
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .paths import repo_root
from .schemas import Classification, Ticket

SEEDS = [
    {
        "cluster": "dl-janpath-pothole",
        "n": 9,
        "type": "pothole",
        "lat": 28.6281,
        "lng": 77.2192,
        "district": "New Delhi",
        "lang": "hi",
        "texts": [
            "जनकपथ पर बड़ा गड्ढा, गाड़ियाँ झटका खा रही हैं",
            "Same stretch, pothole near the crossing after rain",
            "सड़क टूटी हुई है, रात को दिखाई नहीं देती",
        ],
    },
    {
        "cluster": "dl-outerring-pothole",
        "n": 6,
        "type": "pothole",
        "lat": 28.5274,
        "lng": 77.2068,
        "district": "South Delhi",
        "lang": "en",
        "texts": [
            "Outer Ring Road pothole cluster near the flyover ramp",
            "दो लेन में गड्ढे, बाइक गिरने का डर",
        ],
    },
    {
        "cluster": "dl-vikasmarg-water",
        "n": 7,
        "type": "waterlogging",
        "lat": 28.6362,
        "lng": 77.2874,
        "district": "East Delhi",
        "lang": "hi",
        "texts": [
            "विकास मार्ग पर बारिश में कमर तक पानी",
            "Drain blocked, water sits for hours after rain",
        ],
    },
    {
        "cluster": "dl-cp-streetlight",
        "n": 5,
        "type": "streetlight",
        "lat": 28.6328,
        "lng": 77.2195,
        "district": "New Delhi",
        "lang": "en",
        "texts": [
            "Streetlight dead on this stretch since last week",
            "बत्ती खराब, अंधेरा, महिलाएँ डरती हैं",
        ],
    },
    {
        "cluster": "dl-press-footpath",
        "n": 4,
        "type": "footpath",
        "lat": 28.5379,
        "lng": 77.2169,
        "district": "South Delhi",
        "lang": "hi",
        "texts": [
            "फुटपाथ टूटा, व्हीलचेयर नहीं जा सकती",
            "Broken footpath tiles, people walking on the carriageway",
        ],
    },
    {
        "cluster": "dl-aurobindo-drain",
        "n": 3,
        "type": "drainage",
        "lat": 28.5618,
        "lng": 77.2067,
        "district": "South Delhi",
        "lang": "en",
        "texts": ["Open drain overflowing onto Aurobindo Marg after rain"],
    },
]

SCATTER = [
    ("pothole", 28.601, 77.198, "New Delhi", "en", "Pothole on this carriageway after the lights"),
    ("pothole", 28.618, 77.241, "New Delhi", "hi", "गड्ढा, बस रुकने के पास"),
    ("pothole", 28.542, 77.198, "South Delhi", "en", "Rutting and pothole on the service road"),
    ("pothole", 28.551, 77.231, "South Delhi", "hi", "सड़क धँसी हुई है"),
    ("streetlight", 28.605, 77.268, "East Delhi", "en", "Pole dark, no light on the footpath"),
    ("streetlight", 28.641, 77.198, "New Delhi", "hi", "लाइट फ्यूज, चौराहा अंधेरा"),
    ("streetlight", 28.572, 77.251, "South Delhi", "en", "Streetlight flickers then dies"),
    ("footpath", 28.623, 77.198, "New Delhi", "hi", "फुटपाथ पर गड्ढे, बुजुर्ग गिरे"),
    ("footpath", 28.648, 77.274, "East Delhi", "en", "Encroached and broken footpath"),
    ("waterlogging", 28.611, 77.301, "East Delhi", "hi", "बारिश में सड़क तालाब"),
    ("waterlogging", 28.534, 77.221, "South Delhi", "en", "Underpass floods every monsoon"),
    ("drainage", 28.619, 77.277, "East Delhi", "hi", "नाली जाम, बदबू"),
    ("drainage", 28.598, 77.221, "New Delhi", "en", "Cover missing on the roadside drain"),
    ("culvert", 28.529, 77.189, "South Delhi", "en", "Culvert blocked with silt and plastic"),
    ("pothole", 28.633, 77.255, "East Delhi", "hi", "गड्ढे की कतार"),
    ("streetlight", 28.558, 77.189, "South Delhi", "en", "Three lights out on this curve"),
    ("footpath", 28.567, 77.241, "South Delhi", "hi", "टाइल्स उखड़ी हुई हैं"),
    ("other", 28.625, 77.208, "New Delhi", "en", "Loose manhole cover on the stretch"),
]

SINGLETONS = [
    ("pothole", 28.61, 77.23, "New Delhi", "en", "Isolated pothole near C-Hexagon"),
    ("streetlight", 28.59, 77.25, "South Delhi", "hi", "स्ट्रीटलाइट फ्यूज"),
    ("footpath", 28.65, 77.30, "East Delhi", "en", "Footpath missing on this side of the road"),
    ("waterlogging", 28.62, 77.28, "East Delhi", "hi", "नाला चोक, पानी रुकता है"),
    ("culvert", 28.55, 77.19, "South Delhi", "en", "Culvert mouth silted, water spills onto the service lane"),
    ("pothole", 28.64, 77.21, "New Delhi", "hi", "गड्ढा, स्कूल के बाहर"),
    ("streetlight", 28.57, 77.22, "South Delhi", "en", "Two poles dark on this bend"),
    ("drainage", 28.63, 77.31, "East Delhi", "hi", "नाली कवर गायब"),
]


def jitter(i: int, scale: float = 0.00032) -> tuple[float, float]:
    a = math.sin(i * 12.9898) * 43758.5453
    b = math.cos(i * 78.233) * 24634.634
    return (a - math.floor(a) - 0.5) * 2 * scale, (b - math.floor(b) - 0.5) * 2 * scale


def _ticket(n: int, cluster: str, kind: str, lat: float, lng: float, district: str, lang: str, text: str) -> Ticket:
    created = datetime(2026, 8, 20, 6, 0, tzinfo=timezone.utc) + timedelta(hours=n)
    severity = "high" if kind in {"waterlogging", "culvert"} else "medium"
    return Ticket(
        id=f"SAMPLE-DL-{n:03d}",
        tenant_id="delhi_pwd",
        lat=lat,
        lng=lng,
        text=text,
        lang=lang,  # type: ignore[arg-type]
        channel="web",
        media_type="photo",
        classification=Classification(
            type=kind,  # type: ignore[arg-type]
            severity=severity,  # type: ignore[arg-type]
            lang=lang,  # type: ignore[arg-type]
            summary=text,
            reason=f"Citizen photo + text labelled {kind} on a PWD-relevant stretch.",
            confidence=0.86,
            mplads_eligible=kind != "other",
        ),
        cluster_id=cluster,
        source="SAMPLE",
        district=district,
        created_at=created.isoformat().replace("+00:00", "Z"),
        status="open",
    )


def delhi_sample_tickets() -> list[Ticket]:
    out: list[Ticket] = []
    n = 0
    for seed in SEEDS:
        for i in range(seed["n"]):
            n += 1
            d_lat, d_lng = jitter(n)
            lang = seed["lang"] if i % 2 == 0 else ("en" if i % 3 == 0 else "hi")
            text = seed["texts"][i % len(seed["texts"])]
            out.append(
                _ticket(
                    n,
                    seed["cluster"],
                    seed["type"],
                    seed["lat"] + d_lat,
                    seed["lng"] + d_lng,
                    seed["district"],
                    lang,
                    text,
                )
            )
    for idx, (kind, lat, lng, district, lang, text) in enumerate(SINGLETONS, start=1):
        n += 1
        d_lat, d_lng = jitter(n + 50)
        out.append(_ticket(n, f"dl-single-{idx}", kind, lat + d_lat, lng + d_lng, district, lang, text))
    for idx, (kind, lat, lng, district, lang, text) in enumerate(SCATTER, start=1):
        n += 1
        d_lat, d_lng = jitter(n + 90)
        out.append(_ticket(n, f"dl-scatter-{idx}", kind, lat + d_lat, lng + d_lng, district, lang, text))
    return out


def write_sample_files(out_dir: Path | None = None) -> dict:
    tickets = delhi_sample_tickets()
    folder = out_dir or (repo_root() / "data" / "sample")
    folder.mkdir(parents=True, exist_ok=True)
    payload = [t.model_dump() for t in tickets]
    json_path = folder / "events.json"
    csv_path = folder / "events.csv"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    fields = [
        "id",
        "source",
        "tenant_id",
        "lat",
        "lng",
        "lang",
        "channel",
        "media_type",
        "raw_text",
        "category_gold",
        "district",
        "cluster_id",
    ]
    with csv_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for t in tickets:
            writer.writerow(
                {
                    "id": t.id,
                    "source": t.source,
                    "tenant_id": t.tenant_id,
                    "lat": t.lat,
                    "lng": t.lng,
                    "lang": t.lang,
                    "channel": t.channel,
                    "media_type": t.media_type,
                    "raw_text": t.text,
                    "category_gold": t.classification.type,
                    "district": t.district,
                    "cluster_id": t.cluster_id,
                }
            )
    return {"count": len(tickets), "json": str(json_path), "csv": str(csv_path)}
