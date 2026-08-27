"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { MapFrame } from "../../components/MapFrame";
import { TENANTS } from "../../lib/tenants";
import type { Cluster, TenantId } from "../../../../packages/schema/src";

export default function CitizenPage() {
  const [tenant, setTenant] = useState<TenantId>("delhi_pwd");
  const [clusters, setClusters] = useState<Cluster[]>([]);
  const [text, setText] = useState("");
  const [photo, setPhoto] = useState<{ mimeType: string; base64: string } | null>(null);
  const [audio, setAudio] = useState<{ mimeType: string; base64: string } | null>(null);
  const [recording, setRecording] = useState(false);
  const [pick, setPick] = useState<{ lat: number; lng: number } | null>(null);
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<unknown>(null);
  const [error, setError] = useState<string | null>(null);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const t = TENANTS[tenant];

  useEffect(() => {
    fetch(`/api/clusters?tenant=${tenant}`)
      .then((r) => r.json())
      .then((d) => setClusters(d.clusters ?? []));
  }, [tenant]);

  function onFile(file: File | undefined) {
    if (!file) return setPhoto(null);
    const reader = new FileReader();
    reader.onload = () => {
      const url = String(reader.result || "");
      const base64 = url.split(",")[1] || "";
      setPhoto({ mimeType: file.type || "image/jpeg", base64 });
    };
    reader.readAsDataURL(file);
  }

  async function toggleRecord() {
    if (recording && recorderRef.current) {
      recorderRef.current.stop();
      setRecording(false);
      return;
    }
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const rec = new MediaRecorder(stream);
    chunksRef.current = [];
    rec.ondataavailable = (e) => {
      if (e.data.size) chunksRef.current.push(e.data);
    };
    rec.onstop = async () => {
      stream.getTracks().forEach((tr) => tr.stop());
      const blob = new Blob(chunksRef.current, { type: rec.mimeType || "audio/webm" });
      const buf = await blob.arrayBuffer();
      let binary = "";
      const bytes = new Uint8Array(buf);
      for (let i = 0; i < bytes.length; i += 1) binary += String.fromCharCode(bytes[i]);
      setAudio({
        mimeType: blob.type || "audio/webm",
        base64: btoa(binary),
      });
    };
    recorderRef.current = rec;
    rec.start();
    setRecording(true);
  }

  function useMyLocation() {
    navigator.geolocation.getCurrentPosition(
      (pos) => setPick({ lat: pos.coords.latitude, lng: pos.coords.longitude }),
      () => setPick({ lat: t.center[0], lng: t.center[1] }),
    );
  }

  async function submit() {
    setBusy(true);
    setError(null);
    setResult(null);
    try {
      if (!pick) throw new Error("Drop a pin on the map first.");
      const res = await fetch("/api/ingest", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          tenant_id: tenant,
          lat: pick.lat,
          lng: pick.lng,
          text,
          photo,
          audio,
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Ingest failed");
      setResult(data);
      const refresh = await fetch(`/api/clusters?tenant=${tenant}`).then((r) => r.json());
      setClusters(refresh.clusters ?? []);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed");
    } finally {
      setBusy(false);
    }
  }

  const center = useMemo(() => t.center, [t]);

  return (
    <main className="page page-wide">
      <p className="kicker">Field layer · web stand-in for WhatsApp</p>
      <h1>File a development need</h1>
      <p className="lede">
        Photo + pin + text or a Hindi/Marwari voice note. Gemini classifies.
        It does not return a priority score. Rajasthani voice falls back to
        Hindi STT + Gemini, confidence labelled.
      </p>
      <div className="split" style={{ marginTop: 18 }}>
        <section className="card">
          <div className="banner">
            Pins you see already are SAMPLE events, calibrated to published PWD
            Sewa category mix. They are not real complainants.
          </div>
          <label>Tenant</label>
          <select value={tenant} onChange={(e) => setTenant(e.target.value as TenantId)}>
            <option value="delhi_pwd">PWD Delhi</option>
            <option value="rajasthan_pwd">PWD Rajasthan</option>
          </select>
          <label>What is broken?</label>
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="हिंदी, English, या मारवाड़ी. Barmer: पुलिया टूटी"
          />
          <label>Photo</label>
          <input type="file" accept="image/*" onChange={(e) => onFile(e.target.files?.[0])} />
          <label>Voice note</label>
          <div className="row">
            <button className="btn secondary" type="button" onClick={() => void toggleRecord()}>
              {recording ? "Stop recording" : "Record Hindi / Marwari"}
            </button>
            <span className="meta">{audio ? "voice attached" : "optional"}</span>
          </div>
          <div className="row" style={{ marginTop: 12 }}>
            <button className="btn secondary" type="button" onClick={useMyLocation}>
              Use my location
            </button>
            <button className="btn terra" type="button" onClick={submit} disabled={busy}>
              {busy ? "Classifying…" : "Submit"}
            </button>
          </div>
          <p className="meta" style={{ marginTop: 10 }}>
            Pin: {pick ? `${pick.lat.toFixed(5)}, ${pick.lng.toFixed(5)}` : "click the map"}
            {" · "}SLA {t.slaHours}h
          </p>
          {error ? <p className="banner">{error}</p> : null}
          {result ? <pre className="json">{JSON.stringify(result, null, 2)}</pre> : null}
        </section>
        <MapFrame
          center={center}
          zoom={t.zoom}
          clusters={clusters}
          pick={pick}
          onPick={(lat, lng) => setPick({ lat, lng })}
        />
      </div>
    </main>
  );
}
