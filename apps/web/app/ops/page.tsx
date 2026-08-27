"use client";

import { useEffect, useState } from "react";
import { MapFrame } from "../../components/MapFrame";
import { TENANTS } from "../../lib/tenants";
import type { Cluster, TenantId } from "../../../../packages/schema/src";

export default function OpsPage() {
  const [tenant, setTenant] = useState<TenantId>("delhi_pwd");
  const [clusters, setClusters] = useState<Cluster[]>([]);
  const [selected, setSelected] = useState<Cluster | null>(null);
  const [note, setNote] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const t = TENANTS[tenant];

  useEffect(() => {
    fetch(`/api/clusters?tenant=${tenant}`)
      .then((r) => r.json())
      .then((d) => {
        const list = (d.clusters ?? []) as Cluster[];
        setClusters(list);
        setSelected(list[0] ?? null);
        setNote(list[0]?.tickets[0]?.ministry_note ?? null);
      });
  }, [tenant]);

  function pick(id: string) {
    const c = clusters.find((x) => x.id === id) ?? null;
    setSelected(c);
    setNote(c?.tickets[0]?.ministry_note ?? null);
  }

  async function elevate() {
    if (!selected) return;
    setBusy(true);
    try {
      const res = await fetch("/api/elevate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ cluster_id: selected.id }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Elevate failed");
      setNote(data.ministry_note);
      setSelected(data.cluster);
      const refresh = await fetch(`/api/clusters?tenant=${tenant}`).then((r) => r.json());
      setClusters(refresh.clusters ?? []);
    } catch (e) {
      setNote(e instanceof Error ? e.message : "Failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="page page-wide">
      <p className="kicker">Planning layer · Executive Engineer / plan cell</p>
      <h1>Ranked clusters, SQL first</h1>
      <div className="row" style={{ margin: "12px 0 16px" }}>
        <select value={tenant} onChange={(e) => setTenant(e.target.value as TenantId)}>
          <option value="delhi_pwd">PWD Delhi · 3 districts</option>
          <option value="rajasthan_pwd">PWD Rajasthan · Jaipur / Jodhpur / Barmer</option>
        </select>
      </div>
      <div className="split">
        <aside>
          <div className="banner">Score mode is partial until NFHS, OSM/PMGSY and MPLADS snapshots finish loading.</div>
          <div className="cluster-list">
            {clusters.length === 0 ? (
              <div className="card">
                No clusters on this tenant yet. Delhi and Rajasthan SAMPLE events
                should preload. Check the Python API is running.
              </div>
            ) : null}
            {clusters.map((c) => (
              <button
                key={c.id}
                className={`cluster-item ${selected?.id === c.id ? "active" : ""}`}
                onClick={() => pick(c.id)}
                type="button"
              >
                <div className="kicker">{c.type} · {c.district}</div>
                <div>
                  <span className="score">{c.score.priority_score.toFixed(2)}</span>
                  <span className="meta"> · {c.reporter_count} reporters · {c.score.mode}</span>
                </div>
              </button>
            ))}
          </div>
        </aside>
        <div>
          <MapFrame
            center={t.center}
            zoom={t.zoom}
            clusters={clusters}
            selectedId={selected?.id}
            onSelect={pick}
          />
          {selected ? (
            <section className="card" style={{ marginTop: 16 }}>
              <p className="kicker">Score drawer · Gemini does not invent this</p>
              <h2>
                {selected.type} · {selected.district}
              </h2>
              <p className="meta">
                Census 2011 vintage · {selected.reporter_count} SAMPLE reports · status {selected.status}
              </p>
              {selected.score.components.map((comp) => (
                <div key={comp.key}>
                  <div className="meta">
                    {comp.name} · weight {comp.weight} · {comp.used ? (comp.value ?? 0).toFixed(2) : "folded"}
                  </div>
                  <div className="bar">
                    <i style={{ width: `${Math.round((comp.used ? (comp.value ?? 0) : 0) * 100)}%` }} />
                  </div>
                  <div className="meta">{comp.note}</div>
                </div>
              ))}
              <div className="actions">
                <button className="btn terra" type="button" onClick={elevate} disabled={busy}>
                  {busy ? "Writing note…" : "Elevate to national shelf"}
                </button>
              </div>
              {note ? <div className="note" style={{ marginTop: 12 }}>{note}</div> : null}
            </section>
          ) : null}
        </div>
      </div>
    </main>
  );
}
