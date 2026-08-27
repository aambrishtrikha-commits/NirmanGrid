"use client";

import { MapContainer, TileLayer, CircleMarker, Popup, useMapEvents } from "react-leaflet";
import type { Cluster } from "../../../packages/schema/src";

export type DemandMapProps = {
  center: [number, number];
  zoom: number;
  clusters: Cluster[];
  selectedId?: string;
  onSelect?: (id: string) => void;
  onPick?: (lat: number, lng: number) => void;
  pick?: { lat: number; lng: number } | null;
};

function ClickCatch({ onPick }: { onPick?: (lat: number, lng: number) => void }) {
  useMapEvents({
    click(e) {
      onPick?.(e.latlng.lat, e.latlng.lng);
    },
  });
  return null;
}

export default function DemandMap({
  center,
  zoom,
  clusters,
  selectedId,
  onSelect,
  onPick,
  pick,
}: DemandMapProps) {
  return (
    <MapContainer center={center} zoom={zoom} scrollWheelZoom>
      <TileLayer
        attribution='&copy; OpenStreetMap contributors · ODbL'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      <ClickCatch onPick={onPick} />
      {clusters.map((c) => (
        <CircleMarker
          key={c.id}
          center={[c.lat, c.lng]}
          radius={Math.min(18, 7 + c.reporter_count)}
          pathOptions={{
            color: c.id === selectedId ? "#c45c26" : "#1b2a4a",
            fillColor: c.id === selectedId ? "#c45c26" : "#1f7a4d",
            fillOpacity: 0.7,
            weight: 2,
          }}
          eventHandlers={{ click: () => onSelect?.(c.id) }}
        >
          <Popup>
            <strong>{c.type}</strong> · {c.district}
            <br />
            {c.reporter_count} SAMPLE reports · score {c.score.priority_score}
            <br />
            mode: {c.score.mode}
          </Popup>
        </CircleMarker>
      ))}
      {pick ? (
        <CircleMarker
          center={[pick.lat, pick.lng]}
          radius={8}
          pathOptions={{ color: "#c45c26", fillColor: "#c45c26", fillOpacity: 1 }}
        />
      ) : null}
    </MapContainer>
  );
}
