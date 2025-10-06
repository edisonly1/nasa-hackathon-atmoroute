// src/api/ai.ts
import { api } from "./client";

export type EVSRealtime = {
  location: [number, number];
  features_used: Record<string, number>;
  p_ge_70: number;        // probability 0..1
  conf: [number, number]; // [low, high] 0..1
};

export async function aiRealtime(lat: number, lon: number): Promise<EVSRealtime> {
  const { data } = await api.get("/api/ai/realtime", { params: { lat, lon } });
  return data;
}

export async function llmBrief(lat: number, lon: number): Promise<{ brief: string }> {
  const { data } = await api.get("/api/llm/brief", { params: { lat, lon } });
  return data;
}
