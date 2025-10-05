// src/pages/Index.tsx
import { useState } from "react";
import Header from "@/components/weather/Header";
import Sidebar from "@/components/weather/Sidebar";
import EventCorridorView from "@/components/weather/EventCorridorView";
import PointPoeView from "@/components/weather/PointPoeView";
import { postPoe } from "@/api/endpoints";

type Thresholds = {
  precip_mm_day?: number;
  wind_mph?: number;
  rh_pct?: number;
  heatindex_F?: number;
};

const Index = () => {
  // left/right view toggle
  const [activeView, setActiveView] = useState<"corridor" | "poe">("poe");

  // shared point state
  const [lat, setLat] = useState("34.05");
  const [lon, setLon] = useState("-118.25");
  const [isDroppingPin, setIsDroppingPin] = useState(false);

  // PoE / Corridor controls (from Sidebar)
  const [poeDate, setPoeDate] = useState<string>(new Date().toISOString().slice(0, 10));
  const [poeWindowDays, setPoeWindowDays] = useState<number | string>(14);
  const [thresholds, setThresholds] = useState<Thresholds>({
    precip_mm_day: 10,
    wind_mph: 20,
    rh_pct: 80,
    heatindex_F: 95,
  });

  const setT = (k: keyof Thresholds) => (v: string) =>
    setThresholds((prev) => ({ ...prev, [k]: v === "" ? undefined : Number(v) }));

  // PoE results / UX
  const [out, setOut] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  // Backend call for PoE
  async function runPoe() {
    const latN = Number(lat);
    const lonN = Number(lon);
    if (!Number.isFinite(latN) || !Number.isFinite(lonN)) {
      setErr("Pick a valid point on the map first.");
      return;
    }
    if (!/^\d{4}-\d{2}-\d{2}$/.test(poeDate)) {
      setErr("Date must be YYYY-MM-DD.");
      return;
    }

    setErr(null);
    setLoading(true);
    try {
      const thr = {
        precip_mm_day: thresholds.precip_mm_day ?? 10,
        wind_mph: thresholds.wind_mph ?? 20,
        rh_pct: thresholds.rh_pct ?? 80,
        heatindex_F: thresholds.heatindex_F ?? 95,
      };
      // Some builds require metrics objects { var, threshold }
      const metrics = Object.entries(thr).map(([k, v]) => ({ var: k, threshold: Number(v) }));

      const resp = await postPoe({
        lat: latN,
        lon: lonN,
        date: poeDate,
        window_days: Number(poeWindowDays),
        thresholds: thr,
        // @ts-ignore allow metrics if server expects it
        metrics,
      } as any);

      setOut(resp);
      console.log("PoE response:", resp);
    } catch (e: any) {
      setErr(e.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-col md:flex-row h-screen bg-gray-50 font-sans text-sm text-gray-900">
      {/* LEFT: single Sidebar controlling all params */}
      <Sidebar
        activeView={activeView}
        setActiveView={(v) => setActiveView(v as any)}
        lat={lat}
        lon={lon}
        setLat={setLat}
        setLon={setLon}
        isDroppingPin={isDroppingPin}
        setIsDroppingPin={setIsDroppingPin}
        // PoE/Corridor controls
        poeDate={poeDate}
        onChangePoeDate={setPoeDate}
        poeWindowDays={poeWindowDays}
        onChangePoeWindowDays={setPoeWindowDays}
        thresholds={thresholds}
        onChangeThreshold={{
          precip_mm_day: setT("precip_mm_day"),
          wind_mph: setT("wind_mph"),
          rh_pct: setT("rh_pct"),
          heatindex_F: setT("heatindex_F"),
        }}
        onRun={runPoe}
        running={loading}
        errorMsg={err || undefined}
      />

      {/* RIGHT: header + view */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <Header />
        <main className="flex-1 overflow-y-auto p-4 md:p-6">
          {activeView === "corridor" ? (
            <EventCorridorView
              
              dateStr={poeDate}
              windowDays={Number(poeWindowDays) || 14}
              thresholds={thresholds}
            />
          ) : (
            <PointPoeView
              
              lat={lat}
              lon={lon}
              setLat={setLat}
              setLon={setLon}
              isDroppingPin={isDroppingPin}
              setIsDroppingPin={setIsDroppingPin}
              dateStr={poeDate}
              thresholds={thresholds}
              onRun={runPoe}
              loading={loading}
              out={out}
            />
          )}
        </main>
      </div>
    </div>
  );
};

export default Index;
