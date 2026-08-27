import type {
  Cluster,
  DemandType,
  ScoreBreakdown,
  ScoreComponent,
  Ticket,
} from "../../schema/src/index";

/** Locked weights from NirmanGrid-Datasets.xlsx PRIORITY_SCORE. */
export const WEIGHTS = {
  repeat: 0.25,
  population: 0.2,
  vulnerability: 0.1,
  gap: 0.2,
  investment: 0.15,
  seasonal: 0.1,
} as const;

/** Census 2011 PCA district totals. Vintage must stay labelled 2011. */
export const CENSUS_2011_POP: Record<string, number> = {
  "New Delhi": 142004,
  "South Delhi": 2731929,
  "East Delhi": 1709346,
  Jaipur: 6626178,
  Jodhpur: 3687165,
  Barmer: 2603751,
};

const MONSOON_MONTHS = new Set([6, 7, 8, 9]);
const DRAINAGE_TYPES = new Set<DemandType>([
  "waterlogging",
  "culvert",
  "drainage",
]);

export function haversineMeters(
  a: { lat: number; lng: number },
  b: { lat: number; lng: number },
): number {
  const R = 6371000;
  const dLat = ((b.lat - a.lat) * Math.PI) / 180;
  const dLng = ((b.lng - a.lng) * Math.PI) / 180;
  const la1 = (a.lat * Math.PI) / 180;
  const la2 = (b.lat * Math.PI) / 180;
  const h =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(la1) * Math.cos(la2) * Math.sin(dLng / 2) ** 2;
  return 2 * R * Math.asin(Math.min(1, Math.sqrt(h)));
}

export function clusterRadiusMeters(tenantId: string): number {
  return tenantId === "rajasthan_pwd" ? 400 : 150;
}

function clamp01(n: number): number {
  return Math.max(0, Math.min(1, n));
}

function maxPopInTenant(tenantId: string): number {
  if (tenantId === "rajasthan_pwd") {
    return Math.max(
      CENSUS_2011_POP.Jaipur,
      CENSUS_2011_POP.Jodhpur,
      CENSUS_2011_POP.Barmer,
    );
  }
  return Math.max(
    CENSUS_2011_POP["New Delhi"],
    CENSUS_2011_POP["South Delhi"],
    CENSUS_2011_POP["East Delhi"],
  );
}

function gapValue(type: DemandType, tenantId: string): number {
  if (type === "culvert" || type === "drainage") return 0.9;
  if (type === "waterlogging") return 0.7;
  if (type === "pothole") return tenantId === "rajasthan_pwd" ? 0.65 : 0.45;
  if (type === "footpath") return 0.4;
  if (type === "streetlight") return 0.25;
  return 0.3;
}

function seasonalValue(type: DemandType, at: Date): number {
  if (!DRAINAGE_TYPES.has(type)) return 0;
  return MONSOON_MONTHS.has(at.getUTCMonth() + 1) ? 1 : 0;
}

/**
 * Gemini never computes this. If a source is missing, drop its weight and
 * renormalise. UI must say score mode: partial.
 */
