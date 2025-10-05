// src/api/endpoints.ts
import { api } from "./client";
import type { EventRequest, EventResponse, PoeRequest, PoeResponse } from "./types";

export async function postEvent(req: EventRequest): Promise<EventResponse> {
  const { data } = await api.post<EventResponse>("/api/event", req);
  return data;
}

export async function postPoe(req: PoeRequest): Promise<PoeResponse> {
  const { thresholds, ...rest } = req;

  // Guard: thresholds must exist
  if (!thresholds || typeof thresholds !== "object") {
    throw new Error("thresholds is required");
  }

  // Build metrics array in the shape the backend expects
  const metrics = Object.entries(thresholds).map(([k, v]) => ({
    var: k,               // <- required by backend
    threshold: Number(v), // <- required by backend
  }));

  const body = { ...rest, thresholds, metrics };
  const { data } = await api.post<PoeResponse>("/api/poe", body);
  return data;
}

//  backend exports at /api/event/{id}/export
export function getExportUrl(event_id: string, format: "csv" | "json" = "csv") {
  const base = api.defaults.baseURL?.replace(/\/$/, "") || "";
  return `${base}/api/event/${encodeURIComponent(event_id)}/export?format=${format}`;
}
