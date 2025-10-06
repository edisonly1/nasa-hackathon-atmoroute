// src/components/weather/AIInsightCard.tsx
import { useState } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { aiRealtime, llmBrief, EVSRealtime } from "@/api/ai";

export default function AIInsightCard({ lat, lon }: { lat: string; lon: string }) {
  const [evs, setEvs] = useState<EVSRealtime | null>(null);
  const [brief, setBrief] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const latN = Number(lat), lonN = Number(lon);
  const disabled = !Number.isFinite(latN) || !Number.isFinite(lonN);

  async function runAI() {
    if (disabled) return;
    setLoading(true);
    try {
      const r = await aiRealtime(latN, lonN);
      setEvs(r);
      const b = await llmBrief(latN, lonN);
      setBrief(b.brief);
      console.log("[AI Realtime]", r);
      console.log("[AI Brief]", b);
    } catch (e: any) {
      console.error(e);
      setBrief(`Error: ${e.message}`);
    } finally {
      setLoading(false);
    }
  }

  return (
    <Card className="mt-4">
      <CardHeader>
        <CardTitle>AI Insight (EVS + Brief)</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="flex items-center gap-2">
          <Button onClick={runAI} disabled={disabled || loading}>
            {loading ? "Running..." : "Run AI for this point"}
          </Button>
          {disabled && <span className="text-sm text-muted-foreground">Drop a pin first.</span>}
        </div>
        {evs && (
          <div className="text-sm">
            <div>
              <b>EVS ≥ 70% suitability:</b>{" "}
              {(evs.p_ge_70 * 100).toFixed(1)}%{" "}
              <span className="text-muted-foreground">
                conf {Math.round(evs.conf[0]*100)}–{Math.round(evs.conf[1]*100)}%
              </span>
            </div>
          </div>
        )}
        {brief && <pre className="text-sm whitespace-pre-wrap">{brief}</pre>}
      </CardContent>
    </Card>
  );
}
