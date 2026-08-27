import type { TenantId } from "../../../packages/schema/src";

export type Tenant = {
  id: TenantId;
  short: string;
  name: string;
  state: string;
  districts: string[];
  center: [number, number];
  zoom: number;
  slaHours: number;
  languages: string[];
};

export const TENANTS: Record<TenantId, Tenant> = {
  delhi_pwd: {
    id: "delhi_pwd",
    short: "Delhi",
    name: "PWD Delhi",
    state: "NCT of Delhi",
    districts: ["New Delhi", "South Delhi", "East Delhi"],
    center: [28.6139, 77.209],
    zoom: 12,
    slaHours: 72,
    languages: ["hi", "en"],
  },
  rajasthan_pwd: {
    id: "rajasthan_pwd",
    short: "Rajasthan",
    name: "PWD Rajasthan",
    state: "Rajasthan",
    districts: ["Jaipur", "Jodhpur", "Barmer"],
    center: [26.2389, 73.0243],
    zoom: 7,
    slaHours: 96,
    languages: ["hi", "en", "raj"],
  },
};

export function districtForPoint(
  tenantId: TenantId,
  lat: number,
  lng: number,
): string {
  if (tenantId === "rajasthan_pwd") {
    if (lat < 26.2 && lng < 72) return "Barmer";
    if (lng < 73.8) return "Jodhpur";
    return "Jaipur";
  }
  if (lng > 77.26) return "East Delhi";
  if (lat < 28.56) return "South Delhi";
  return "New Delhi";
}
