# One-shot deploy from Windows. Does not print secrets.
$ErrorActionPreference = "Stop"
Set-Location (Resolve-Path "$PSScriptRoot\..")

$project = (gcloud config get-value project 2>$null)
if (-not $project -or $project -eq "(unset)") {
  throw "Run: gcloud config set project YOUR_PROJECT_ID"
}

Write-Host "Project: $project"
Write-Host "Submitting Cloud Build (API + web)..."
gcloud builds submit --config infra/cloudbuild.yaml
Write-Host "Web URL:"
gcloud run services describe nirmangrid-web --region asia-south1 --format="value(status.url)"