export function scoreCluster(
  tickets: Ticket[],
  opts?: { hasNfhs?: boolean; hasPmgsyOsm?: boolean; hasMplads?: boolean },
): ScoreBreakdown {
  const lead = tickets[0];
  const tenantId = lead?.tenant_id ?? "delhi_pwd";
  const type = lead?.classification.type ?? "other";
  const district = lead?.district ?? "New Delhi";
  const at = new Date(lead?.created_at ?? Date.now());

  const hasNfhs = opts?.hasNfhs ?? false;
  const hasGapLayer = opts?.hasPmgsyOsm ?? false;
  const hasMplads = opts?.hasMplads ?? false;

  const reporters = Math.min(tickets.length, 12);
  const repeat = reporters / 12;

  const pop = CENSUS_2011_POP[district] ?? 0;
  const population = pop > 0 ? pop / maxPopInTenant(tenantId) : null;

  const vulnerability = hasNfhs ? 0.5 : null;
  const gap = hasGapLayer ? gapValue(type, tenantId) : gapValue(type, tenantId);
  const investment = hasMplads ? 0.4 : 1;
  const seasonal = seasonalValue(type, at);

  const raw: ScoreComponent[] = [
    {
      key: "repeat",
      name: "Repeat demand",
      weight: WEIGHTS.repeat,
      value: repeat,
      used: true,
      note: `${tickets.length} SAMPLE reporters on this stretch, cap 12.`,
    },
    {
      key: "population",
      name: "Population pressure",
      weight: WEIGHTS.population,
      value: population,
      used: population !== null,
      note: `Census 2011 PCA TOT_P for ${district} = ${pop.toLocaleString("en-IN")}. Vintage 2011.`,
    },
    {
      key: "vulnerability",
      name: "Vulnerability overlay",
      weight: WEIGHTS.vulnerability,
      value: vulnerability,
      used: hasNfhs,
      note: hasNfhs
        ? "NFHS-5 district composite."
        : "NFHS-5 not loaded. Weight folds into population.",
    },
    {
      key: "gap",
      name: "Infrastructure gap",
      weight: WEIGHTS.gap,
      value: gap,
      used: true,
      note: hasGapLayer
        ? "OSM + PMGSY snap."
        : "Partial: category heuristic until OSM/PMGSY highways are loaded. Not a live PWD inventory.",
    },
    {
      key: "investment",
      name: "Investment already present",
      weight: WEIGHTS.investment,
      value: investment,
      used: true,
      note: hasMplads
        ? "MPLADS snapshot joined on PC."
        : "Partial: no MPLADS/PMGSY work of this class in the loaded snapshot. Absence raises score.",
    },
    {
      key: "seasonal",
      name: "Seasonal urgency",
      weight: WEIGHTS.seasonal,
      value: seasonal,
      used: true,
      note: DRAINAGE_TYPES.has(type)
        ? `Active for ${type} in monsoon months. Month=${at.getUTCMonth() + 1}.`
        : "Off — not a drainage/culvert/waterlogging class.",
    },
  ];

  if (!hasNfhs && population !== null) {
    const popComp = raw.find((c) => c.key === "population");
    if (popComp) popComp.weight += WEIGHTS.vulnerability;
  }

  const used = raw.filter((c) => c.used && c.value !== null);
  const weightSum = used.reduce((s, c) => s + c.weight, 0) || 1;
  const priority = used.reduce(
    (s, c) => s + c.weight * clamp01(c.value as number),
    0,
  );
  const priority_score = Number((priority / weightSum).toFixed(2));

  const mode: ScoreBreakdown["mode"] =
    hasNfhs && hasGapLayer && hasMplads ? "full" : "partial";

  return {
    mode,
    priority_score,
    components: raw,
    vintage_notes: [
      "Census population is 2011 PCA, not 2026.",
      "Citizen events on this map are SAMPLE, not real PWD Sewa tickets.",
      "OSM is not an official PWD inventory.",
    ],
  };
}

export function toCluster(id: string, tickets: Ticket[]): Cluster {
  const sorted = [...tickets].sort(
    (a, b) => +new Date(a.created_at) - +new Date(b.created_at),
  );
  const lead = sorted[0];
  const lat =
    sorted.reduce((s, t) => s + t.lat, 0) / Math.max(sorted.length, 1);
  const lng =
    sorted.reduce((s, t) => s + t.lng, 0) / Math.max(sorted.length, 1);
  const elevated = sorted.some((t) => t.status === "elevated");
  return {
    id,
    tenant_id: lead.tenant_id,
    type: lead.classification.type,
    lat,
    lng,
    district: lead.district,
    reporter_count: sorted.length,
    tickets: sorted,
    score: scoreCluster(sorted),
    status: elevated ? "elevated" : "open",
  };
}
