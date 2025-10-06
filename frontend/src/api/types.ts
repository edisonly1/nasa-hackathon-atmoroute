// src/api/types.ts
export type ISODate = string;
export type GeometryType = "route" | "area";

export interface EventRequest {
  geometry_type: GeometryType;
  geometry_geojson: GeoJSON.LineString | GeoJSON.Polygon;
  start_ts: string;        // ISO, midnight UTC for the chosen date
  duration_min: number;    // days * 1440
  step_min: number;        // 1440 (daily)
  mode: "climo";
  hourly?: boolean;
  thresholds?: { evs_min?: number };
}

export interface CellEVS { t: number; total: number; rain: number; wind: number; heat: number; humidity: number; }
export interface EventCell { cell_id: number; lon: number; lat: number; evs: CellEVS[] }
export interface EventAggregate { t: number; coverage_ge_70: number; mean: number; min: number; }

export interface EventMeta {
  units: Record<string,string>;
  sources: string[];
  notes?: string;
  extra?: {
    mode?: string;
    best_time_idx?: number;
    best_time_iso?: ISODate;
    climo_window_days?: number;
    coerced_to_daily?: boolean;
  };
}

export interface EventResponse {
  event_id: string;
  times: ISODate[];
  cells: EventCell[];
  aggregates: EventAggregate[];
  meta: EventMeta;
}

export interface PoeRequest {
  lat: number; lon: number;
  date: string;            // YYYY-MM-DD
  window_days: number;     // default 14
  thresholds: { precip_mm_day: number; wind_mph: number; rh_pct: number; heatindex_F: number; };
}

export interface PoeResponse {
  poe: { precip_mm_day: number; wind_mph: number; rh_pct: number; heatindex_F: number };
  histograms: Record<string, unknown>;
  meta: { units?: Record<string,string>; sources?: string[]; notes?: string; [k: string]: any };
}


// AI
export interface AIScoreResponse {
  p_ge_70: number;                   // probability EVS >= 70 (0..1)
  conf: [number, number];            // confidence interval (0..1)
  location?: [number, number];       // present for /ai/realtime
  features_used?: Record<string, number>;
}

export interface LLMBriefResponse {
  p_ge_70: number;
  conf: [number, number];
  brief: string;                     // short offline NLG summary
}
