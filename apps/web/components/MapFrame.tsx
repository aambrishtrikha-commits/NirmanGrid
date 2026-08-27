"use client";

import dynamic from "next/dynamic";
import type { DemandMapProps } from "./DemandMap";

const DemandMap = dynamic(() => import("./DemandMap"), { ssr: false });

export function MapFrame(props: DemandMapProps) {
  return (
    <div className="map-wrap">
      <DemandMap {...props} />
    </div>
  );
}
