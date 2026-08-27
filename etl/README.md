# ETL — Python, public data only

If a source is not in `NirmanGrid-Datasets.xlsx`, do not invent an API for it.

Score, classify plumbing, clustering and ETL live in Python (`apps/api`, `etl/`). The Next.js app is the citizen/ops UI.

```bash
python -m pip install -r apps/api/requirements.txt
python etl/generate_sample_events.py
python etl/01_boundaries.py
python etl/02_osm_delhi.py
python etl/03_osm_rajasthan.py
python etl/04_pmgsy_rajasthan.py
python -m pytest apps/api/tests
```

`02_osm_delhi.py` uses Overpass unless `data/raw/NewDelhi.osm.pbf` is present (BBBike extract). OSM is not a PWD inventory. Attribute ODbL.

Do not scrape personal PWD Sewa complaints. Do not fake Gati Shakti.
