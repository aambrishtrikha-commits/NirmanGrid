# ETL — public data only

If a source is not in `NirmanGrid-Datasets.xlsx`, do not invent an API for it.

## Week 1

Delhi SAMPLE events are generated in `apps/web/lib/sampleEvents.ts` and loaded into memory on boot. Every row is `source=SAMPLE`.

Next loads, in this order:

1. `01_boundaries` — Datameet district + PC GeoJSON, filter NCT of Delhi and Rajasthan.
2. `02_osm_delhi` — BBBike NewDelhi extract → `data/clean/delhi_highways.geojson` with `highway=*`.
3. Census 2011 PCA for the six demo districts, join on LGD.
4. PWD Sewa public category totals snapshot (no ticket dump).
5. Rajasthan highways + PMGSY (week 2).

Do not scrape personal PWD Sewa complaints. Do not fake Gati Shakti.
