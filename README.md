# NirmanGrid

Citizens speak a development need in their language. The system ranks that need against what India is already funded to build.

Track 1 — AI for Digital Public Infrastructure & Governance  
Google Cloud · Build with AI: Code for Communities — Second Edition  
AppD AI · submission window ends 30 Sep 2026

## What this is

A Digital Public Good with three layers:

1. **Field** — WhatsApp / web intake. Photo, pin, voice. Gemini classifies. Ticket in under a minute.
2. **Planning** — clusters scored on Census, OSM/PMGSY gap, MPLADS/PMGSY money already present, NFHS, rain.
3. **National** — Delhi PWD + Rajasthan PWD, one protocol, ranked shelf, 12-line ministry note.

If the planning or national layer is missing, this is last year's product.

## Current contents

| File | Role |
|------|------|
| `NirmanGrid-Production-Bible.docx` | Build spec. If a feature is not in here, it is out of scope. |
| `NirmanGrid-Datasets.xlsx` | Only allowed data list. Do not invent an API for a source that is not listed. |
| `NirmanGrid-Pitch.pptx` | Ten-slide pitch. |

Week 1 code is in this repo: citizen form, Gemini classify, SQL score, ops map, national shelf, 60 Delhi SAMPLE events.

## Intended layout

```
apps/web          Next.js citizen + ops
apps/api          ingest, classify, score, notify
packages/schema   ticket, cluster, score, tenant schemas
data/raw          dated public downloads, never PII
data/clean        loadable parquet / geojson / csv
data/sample       events.csv with source=SAMPLE
etl/              download and transform scripts
prompts/          classify.md, ministry_note.md
infra/            Cloud Run Dockerfile, cloudbuild.yaml
docs/             demo script and supporting notes
```

## What we will not claim

- Signed PWD contract or production SLA
- Live PM Gati Shakti or eSAKSHI write-access
- Real complainant PII (citizen events are stamped `SAMPLE`)
- Census 2011 passed off as 2026
- WCD / AHD features bolted onto this product

## Dataset honesty

Every planning-layer source is listed in `NirmanGrid-Datasets.xlsx` with an `Access_Reality` flag:

- `LIVE_PUBLIC` — downloadable now
- `PORTAL_ONLY` — published page, no bulk API; dated snapshot only
- `NO_PUBLIC_API` — do not claim as integrated
- `SYNTHETIC_LABELED` — generated events, every row stamped `SAMPLE`

Cite OSM (ODbL), Datameet (CC BY 4.0), MoRD, MoSPI, and ORGI where used.

## Google AI

Classify and the ministry note must hit Gemini on the live URL. Score is SQL, not a chat. If Gemini and SQL disagree, SQL wins.

## Local setup

Python is the planning engine. Next.js is the UI. You need Python 3.12, Node 22+, and a Gemini API key. Cloud Run is the only production step you run.

```bash
copy .env.example .env
# fill GEMINI_API_KEY  (required for classify + ministry note)

python -m pip install -r apps/api/requirements.txt
python etl/generate_sample_events.py
python -m pytest apps/api/tests
python -m uvicorn nirmangrid.main:app --app-dir apps/api --reload --port 8000

npm install --prefix apps/web
npm run dev
```

Open http://127.0.0.1:3000

- `/citizen` — photo + pin + text. Gemini classifies. No priority_score in that JSON.
- `/ops` — Delhi SAMPLE clusters, SQL score drawer, elevate.
- `/national` — ranked shelf across tenants.
- `/api/health` — proxied to the Python API (`engine: python`, SAMPLE events)

Without `GEMINI_API_KEY`, the map and scores still run. Filing a live report or elevating returns 503. We do not stub Gemini.

### What you deploy

Two Cloud Run services in **console.cloud.google.com** (same `GCP_PROJECT`). Full steps: `docs/DEPLOY.md`.

```bash
gcloud builds submit --config infra/cloudbuild.yaml
```

Create Secret Manager secret `GEMINI_API_KEY` first. Do not put the key in git.

## Licence

Code: MIT (see `LICENSE`).  
Data: Government Open Data License — India / CC-BY / ODbL as labelled per source.
