// src/components/weather/EventCorridorView.tsx
import { useCallback, useMemo, useState } from "react";
import LeafletMap from "./LeafletMap";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { postPoe } from "@/api/endpoints";
import { normalizeThresholds, PoeThresholds } from "@/lib/thresholds";

type EvsPoint = { lat: number; lon: number; value: number };

// ---- helpers to normalize backend shapes ---------------------------------

function extractPoeMap(out: any): Record<string, number> | null {
  if (!out) return null;
  const res = out?.data ?? out?.result ?? out;
  if (res?.poe && typeof res.poe === "object") return res.poe;
  if (res?.results && typeof res.results === "object" && !Array.isArray(res.results)) {
    const acc: Record<string, number> = {};
    for (const [k, v] of Object.entries(res.results)) {
      const val = (v as any)?.poe;
      if (typeof val === "number") acc[k] = val;
    }
    return Object.keys(acc).length ? acc : null;
  }
  return null;
}

type HistData = { bins: number[]; pdf: number[] };

function extractHistForVar(out: any, k: string): HistData | null {
  const res = out?.data ?? out?.result ?? out;
  const obj = res?.results?.[k];
  if (!obj) return null;

  // New-style { hist: { bins, pdf } }
  if (obj?.hist && Array.isArray(obj.hist.bins) && Array.isArray(obj.hist.pdf)) {
    return { bins: obj.hist.bins as number[], pdf: obj.hist.pdf as number[] };
  }

  // Legacy array hist (no bins)
  if (Array.isArray(obj.hist)) {
    const arr = obj.hist as number[];
    return { bins: Array.from({ length: arr.length }, (_, i) => i), pdf: arr };
  }

  // Legacy stats.hist (+ optional stats.bins)
  if (obj?.stats && Array.isArray(obj.stats.hist)) {
    const pdf = obj.stats.hist as number[];
    const maybeBins = Array.isArray(obj.stats.bins)
      ? (obj.stats.bins as number[])
      : Array.from({ length: pdf.length }, (_, i) => i);
    return { bins: maybeBins, pdf };
  }
  return null;
}

function toCSV(rows: (string | number)[][]): string {
  return rows
    .map((r) =>
      r
        .map((c) => {
          const s = String(c ?? "");
          return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
        })
        .join(",")
    )
    .join("\n");
}

function downloadBlob(data: string, filename: string, type = "text/plain") {
  const blob = new Blob([data], { type });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = filename;
  a.click();
  URL.revokeObjectURL(a.href);
}

// Ensure we only send YYYY-MM-DD (UTC) to the climo endpoint
function toDateOnlyUTC(input: string): string {
  const d = new Date(input);
  if (isNaN(d.getTime())) return input; // already "YYYY-MM-DD"
  return new Date(Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), d.getUTCDate()))
    .toISOString()
    .slice(0, 10);
}

// ---- component ------------------------------------------------------------

