import type {
  DemandType,
  Lang,
  Ticket,
} from "../../../packages/schema/src";

type Seed = {
  cluster: string;
  n: number;
  type: DemandType;
  lat: number;
  lng: number;
  district: string;
  lang: Lang;
  texts: string[];
};

const SEEDS: Seed[] = [
  {
    cluster: "dl-janpath-pothole",
    n: 9,
    type: "pothole",
    lat: 28.6281,
    lng: 77.2192,
    district: "New Delhi",
    lang: "hi",
    texts: [
      "जनकपथ पर बड़ा गड्ढा, गाड़ियाँ झटका खा रही हैं",
      "Same stretch, pothole near the crossing after rain",
      "सड़क टूटी हुई है, रात को दिखाई नहीं देती",
    ],
  },
  {
    cluster: "dl-outerring-pothole",
    n: 6,
    type: "pothole",
    lat: 28.5274,
    lng: 77.2068,
    district: "South Delhi",
    lang: "en",
    texts: [
      "Outer Ring Road pothole cluster near the flyover ramp",
      "दो लेन में गड्ढे, बाइक गिरने का डर",
    ],
  },
  {
    cluster: "dl-vikasmarg-water",
    n: 7,
    type: "waterlogging",
    lat: 28.6362,
    lng: 77.2874,
    district: "East Delhi",
    lang: "hi",
    texts: [
      "विकास मार्ग पर बारिश में कमर तक पानी",
      "Drain blocked, water sits for hours after rain",
    ],
  },
  {
    cluster: "dl-cp-streetlight",
    n: 5,
    type: "streetlight",
    lat: 28.6328,
    lng: 77.2195,
    district: "New Delhi",
    lang: "en",
    texts: [
      "Streetlight dead on this stretch since last week",
      "बत्ती खराब, अंधेरा, महिलाएँ डरती हैं",
    ],
  },
  {
    cluster: "dl-press-footpath",
    n: 4,
    type: "footpath",
    lat: 28.5379,
    lng: 77.2169,
    district: "South Delhi",
    lang: "hi",
    texts: [
      "फुटपाथ टूटा, व्हीलचेयर नहीं जा सकती",
      "Broken footpath tiles, people walking on the carriageway",
    ],
  },
  {
    cluster: "dl-aurobindo-drain",
    n: 3,
    type: "drainage",
    lat: 28.5618,
    lng: 77.2067,
    district: "South Delhi",
    lang: "en",
    texts: ["Open drain overflowing onto Aurobindo Marg after rain"],
  },
];

const SCATTER: Array<[DemandType, number, number, string, Lang, string]> = [
  ["pothole", 28.601, 77.198, "New Delhi", "en", "Pothole on this carriageway after the lights"],
  ["pothole", 28.618, 77.241, "New Delhi", "hi", "गड्ढा, बस रुकने के पास"],
  ["pothole", 28.542, 77.198, "South Delhi", "en", "Rutting and pothole on the service road"],
  ["pothole", 28.551, 77.231, "South Delhi", "hi", "सड़क धँसी हुई है"],
  ["streetlight", 28.605, 77.268, "East Delhi", "en", "Pole dark, no light on the footpath"],
  ["streetlight", 28.641, 77.198, "New Delhi", "hi", "लाइट फ्यूज, चौराहा अंधेरा"],
  ["streetlight", 28.572, 77.251, "South Delhi", "en", "Streetlight flickers then dies"],
  ["footpath", 28.623, 77.198, "New Delhi", "hi", "फुटपाथ पर गड्ढे, बुजुर्ग गिरे"],
  ["footpath", 28.648, 77.274, "East Delhi", "en", "Encroached and broken footpath"],
  ["waterlogging", 28.611, 77.301, "East Delhi", "hi", "बारिश में सड़क तालाब"],
  ["waterlogging", 28.534, 77.221, "South Delhi", "en", "Underpass floods every monsoon"],
  ["drainage", 28.619, 77.277, "East Delhi", "hi", "नाली जाम, बदबू"],
  ["drainage", 28.598, 77.221, "New Delhi", "en", "Cover missing on the roadside drain"],
  ["culvert", 28.529, 77.189, "South Delhi", "en", "Culvert blocked with silt and plastic"],
  ["pothole", 28.633, 77.255, "East Delhi", "hi", "गड्ढे की कतार"],
  ["streetlight", 28.558, 77.189, "South Delhi", "en", "Three lights out on this curve"],
  ["footpath", 28.567, 77.241, "South Delhi", "hi", "टाइल्स उखड़ी हुई हैं"],
  ["other", 28.625, 77.208, "New Delhi", "en", "Loose manhole cover on the stretch"],
];

