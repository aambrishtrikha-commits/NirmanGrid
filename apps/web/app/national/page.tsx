"use client";

import { useEffect, useState } from "react";
import type { Cluster } from "../../../../packages/schema/src";

export default function NationalPage() {
  const [clusters, setClusters] = useState<Cluster[]>([]);

  useEffect(() => {
    fetch("/api/clusters")
      .then((r) => r.json())
      .then((d) => setClusters(d.clusters ?? []));
  }, []);

  return (
    <main className="page">
      <p className="kicker">National layer · MoHUA / MoRTH / NITI-style view</p>
      <h1>Ranked shelf across tenants</h1>
      <p className="lede">
        Same classify → snap → cluster → score → elevate protocol. Delhi and
        Rajasthan are a union query, not two bots. A third state is a boundary
        file and a language pack.
      </p>
      <div className="grid-2" style={{ marginTop: 18 }}>
        {clusters.map((c, i) => (
          <article className="card" key={c.id}>
            <p className="kicker">#{i + 1} · {c.tenant_id} · {c.score.mode}</p>
            <h2>
              {c.type} · {c.district}
            </h2>
            <p className="score">{c.score.priority_score.toFixed(2)}</p>
            <p className="meta">
              {c.reporter_count} SAMPLE reports · Census 2011 labelled · {c.status}
            </p>
            {c.tickets[0]?.ministry_note ? (
              <pre className="note">{c.tickets[0].ministry_note}</pre>
            ) : (
              <p className="meta">Not yet elevated. Do that from the planning desk.</p>
            )}
          </article>
        ))}
      </div>
    </main>
  );
}
