// src/lib/thresholds.ts

// Shared defaults (match your sidebar UI)
export const DEFAULT_THRESHOLDS = {
  precip_mm_day: 10,
  wind_mph: 20,
  rh_pct: 80,
  heatindex_F: 90, // change to 95 if you prefer
};

export type PoeThresholds = {
  precip_mm_day: number;
  wind_mph: number;
  rh_pct: number;
  heatindex_F: number;
};

// Accepts partial/optional thresholds from UI, returns a complete object
export function normalizeThresholds(t: Partial<PoeThresholds> | any): PoeThresholds {
  return {
    precip_mm_day: Number(t?.precip_mm_day ?? DEFAULT_THRESHOLDS.precip_mm_day),
    wind_mph: Number(t?.wind_mph ?? DEFAULT_THRESHOLDS.wind_mph),
    rh_pct: Number(t?.rh_pct ?? DEFAULT_THRESHOLDS.rh_pct),
    heatindex_F: Number(t?.heatindex_F ?? DEFAULT_THRESHOLDS.heatindex_F),
  };
}
