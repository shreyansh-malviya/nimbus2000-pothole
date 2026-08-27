"use client";
import { MapContainer, TileLayer, Polyline, CircleMarker, Tooltip, useMap } from "react-leaflet";
import { useEffect, useMemo } from "react";
import type { SessionData, Severity } from "@/lib/types";
import { SEVERITY_COLOR } from "@/lib/constants";

interface Props {
  data: SessionData;
  severityFilter: Severity | "all";
  activeFrame: string | null;
  onSelect: (frame: string) => void;
}

const RANK: Record<Severity, number> = { shallow: 0, deep: 1, severe: 2 };
function worstSeverity(sevs: Severity[]): Severity {
  return sevs.reduce((w, s) => (RANK[s] > RANK[w] ? s : w), "shallow" as Severity);
}

function FitBounds({ data }: { data: SessionData }) {
  const map = useMap();
  useEffect(() => {
    const pts = data.path.map((p) => [p.lat, p.lon] as [number, number]);
    if (pts.length > 1) map.fitBounds(pts as any, { padding: [30, 30] });
    else if (pts.length === 1) map.setView(pts[0], 17);
  }, [data, map]);
  return null;
}

export function FlightMap({ data, severityFilter, activeFrame, onSelect }: Props) {
  const center = useMemo<[number, number]>(() => {
    const b = data.summary.area_bounds;
    if (!b || b.min_lat === undefined) return [12.84, 77.66];
    return [(b.min_lat + b.max_lat) / 2, (b.min_lon + b.max_lon) / 2];
  }, [data]);

  const line = data.path.map((p) => [p.lat, p.lon] as [number, number]);

  const markers = data.detections
    .filter((d) => d.potholes.length > 0 && d.gps)
    .map((d) => ({ d, worst: worstSeverity(d.potholes.map((p) => p.severity)), count: d.potholes.length }))
    .filter((m) => severityFilter === "all" || m.d.potholes.some((p) => p.severity === severityFilter));

  return (
    <div className="map-wrap">
      <MapContainer center={center} zoom={16} scrollWheelZoom className="leaflet-root">
        <TileLayer
          url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution="&copy; OpenStreetMap contributors"
          maxZoom={19}
          className="map-dark-tiles"
        />
        <FitBounds data={data} />

        {/* Dashed amber flight route (theme-consistent). */}
        <Polyline
          positions={line}
          pathOptions={{ color: "#ffc21f", weight: 2.5, opacity: 0.7, dashArray: "6 6" }}
        />

        {markers.map(({ d, worst, count }) => {
          const isActive = d.frame_id === activeFrame;
          return (
            <CircleMarker
              key={d.frame_id}
              center={[d.gps.lat, d.gps.lon]}
              radius={isActive ? 11 : 6 + Math.min(count - 1, 4)}
              pathOptions={{
                color: "#0d0d0f",
                weight: isActive ? 2.5 : 1.5,
                fillColor: SEVERITY_COLOR[worst],
                fillOpacity: 0.92,
              }}
              eventHandlers={{ click: () => onSelect(d.frame_id) }}
            >
              <Tooltip direction="top" offset={[0, -4]} opacity={1}>
                <div className="map-tip">
                  <strong>{d.frame_id}</strong>
                  <span>
                    {count} pothole{count > 1 ? "s" : ""} · worst {worst}
                  </span>
                  <span className="map-tip__gps">
                    {d.gps.lat.toFixed(5)}, {d.gps.lon.toFixed(5)}
                  </span>
                </div>
              </Tooltip>
            </CircleMarker>
          );
        })}
      </MapContainer>

      <div className="map-legend">
        <span className="map-legend__title">Path</span>
        <span className="map-legend__path" /> Flight route
        <span className="map-legend__sep" />
        {(["shallow", "deep", "severe"] as Severity[]).map((s) => (
          <span key={s} className="map-legend__item">
            <span className="map-legend__dot" style={{ background: SEVERITY_COLOR[s] }} />
            {s}
          </span>
        ))}
      </div>
    </div>
  );
}