export default function EventCorridorView({
  dateStr,
  windowDays,
  thresholds,
}: {
  dateStr: string;
  windowDays: number;
  thresholds: Partial<PoeThresholds>; // allow partials from UI
}) {
  // drawing → segment midpoints
  const [midpoints, setMidpoints] = useState<[number, number][]>([]);

  // results
  const [avgPoe, setAvgPoe] = useState<Record<string, number> | null>(null);
  const [avgHists, setAvgHists] = useState<Record<string, HistData>>({});
  const [pointEvs, setPointEvs] = useState<EvsPoint[]>([]);
  const [evsOverall, setEvsOverall] = useState<number | null>(null);
  const [running, setRunning] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [rawPointResults, setRawPointResults] = useState<any[]>([]);

  const keysShown = useMemo(() => {
    if (!avgPoe) return [];
    return Object.keys(avgPoe);
  }, [avgPoe]);

  const run = useCallback(async () => {
    setErr(null);
    setRunning(true);
    try {
      if (!midpoints.length) {
        setErr("Draw at least one route (with one or more segments).");
        setRunning(false);
        return;
      }

      const th = normalizeThresholds(thresholds);

      // call backend for each segment midpoint
      const results = await Promise.all(
        midpoints.map(([lat, lon]) =>
          postPoe({
            date: toDateOnlyUTC(dateStr),
            window_days: windowDays,
            lat,
            lon,
            thresholds: th,           // <- normalized, complete numbers
            mode: "climo",            // for reanalysis sub-daily, pass full datetime instead
          })
        )
      );

      setRawPointResults(results);

      // average PoE across points
      const maps = results.map(extractPoeMap).filter(Boolean) as Record<string, number>[];
      const keys = new Set<string>(maps.flatMap((m) => Object.keys(m)));
      const avg: Record<string, number> = {};
      keys.forEach((k) => {
        let sum = 0, n = 0;
        maps.forEach((m) => {
          if (typeof m[k] === "number") {
            sum += m[k];
            n++;
          }
        });
        if (n) avg[k] = sum / n;
      });

      // per-point EVS for markers
      const points: EvsPoint[] = results.map((r, i) => {
        const poe = extractPoeMap(r) || {};
        const subs = Object.values(poe).map((p) => 100 * (1 - (p as number)));
        const evs = subs.length ? subs.reduce((a, b) => a + b, 0) / subs.length : 0;
        return { lat: midpoints[i][0], lon: midpoints[i][1], value: Number(evs.toFixed(1)) };
      });

      // average histograms element-wise where lengths and bins match
      const histAcc: Record<string, { bins: number[]; pdf: number[] }> = {};
      const histCount: Record<string, number> = {};

      Array.from(keys).forEach((k) => {
        // Use first available histogram as template
        let template: HistData | null = null;
        for (const r of results) {
          const h = extractHistForVar(r, k);
          if (h && Array.isArray(h.pdf) && h.pdf.length) {
            template = { bins: h.bins.slice(), pdf: h.pdf.slice() };
            break;
          }
        }
        if (!template) return;

        histAcc[k] = { bins: template.bins.slice(), pdf: new Array(template.pdf.length).fill(0) };
        histCount[k] = 0;

        for (const r of results) {
          const h = extractHistForVar(r, k);
          if (
            h &&
            h.pdf.length === template.pdf.length &&
            h.bins.length === template.bins.length &&
            h.bins.every((b, i) => b === template!.bins[i])
          ) {
            for (let i = 0; i < h.pdf.length; i++) {
              histAcc[k].pdf[i] += h.pdf[i];
            }
            histCount[k]++;
          }
        }

        if (histCount[k] > 0) {
          for (let i = 0; i < histAcc[k].pdf.length; i++) {
            histAcc[k].pdf[i] /= histCount[k];
          }
        }
      });

      setAvgHists(histAcc);
      setPointEvs(points);
      setAvgPoe(Object.keys(avg).length ? avg : null);

      // overall EVS (average of point EVS)
      const overall =
        points.length > 0 ? Number((points.reduce((a, b) => a + b.value, 0) / points.length).toFixed(1)) : null;
      setEvsOverall(overall);
    } catch (e: any) {
      setErr(e?.message || "Failed to run corridor.");
    } finally {
      setRunning(false);
    }
  }, [midpoints, dateStr, windowDays, thresholds]);

  // ---- downloads ----------------------------------------------------------

  function downloadCSV() {
    if (!rawPointResults.length) return;

    const poeKeys = new Set<string>();
    rawPointResults.forEach((r) => {
      const m = extractPoeMap(r);
      if (m) Object.keys(m).forEach((k) => poeKeys.add(k));
    });
    const keys = Array.from(poeKeys);

    const header = ["lat", "lon", ...keys.map((k) => `poe.${k}`), "evs"];
    const rows: (string | number)[][] = [header];

    rawPointResults.forEach((r, i) => {
      const m = extractPoeMap(r) || {};
      const subs = Object.values(m).map((p: any) => 100 * (1 - Number(p)));
      const evs = subs.length ? subs.reduce((a, b) => a + b, 0) / subs.length : 0;
      const [lat, lon] = [pointEvs[i]?.lat ?? "", pointEvs[i]?.lon ?? ""];
      rows.push([lat, lon, ...keys.map((k) => m[k] ?? ""), Number(evs.toFixed(2))]);
    });

    if (avgPoe) rows.push(["AVERAGE", "", ...keys.map((k) => avgPoe[k] ?? ""), ""]);

    downloadBlob(toCSV(rows), `corridor_route_${dateStr}_window${windowDays}.csv`, "text/csv");
  }

  function downloadAvgHistsCSV() {
    if (!avgHists || Object.keys(avgHists).length === 0) return;
    const rows: (string | number)[][] = [];
    for (const [k, v] of Object.entries(avgHists)) {
      const bins = v.bins;
      const pdf = v.pdf;
      rows.push([k, "bin_start", "bin_end", "pdf"]);
      for (let i = 0; i < pdf.length; i++) {
        const start = bins[i] ?? "";
        const end = bins[i + 1] ?? "";
        rows.push([k, start, end, Number(pdf[i].toFixed(6))]);
      }
      rows.push([]);
    }
    downloadBlob(
      toCSV(rows),
      `corridor_route_${dateStr}_window${windowDays}_avg_hists.csv`,
      "text/csv"
    );
  }

  // ---- UI -----------------------------------------------------------------

  return (
    <div className="space-y-4">
      {/* ACTIONS */}
      <div className="flex flex-wrap gap-2 items-center">
        <Button onClick={run} disabled={running || midpoints.length === 0}>
          {running ? "Running..." : "Run Corridor (Route)"}
        </Button>
        <Button variant="outline" onClick={downloadCSV} disabled={!rawPointResults.length}>
          Download CSV
        </Button>
        <Button variant="outline" onClick={downloadAvgHistsCSV} disabled={!Object.keys(avgHists).length}>
          Download Hists CSV
        </Button>
        {err && <span className="text-red-600 ml-3">{err}</span>}
      </div>

      {/* MAP */}
      <div className="h-[420px] md:h-[520px]">
        <LeafletMap
          drawingEnabled
          onRoutesChange={({ midpoints }) => setMidpoints(midpoints)}
          points={pointEvs} // shows dots per segment midpoint after Run
        />
      </div>

      {/* RESULTS */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader>
            <CardTitle>Route EVS</CardTitle>
          </CardHeader>
          <CardContent>
            {evsOverall !== null ? (
              <div className="text-3xl font-semibold">{evsOverall}</div>
            ) : (
              <div className="text-muted-foreground">Draw routes and run to see EVS.</div>
            )}
            <p className="text-xs text-muted-foreground mt-2">
              EVS is 100×(1−PoE) averaged over variables, then averaged across each route.
            </p>
          </CardContent>
        </Card>

        <Card className="md:col-span-2">
          <CardHeader>
            <CardTitle>Probability of Exceedance (PoE)</CardTitle>
          </CardHeader>
          <CardContent>
            {avgPoe ? (
              <>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  {Object.entries(avgPoe).map(([k, v]) => (
                    <div key={k} className="p-2 border rounded">
                      <div className="text-xs text-muted-foreground">{k}</div>
                      <div className="text-xl font-semibold">{(100 * v).toFixed(1)}%</div>
                    </div>
                  ))}
                </div>

                {!!Object.keys(avgHists).length && (
                  <div className="mt-4">
                    <div className="font-medium mb-2">Average Histograms</div>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                      {Object.entries(avgHists).map(([k, { bins, pdf }]) => (
                        <div key={k} className="p-3 border rounded">
                          <div className="text-xs mb-2 font-mono">{k}</div>
                          {/* bars */}
                          <div className="flex items-end gap-1 h-28">
                            {pdf.map((v, i) => (
                              <div
                                key={i}
                                className="bg-gray-400 rounded-sm"
                                title={`bin ${i}: ${bins[i]} → ${bins[i + 1] ?? '+'}\nprob ~ ${v.toFixed(3)}`}
                                style={{
                                  width: `${Math.max(6, 100 / Math.max(12, pdf.length))}%`,
                                  height: `${Math.max(2, v * 100)}%`,
                                  minHeight: 2,
                                }}
                              />
                            ))}
                          </div>
                          {/* x-axis labels (sparse) */}
                          <div className="mt-2 flex text-[10px] text-muted-foreground justify-between">
                            <span>{bins[0] ?? ""}</span>
                            <span>{bins[Math.floor(bins.length / 2)] ?? ""}</span>
                            <span>{bins[bins.length - 1] ?? ""}</span>
                          </div>
                          <div className="text-[10px] text-muted-foreground mt-1">
                            Bars show averaged bin probabilities (pdf).
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </>
            ) : (
              <div className="text-muted-foreground">No PoE yet.</div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Notes</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="list-disc list-inside space-y-1">
              <li>Route: each sampled <strong>per segment</strong> of each drawn line.</li>
              <li>PoE based on NASA POWER daily climatology (±window around {dateStr}).</li>
              <li>
                Thresholds: precip {thresholds?.precip_mm_day ?? 10} mm/day, wind {thresholds?.wind_mph ?? 20} mph,
                RH {thresholds?.rh_pct ?? 80}%, HI {thresholds?.heatindex_F ?? 90}°F.
              </li>
            </ul>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
