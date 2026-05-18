#!/usr/bin/env pwsh
# Docker-Compose preview: brings up Postgres + Redis + API + Worker + Web + Caddy,
# applies migrations, seeds the database, and prints credentials.
#
# Requires: Docker Desktop. Run from the repo root.

$ErrorActionPreference = "Stop"
$Root  = Resolve-Path "$PSScriptRoot\.."
$Infra = Join-Path $Root "infra"

Write-Host "CustomerFlow AI preview (Docker Compose)" -ForegroundColor Cyan
Write-Host "================================="

if (-not (Test-Path "$Infra\.env")) {
    Write-Host "`nNo $Infra\.env found — creating one from .env.example with preview defaults..." -ForegroundColor Yellow
    $env_template = @"
ENVIRONMENT=development
DATABASE_URL=postgresql+asyncpg://customerflow:customerflow_pw@postgres:5432/customerflow_ai
REDIS_URL=redis://:redispw@redis:6379/0
POSTGRES_PASSWORD=customerflow_pw
REDIS_PASSWORD=redispw
JWT_SECRET=preview_jwt_secret_not_for_production_use_aaaaaaaaaaaaaaaaaa
JWT_REFRESH_SECRET=preview_refresh_secret_not_for_production_use_bbbbbbb
ALLOWED_ORIGINS=http://localhost:3000
FRONTEND_URL=http://localhost:3000
COOKIE_SECURE=false
COOKIE_SAMESITE=lax
SMS_PROVIDER=mock
EMAIL_PROVIDER=mock
PAYMENT_PROVIDER=mock
AI_PROVIDER=mock
SOCIAL_PROVIDER=mock
"@
    $env_template | Out-File "$Infra\.env" -Encoding utf8
}

Push-Location $Infra

Write-Host "`nBuilding images..." -ForegroundColor Cyan
docker compose build
if ($LASTEXITCODE -ne 0) { Pop-Location; exit 1 }

Write-Host "`nStarting Postgres + Redis..." -ForegroundColor Cyan
docker compose up -d postgres redis
Start-Sleep -Seconds 5

Write-Host "`nRunning migrations..." -ForegroundColor Cyan
docker compose run --rm api uv run alembic upgrade head
if ($LASTEXITCODE -ne 0) { Pop-Location; exit 1 }

Write-Host "`nSeeding demo data..." -ForegroundColor Cyan
docker compose run --rm api uv run python scripts/seed_data.py
if ($LASTEXITCODE -ne 0) { Pop-Location; exit 1 }

Write-Host "`nStarting API + worker + web..." -ForegroundColor Cyan
docker compose up -d api worker web
Pop-Location

Write-Host ""
Write-Host "==============================================================" -ForegroundColor Green
Write-Host "  Preview is up at http://localhost:3000" -ForegroundColor Green
Write-Host "==============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "  API docs    http://localhost:8000/docs"
Write-Host ""
Write-Host "  Super admin   admin@customerflow.ai  / Admin@CustomerFlow1"
Write-Host "  Plumber       mike@smithsplumbing.co.uk / Plumber@Test1"
Write-Host "  Electrician   sarah@brightspark.co.uk   / Electric@Test1"
Write-Host "  Cleaner       priya@sparkclean.co.uk    / Cleaner@Test1"
Write-Host "  Salon         amira@luxesalon.co.uk     / Salon@Test12"
Write-Host ""
Write-Host "  Stop:  cd infra && docker compose down" -ForegroundColor Yellow