const SINGLETONS: Omit<Seed, "n" | "cluster">[] = [
  {
    type: "pothole",
    lat: 28.61,
    lng: 77.23,
    district: "New Delhi",
    lang: "en",
    texts: ["Isolated pothole near C-Hexagon"],
  },
  {
    type: "streetlight",
    lat: 28.59,
    lng: 77.25,
    district: "South Delhi",
    lang: "hi",
    texts: ["स्ट्रीटलाइट फ्यूज"],
  },
  {
    type: "footpath",
    lat: 28.65,
    lng: 77.3,
    district: "East Delhi",
    lang: "en",
    texts: ["Footpath missing on this side of the road"],
  },
  {
    type: "waterlogging",
    lat: 28.62,
    lng: 77.28,
    district: "East Delhi",
    lang: "hi",
    texts: ["नाला चोक, पानी रुकता है"],
  },
  {
    type: "culvert",
    lat: 28.55,
    lng: 77.19,
    district: "South Delhi",
    lang: "en",
    texts: ["Culvert mouth silted, water spills onto the service lane"],
  },
  {
    type: "pothole",
    lat: 28.64,
    lng: 77.21,
    district: "New Delhi",
    lang: "hi",
    texts: ["गड्ढा, स्कूल के बाहर"],
  },
  {
    type: "streetlight",
    lat: 28.57,
    lng: 77.22,
    district: "South Delhi",
    lang: "en",
    texts: ["Two poles dark on this bend"],
  },
  {
    type: "drainage",
    lat: 28.63,
    lng: 77.31,
    district: "East Delhi",
    lang: "hi",
    texts: ["नाली कवर गायब"],
  },
];

function jitter(i: number, scale = 0.00032): [number, number] {
  const a = Math.sin(i * 12.9898) * 43758.5453;
  const b = Math.cos(i * 78.233) * 24634.634;
  return [
    (a - Math.floor(a) - 0.5) * 2 * scale,
    (b - Math.floor(b) - 0.5) * 2 * scale,
  ];
}

function ticketFrom(
  id: string,
  cluster: string,
  type: DemandType,
  lat: number,
  lng: number,
  district: string,
  lang: Lang,
  text: string,
  hourOffset: number,
): Ticket {
  const created = new Date(Date.UTC(2026, 7, 20, 6, 0, 0));
  created.setUTCHours(created.getUTCHours() + hourOffset);
  return {
    id,
    tenant_id: "delhi_pwd",
    lat,
    lng,
    text,
    lang,
    channel: "web",
    media_type: "photo",
    classification: {
      type,
      severity: type === "waterlogging" || type === "culvert" ? "high" : "medium",
      lang,
      summary: text,
      reason: `Citizen photo + text labelled ${type} on a PWD-relevant stretch.`,
      confidence: 0.86,
      mplads_eligible: type !== "other",
    },
    cluster_id: cluster,
    source: "SAMPLE",
    district,
    created_at: created.toISOString(),
    status: "open",
  };
}

export function delhiSampleTickets(): Ticket[] {
  const out: Ticket[] = [];
  let n = 0;
  for (const seed of SEEDS) {
    for (let i = 0; i < seed.n; i += 1) {
      n += 1;
      const [dLat, dLng] = jitter(n);
      const text = seed.texts[i % seed.texts.length];
      out.push(
        ticketFrom(
          `SAMPLE-DL-${String(n).padStart(3, "0")}`,
          seed.cluster,
          seed.type,
          seed.lat + dLat,
          seed.lng + dLng,
          seed.district,
          i % 2 === 0 ? seed.lang : i % 3 === 0 ? "en" : "hi",
          text,
          n,
        ),
      );
    }
  }
  SINGLETONS.forEach((s, idx) => {
    n += 1;
    const [dLat, dLng] = jitter(n + 50);
    out.push(
      ticketFrom(
        `SAMPLE-DL-${String(n).padStart(3, "0")}`,
        `dl-single-${idx + 1}`,
        s.type,
        s.lat + dLat,
        s.lng + dLng,
        s.district,
        s.lang,
        s.texts[0],
        n,
      ),
    );
  });
  SCATTER.forEach((row, idx) => {
    n += 1;
    const [type, lat, lng, district, lang, text] = row;
    const [dLat, dLng] = jitter(n + 90);
    out.push(
      ticketFrom(
        `SAMPLE-DL-${String(n).padStart(3, "0")}`,
        `dl-scatter-${idx + 1}`,
        type,
        lat + dLat,
        lng + dLng,
        district,
        lang,
        text,
        n,
      ),
    );
  });
  return out;
}
