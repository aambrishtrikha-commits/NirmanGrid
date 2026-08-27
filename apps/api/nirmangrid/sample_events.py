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


def _ticket(
    n: int,
    cluster: str,
    kind: str,
    lat: float,
    lng: float,
    district: str,
    lang: str,
    text: str,
    *,
    tenant_id: str = "delhi_pwd",
    prefix: str = "SAMPLE-DL",
) -> Ticket:
    created = datetime(2026, 8, 20, 6, 0, tzinfo=timezone.utc) + timedelta(hours=n)
    severity = "high" if kind in {"waterlogging", "culvert"} else "medium"
    return Ticket(
        id=f"{prefix}-{n:03d}",
        tenant_id=tenant_id,  # type: ignore[arg-type]
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


RJ_SEEDS = [
    {
        "cluster": "rj-barmer-culvert",
        "n": 9,
        "type": "culvert",
        "lat": 25.7352,
        "lng": 71.3884,
        "district": "Barmer",
        "lang": "raj",
        "texts": [
            "पुलिया टूटी, बारिश में गाड़ी नहीं जाती",
            "Culvert washed out, no all-weather access to the village",
            "पाळिया टूट गयो, मॉनसून में रास्ता बंद",
        ],
    },
    {
        "cluster": "rj-barmer-pothole",
        "n": 8,
        "type": "pothole",
        "lat": 25.7521,
        "lng": 71.3962,
        "district": "Barmer",
        "lang": "hi",
        "texts": [
            "बाड़मेर सड़क पर गड्ढे, बस हिलती है",
            "Potholes on the Barmer approach road",
        ],
    },
    {
        "cluster": "rj-jodhpur-pothole",
        "n": 8,
        "type": "pothole",
        "lat": 26.2389,
        "lng": 73.0243,
        "district": "Jodhpur",
        "lang": "hi",
        "texts": [
            "जोधपुर रिंग पर गड्ढा, रात को दिखता नहीं",
            "Jodhpur stretch pothole near the circle",
        ],
    },
    {
        "cluster": "rj-jodhpur-water",
        "n": 7,
        "type": "waterlogging",
        "lat": 26.2701,
        "lng": 73.0084,
        "district": "Jodhpur",
        "lang": "hi",
        "texts": [
            "बारिश में पानी कमर तक, नाला चोक",
            "Underpass floods every monsoon in Jodhpur",
        ],
    },
    {
        "cluster": "rj-jaipur-pothole",
        "n": 8,
        "type": "pothole",
        "lat": 26.9124,
        "lng": 75.7873,
        "district": "Jaipur",
        "lang": "hi",
        "texts": [
            "जयपुर में गड्ढे, ट्रैफिक जाम",
            "MI Road service lane pothole cluster",
        ],
    },
    {
        "cluster": "rj-jaipur-light",
        "n": 6,
        "type": "streetlight",
        "lat": 26.8467,
        "lng": 75.8020,
        "district": "Jaipur",
        "lang": "en",
        "texts": [
            "Streetlights dead on this Jaipur stretch",
            "लाइट फ्यूज, अंधेरा",
        ],
    },
]

RJ_SCATTER = [
    ("pothole", 25.70, 71.45, "Barmer", "hi", "गड्ढा, गाँव की सड़क"),
    ("drainage", 25.78, 71.37, "Barmer", "raj", "नाली जाम, बदबू"),
    ("culvert", 25.68, 71.50, "Barmer", "en", "Second culvert silted on this rural link"),
    ("streetlight", 25.75, 71.41, "Barmer", "hi", "बत्ती खराब"),
    ("pothole", 25.82, 71.33, "Barmer", "en", "Rutted track, asks for all-weather road"),
    ("footpath", 25.75, 71.39, "Barmer", "hi", "फुटपाथ नहीं"),
    ("waterlogging", 25.73, 71.42, "Barmer", "raj", "बारिश में रास्ता तालाब"),
    ("drainage", 25.76, 71.35, "Barmer", "en", "Open drain onto the carriageway"),
    ("pothole", 25.71, 71.48, "Barmer", "hi", "गड्ढों की कतार"),
    ("culvert", 25.69, 71.36, "Barmer", "en", "Culvert mouth blocked with sand"),
    ("other", 25.74, 71.40, "Barmer", "hi", "मैनहोल कवर गायब"),
    ("pothole", 25.77, 71.44, "Barmer", "en", "Shoulder broken after rain"),
    ("streetlight", 25.72, 71.38, "Barmer", "hi", "दो पोल अंधेरे"),
    ("pothole", 25.80, 71.39, "Barmer", "raj", "सड़क टूटी"),
    ("drainage", 25.66, 71.41, "Barmer", "en", "No side drain, water sits"),
    ("pothole", 25.84, 71.42, "Barmer", "hi", "बस स्टॉप के पास गड्ढा"),
    ("culvert", 25.63, 71.47, "Barmer", "en", "Cause-way, not a culvert — all-weather request"),
    ("footpath", 25.751, 71.392, "Barmer", "hi", "पैदल चलने की जगह नहीं"),
    ("pothole", 25.79, 71.36, "Barmer", "en", "Patch failed in one monsoon"),
    ("waterlogging", 25.74, 71.43, "Barmer", "hi", "नाला ओवरफ्लो"),
    ("pothole", 26.29, 73.04, "Jodhpur", "hi", "गड्ढा, स्कूल के बाहर"),
    ("streetlight", 26.25, 73.01, "Jodhpur", "en", "Two poles dark on this bend"),
    ("footpath", 26.22, 73.03, "Jodhpur", "hi", "फुटपाथ टूटा"),
    ("drainage", 26.26, 72.99, "Jodhpur", "en", "Drain cover missing"),
    ("pothole", 26.21, 73.05, "Jodhpur", "hi", "सड़क धँसी"),
    ("culvert", 26.18, 73.02, "Jodhpur", "en", "Culvert silted on the outskirt road"),
    ("waterlogging", 26.24, 73.06, "Jodhpur", "hi", "चौराहे पर पानी"),
    ("streetlight", 26.27, 73.03, "Jodhpur", "en", "Lights out after 9pm"),
    ("pothole", 26.23, 72.98, "Jodhpur", "hi", "गड्ढे, बाइक गिरने का डर"),
    ("footpath", 26.28, 73.01, "Jodhpur", "en", "Encroached footpath"),
    ("drainage", 26.20, 73.04, "Jodhpur", "hi", "नाली चोक"),
    ("pothole", 26.31, 73.02, "Jodhpur", "en", "Highway slip road pothole"),
    ("streetlight", 26.19, 73.00, "Jodhpur", "hi", "बत्ती फ्यूज"),
    ("waterlogging", 26.25, 73.07, "Jodhpur", "en", "Local ponding every rain"),
    ("pothole", 26.22, 73.06, "Jodhpur", "hi", "रिंग रोड गड्ढा"),
    ("other", 26.24, 73.01, "Jodhpur", "en", "Loose manhole"),
    ("culvert", 26.16, 72.97, "Jodhpur", "hi", "पुलिया दबी हुई"),
    ("pothole", 26.33, 73.05, "Jodhpur", "en", "Rutted shoulder"),
    ("streetlight", 26.21, 73.02, "Jodhpur", "hi", "तीन पोल अंधेरे"),
    ("drainage", 26.27, 73.00, "Jodhpur", "en", "Open drain smell"),
    ("pothole", 26.89, 75.80, "Jaipur", "hi", "गड्ढा, सिग्नल के बाद"),
    ("footpath", 26.92, 75.79, "Jaipur", "en", "Broken tiles, people on carriageway"),
    ("streetlight", 26.85, 75.81, "Jaipur", "hi", "लाइट खराब"),
    ("waterlogging", 26.91, 75.76, "Jaipur", "en", "Underpass floods"),
    ("pothole", 26.94, 75.82, "Jaipur", "hi", "सड़क टूटी"),
    ("drainage", 26.88, 75.78, "Jaipur", "en", "Choked nala"),
    ("footpath", 26.90, 75.81, "Jaipur", "hi", "व्हीलचेयर नहीं जा सकती"),
    ("pothole", 26.86, 75.79, "Jaipur", "en", "Service lane pothole"),
    ("streetlight", 26.93, 75.77, "Jaipur", "hi", "अंधेरा चौराहा"),
    ("culvert", 26.84, 75.83, "Jaipur", "en", "Culvert mouth plastic-clogged"),
    ("pothole", 26.95, 75.80, "Jaipur", "hi", "गड्ढों की लाइन"),
    ("drainage", 26.87, 75.82, "Jaipur", "en", "Cover missing"),
    ("footpath", 26.91, 75.84, "Jaipur", "hi", "फुटपाथ पर गड्ढे"),
    ("streetlight", 26.89, 75.76, "Jaipur", "en", "Flicker then die"),
    ("waterlogging", 26.86, 75.77, "Jaipur", "hi", "बारिश में तालाब"),
    ("pothole", 26.93, 75.81, "Jaipur", "en", "Bus stop pothole"),
    ("other", 26.90, 75.78, "Jaipur", "hi", "मैनहोल ढीला"),
    ("pothole", 26.88, 75.85, "Jaipur", "en", "Patch failed"),
    ("streetlight", 26.92, 75.75, "Jaipur", "hi", "दो पोल बंद"),
    ("footpath", 26.94, 75.79, "Jaipur", "en", "No footpath this side"),
]


def rajasthan_sample_tickets() -> list[Ticket]:
    out: list[Ticket] = []
    n = 0
    for seed in RJ_SEEDS:
        for i in range(seed["n"]):
            n += 1
            d_lat, d_lng = jitter(n + 200)
            lang = seed["lang"] if i % 2 == 0 else ("hi" if i % 3 else "raj")
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
                    tenant_id="rajasthan_pwd",
                    prefix="SAMPLE-RJ",
                )
            )
    for idx, (kind, lat, lng, district, lang, text) in enumerate(RJ_SCATTER, start=1):
        n += 1
        d_lat, d_lng = jitter(n + 300)
        out.append(
            _ticket(
                n,
                f"rj-scatter-{idx}",
                kind,
                lat + d_lat,
                lng + d_lng,
                district,
                lang,
                text,
                tenant_id="rajasthan_pwd",
                prefix="SAMPLE-RJ",
            )
        )
    return out


def all_sample_tickets() -> list[Ticket]:
    return delhi_sample_tickets() + rajasthan_sample_tickets()


def write_sample_files(out_dir: Path | None = None) -> dict:
    tickets = all_sample_tickets()
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
