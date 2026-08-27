# Deploy NirmanGrid to Cloud Run

Do this in **Google Cloud Console** (Cloud Shell) or a local `gcloud` terminal.  
Project = `GCP_PROJECT` from `.env` (console.cloud.google.com), not AI Studio.

Two services go up:

- `nirmangrid-api` — Python engine (Gemini, score, SAMPLE data)
- `nirmangrid-web` — Next.js UI (the URL you give judges)

The Gemini key is a **Secret Manager** secret. It never goes in git.

## 1. One-time setup

```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  secretmanager.googleapis.com \
  containerregistry.googleapis.com \
  artifactregistry.googleapis.com
```

Create the secret from local `.env` **without printing the key**. PowerShell:

```powershell
$line = (Get-Content .env | Where-Object { $_ -like 'GEMINI_API_KEY=*' } | Select-Object -First 1)
$key = $line.Substring('GEMINI_API_KEY='.Length).Trim().Trim('"')
Set-Content -NoNewline -Path .gemini_secret.tmp -Value $key
gcloud secrets create GEMINI_API_KEY --data-file=.gemini_secret.tmp
Remove-Item .gemini_secret.tmp -Force
```

If the secret already exists:

```powershell
gcloud secrets versions add GEMINI_API_KEY --data-file=.gemini_secret.tmp
```

Let Cloud Run read it:

```bash
PROJECT_NUMBER=$(gcloud projects describe $(gcloud config get-value project) --format="value(projectNumber)")
gcloud secrets add-iam-policy-binding GEMINI_API_KEY \
  --member="serviceAccount:${PROJECT_NUMBER}-frank.g@example.org" \
  --role="roles/secretmanager.secretAccessor"
```

Let Cloud Build deploy Cloud Run:

```bash
PROJECT_NUMBER=$(gcloud projects describe $(gcloud config get-value project) --format="value(projectNumber)")
gcloud projects add-iam-policy-binding $(gcloud config get-value project) \
  --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
  --role="roles/run.admin"
gcloud projects add-iam-policy-binding $(gcloud config get-value project) \
  --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"
```

## 2. Build and deploy

From the repo root (after `git pull` so you have the latest Docker files):

```bash
gcloud builds submit --config infra/cloudbuild.yaml
```

First build is slow (Node image + Python image + ~40 MB of GeoJSON).

## 3. URLs

```bash
gcloud run services describe nirmangrid-web --region asia-south1 --format="value(status.url)"
gcloud run services describe nirmangrid-api --region asia-south1 --format="value(status.url)"
```

Open the **web** URL. `/api/health` should show `"engine": "python"` and `"gemini": true`.

Judges use the web URL only.

## If deploy fails

- Secret missing → step 1 create `GEMINI_API_KEY`
- Permission denied on Secret Manager → IAM binding on the Compute Engine default SA
- Cloud Build cannot deploy Run → `run.admin` + `iam.serviceAccountUser` on the Cloud Build SA
- UI loads but classify 502 → web `API_URL` must be the **api** service URL, no trailing slash
