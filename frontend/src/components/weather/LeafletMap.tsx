// src/components/weather/LeafletMap.tsx
import { MapContainer, TileLayer, Marker, CircleMarker, useMap } from "react-leaflet";
import L, { FeatureGroup as LFeatureGroup, LatLng, Polyline } from "leaflet";
import { useEffect, useRef, useCallback } from "react";
import "leaflet/dist/leaflet.css";
import "leaflet-draw"; // augments L with Draw
import "leaflet-draw/dist/leaflet.draw.css";

// Fix default marker icons (Vite bundling)
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
});

type EVSPoint = { lat: number; lon: number; value: number };

type RoutesChange = {
  lines: GeoJSON.LineString[];
  midpoints: [number, number][];
};

interface LeafletMapProps {
  markerPosition?: [number, number] | null;
  onMapClick?: (latlng: L.LatLng) => void;
  isDroppingPin?: boolean;
  drawingEnabled?: boolean;

  /** NEW: Fired whenever routes change (create/edit/delete). */
  onRoutesChange?: (e: RoutesChange) => void;

  /** Back-compat: fired only for the most recent created geometry. */
  onDraw?: (geom: GeoJSON.LineString | GeoJSON.Polygon) => void;

  points?: EVSPoint[];
  center?: [number, number];
  zoom?: number;
}

export default function LeafletMap({
  markerPosition,
  onMapClick,
  isDroppingPin = false,
  drawingEnabled = false,
  onRoutesChange,
  onDraw,
  points = [],
  center = [34.05, -118.25],
  zoom = 12,
}: LeafletMapProps) {
  const fgRef = useRef<LFeatureGroup | null>(null);

  // color scale for EVS dots
  const colorFor = (v: number) => {
    const h = Math.max(0, Math.min(120, (v / 100) * 120)); // 0 red -> 120 green
    return `hsl(${h} 80% 45%)`;
  };

  // recompute all lines + midpoints and notify parent
  const emitRoutes = useCallback(() => {
    if (!fgRef.current || !onRoutesChange) return;
    const lines: GeoJSON.LineString[] = [];
    const mids: [number, number][] = [];

    fgRef.current.eachLayer((layer) => {
      if (layer instanceof Polyline) {
        const latlngs = layer.getLatLngs() as LatLng[];
        if (latlngs.length >= 2) {
          const gj = (layer as any).toGeoJSON() as GeoJSON.Feature<GeoJSON.LineString>;
          if (gj?.geometry) lines.push(gj.geometry);
          mids.push(...segmentMidpoints(latlngs));
        }
      }
    });

    onRoutesChange({ lines, midpoints: mids });
  }, [onRoutesChange]);

  return (
    <div className={`h-full w-full rounded-lg overflow-hidden border ${isDroppingPin ? "cursor-crosshair" : ""}`}>
      <MapContainer center={center} zoom={zoom} scrollWheelZoom style={{ height: "100%", width: "100%" }}>
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution="&copy; OpenStreetMap contributors"
        />

        {/* Draw toolbar + persistence */}
        {drawingEnabled && <DrawControl featureGroupRef={fgRef} onAnyChange={emitRoutes} onCreatedGeom={onDraw} />}

        {/* Click-to-drop-pin */}
        {isDroppingPin && <MapClickHandler onClick={onMapClick} />}

        {/* EVS overlay */}
        {points.map((p, i) => (
          <CircleMarker
            key={i}
            center={[p.lat, p.lon]}
            radius={6}
            pathOptions={{ color: colorFor(p.value), fillColor: colorFor(p.value), fillOpacity: 0.9, weight: 1 }}
          />
        ))}

        {markerPosition && <Marker position={markerPosition} />}
      </MapContainer>
    </div>
  );
}

