// src/components/weather/PointPoeView.tsx
import LeafletMap from "./LeafletMap";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { LatLng } from "leaflet";
import { normalizeThresholds, PoeThresholds } from "@/lib/thresholds";


type Thresholds = {
  precip_mm_day?: number;
  wind_mph?: number;
  rh_pct?: number;
  heatindex_F?: number;
};

function extractPoe(raw: any): Record<string, number> | null {
  if (!raw) return null;
  const out = raw?.data ?? raw?.result ?? raw;
  if (out?.poe && typeof out.poe === "object") return out.poe;

  if (out?.results && typeof out.results === "object" && !Array.isArray(out.results)) {
    const acc: Record<string, number> = {};
    for (const [k, v] of Object.entries(out.results)) {
      const val = typeof (v as any)?.poe === "number" ? (v as any).poe : undefined;
      if (typeof val === "number" && val >= 0 && val <= 1) acc[k] = val;
    }
    if (Object.keys(acc).length) return acc;
  }

  // tolerant fallback (arrays, etc.)
  const arrays = [out?.metrics, out?.results, out?.items].filter(Array.isArray) as any[];
  const pickProb = (obj: any): number | undefined => {
    const preferred = ["poe", "p_exceed", "prob_exceed", "probability_exceedance", "prob", "p"];
    for (const k of preferred) {
      const v = obj?.[k];
      if (typeof v === "number" && v >= 0 && v <= 1) return v;
    }
    for (const [k, v] of Object.entries(obj || {})) {
      if (typeof v === "number" && v >= 0 && v <= 1 && /(poe|prob|exceed|p_)/i.test(k)) return v;
    }
    return undefined;
  };
  for (const arr of arrays) {
    const acc: Record<string, number> = {};
    for (const item of arr) {
      const key = item?.var ?? item?.name ?? item?.key ?? item?.variable;
      const val = pickProb(item) ?? pickProb(item?.stats);
      if (key && typeof val === "number") acc[key] = val;
    }
    if (Object.keys(acc).length) return acc;
  }
  return null;
}

function extractHists(raw: any): Record<string, number[]> {
  const out = raw?.data ?? raw?.result ?? raw;
  const res = out?.results;
  const h: Record<string, number[]> = {};
  if (res && typeof res === "object" && !Array.isArray(res)) {
    for (const [k, v] of Object.entries(res)) {
      const arr = (v as any)?.hist ?? (v as any)?.stats?.hist;
      if (Array.isArray(arr)) h[k] = arr as number[];
    }
  }
  return h;
}

function toCSV(rows: (string | number)[][]): string {
  return rows.map((r) => r.map((v) => String(v ?? "")).join(",")).join("\n");
}

function downloadBlob(data: string, filename: string, type = "text/plain") {
  const blob = new Blob([data], { type });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = filename;
  a.click();
  URL.revokeObjectURL(a.href);
}

export default function PointPoeView(props: {
  lat: string;
  lon: string;
  isDroppingPin: boolean;
  setLat: (s: string) => void;
  setLon: (s: string) => void;
  setIsDroppingPin: (b: boolean) => void;

  dateStr: string;
  thresholds: Thresholds;

  onRun: () => void;
  loading: boolean;
  out: any | null;
}) {
  const { lat, lon, isDroppingPin, setLat, setLon, setIsDroppingPin, onRun, loading, out, dateStr } = props;

  const markerLat = Number(lat),
    markerLon = Number(lon);
  const markerPosition: [number, number] | null =
    Number.isFinite(markerLat) && Number.isFinite(markerLon) ? [markerLat, markerLon] : null;

  const handleMapClick = (ll: LatLng) => {
    setLat(ll.lat.toFixed(4));
    setLon(ll.lng.toFixed(4));
    setIsDroppingPin(false);
  };

  const poeMap = extractPoe(out);
  const hists = extractHists(out);
  const meta = out?.meta
    ? { ...out.meta, sources: (out.meta.sources || []).filter((s: string) => !/Data Rods Hydrology/i.test(s)) }
    : out?.meta;

  function downloadCSV() {
    if (!poeMap) return;
    const rows = [["variable", "poe"], ...Object.entries(poeMap).map(([k, v]) => [k, String(v)])];
    downloadBlob(toCSV(rows), `poe_${markerLat}_${markerLon}_${dateStr}.csv`, "text/csv");
  }

  function downloadJSON() {
    const payload = {
      mode: "point-poe",
      date: dateStr,
      lat: markerLat,
      lon: markerLon,
      meta,
      poe: poeMap,
      histograms: hists,
    };
    downloadBlob(JSON.stringify(payload, null, 2), `poe_${markerLat}_${markerLon}_${dateStr}.json`, "application/json");
  }

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center justify-end gap-2">
        <Button onClick={onRun} disabled={loading}>
          {loading ? "Running…" : "Run PoE"}
        </Button>
        <Button variant="outline" onClick={downloadCSV} disabled={!poeMap}>
          Download CSV
        </Button>
        <Button variant="outline" onClick={downloadJSON} disabled={!out}>
          Download JSON
        </Button>
      </div>

      <div className="h-[420px] md:h-[520px]">
        <LeafletMap markerPosition={markerPosition} onMapClick={handleMapClick} isDroppingPin={isDroppingPin} drawingEnabled={false} />
      </div>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Point Probability of Exceedance (PoE)</CardTitle>
        </CardHeader>
        <CardContent>
          {poeMap ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div className="p-3 rounded border">
                <div className="font-semibold mb-2">PoE</div>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  {Object.entries(poeMap).map(([k, v]) => (
                    <div key={k} className="flex items-center justify-between p-2 rounded border">
                      <span className="font-mono">{k}</span>
                      <span className="tabular-nums">{Number(v).toFixed(2)}</span>
                    </div>
                  ))}
                </div>

                {/* Histograms per variable */}
                {Object.keys(hists).length > 0 && (
                  <div className="mt-4">
                    <div className="font-medium mb-2">Histograms</div>
                    <div className="grid grid-cols-2 gap-3">
                      {Object.entries(hists).map(([k, bins]) => (
                        <div key={k} className="p-2 border rounded">
                          <div className="text-xs mb-1 font-mono">{k}</div>
                          <div className="flex items-end h-16 gap-1">
                            {bins.map((val, i) => (
                              <div
                                key={i}
                                title={`${val}`}
                                style={{ height: `${Math.max(2, val * 100)}%` }}
                                className="w-2 bg-gray-400"
                              />
                            ))}
                          </div>
                          <div className="text-[10px] text-muted-foreground mt-1">
                            Bars show relative bin frequencies from the historical window.
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              <div className="p-3 rounded border">
                <div className="font-semibold mb-1">Notes</div>
                <pre className="text-xs whitespace-pre-wrap">{JSON.stringify(meta || {}, null, 2)}</pre>
              </div>
            </div>
          ) : (
            <div className="h-64 flex items-center justify-center bg-gray-100 rounded-md">
              <p className="text-muted-foreground">No PoE values found in response.</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