/** Mount Leaflet.draw toolbars and wire them to a persistent FeatureGroup. */
function DrawControl({
  featureGroupRef,
  onAnyChange,
  onCreatedGeom,
}: {
  featureGroupRef: React.MutableRefObject<LFeatureGroup | null>;
  onAnyChange?: () => void;
  onCreatedGeom?: (geom: GeoJSON.LineString | GeoJSON.Polygon) => void;
}) {
  const map = useMap();

  useEffect(() => {
    if (!map) return;

    // persistent group that holds all user-drawn layers
    const fg = featureGroupRef.current ?? new L.FeatureGroup();
    if (!featureGroupRef.current) {
      featureGroupRef.current = fg;
      map.addLayer(fg);
    }

    // ROUTE-ONLY drawing: allow polylines; disable polygons/markers
    const drawControl = new (L as any).Control.Draw({
      edit: { featureGroup: fg, remove: true },
      draw: {
        polyline: true,
        polygon: false,
        rectangle: false,
        circle: false,
        circlemarker: false,
        marker: false,
      },
      position: "topright",
    });
    map.addControl(drawControl);

    function handleCreated(e: any) {
      const layer = e.layer as L.Layer;
      // persist this layer in the FG so it doesn't "disappear"
      fg.addLayer(layer);

      // Back-compat single-geom callback
      const gj = (layer as any).toGeoJSON() as GeoJSON.Feature;
      if (gj?.geometry && (gj.geometry.type === "LineString" || gj.geometry.type === "Polygon")) {
        onCreatedGeom?.(gj.geometry as any);
      }

      onAnyChange?.();
    }
    function handleEdited() { onAnyChange?.(); }
    function handleDeleted() { onAnyChange?.(); }

    map.on((L as any).Draw.Event.CREATED, handleCreated);
    map.on((L as any).Draw.Event.EDITED, handleEdited);
    map.on((L as any).Draw.Event.DELETED, handleDeleted);

    return () => {
      map.off((L as any).Draw.Event.CREATED, handleCreated);
      map.off((L as any).Draw.Event.EDITED, handleEdited);
      map.off((L as any).Draw.Event.DELETED, handleDeleted);
      map.removeControl(drawControl);
      // keep the FG so shapes persist across re-renders; remove if you want cleanup:
      // map.removeLayer(fg);
    };
  }, [map, featureGroupRef, onAnyChange, onCreatedGeom]);

  return null;
}

function MapClickHandler({ onClick }: { onClick?: (ll: L.LatLng) => void }) {
  const map = useMap();

  useEffect(() => {
    if (!onClick) return;

    const handler = (e: L.LeafletMouseEvent) => onClick(e.latlng);

    map.on("click", handler);
    return () => {
      map.off("click", handler);
    };
  }, [map, onClick]);

  return null;
}

function segmentMidpoints(latlngs: L.LatLng[], minLenMeters = 5): [number, number][] {
  const mids: [number, number][] = [];
  for (let i = 1; i < latlngs.length; i++) {
    const a = latlngs[i - 1];
    const b = latlngs[i];
    if (a.equals(b)) continue;
    const d = a.distanceTo(b);
    if (d < minLenMeters) continue; // skip tiny segments (optional)
    const lat = (a.lat + b.lat) / 2;
    const lon = (a.lng + b.lng) / 2;
    mids.push([Number(lat.toFixed(6)), Number(lon.toFixed(6))]);
  }
  return mids;
}


/** Distance-weighted midpoint along a polyline */
function midpointOnLine(latlngs: LatLng[]): [number, number] {
  const d: number[] = [0];
  for (let i = 1; i < latlngs.length; i++) d[i] = d[i - 1] + latlngs[i - 1].distanceTo(latlngs[i]);
  const half = d[d.length - 1] / 2;
  for (let i = 1; i < latlngs.length; i++) {
    if (d[i] >= half) {
      const seg = d[i] - d[i - 1] || 1;
      const t = (half - d[i - 1]) / seg;
      const a = latlngs[i - 1], b = latlngs[i];
      const lat = a.lat + t * (b.lat - a.lat);
      const lon = a.lng + t * (b.lng - a.lng);
      return [Number(lat.toFixed(6)), Number(lon.toFixed(6))];
    }
  }
  const last = latlngs[latlngs.length - 1];
  return [Number(last.lat.toFixed(6)), Number(last.lng.toFixed(6))];
}
