# =============================================================================
# CustomerFlow AI -- local preview launcher (Windows / PowerShell)
# =============================================================================
# Spins up the API on http://localhost:8000 and the web app on
# http://localhost:3000 against a local SQLite database, seeds a super admin
# plus four tenant owners with realistic demo data, and prints the
# credentials.
#
# Prerequisites (one-time):
#   - Python 3.11+   (https://www.python.org)
#   - Node.js 20+    (https://nodejs.org)
#   - uv             (pip install uv  OR  winget install astral-sh.uv)
#   - pnpm           (npm install -g pnpm@9)
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File scripts\preview.ps1
# =============================================================================

$ErrorActionPreference = "Stop"
$Root  = (Resolve-Path "$PSScriptRoot\..").Path
$Api   = Join-Path $Root "apps\api"
$Web   = Join-Path $Root "apps\web"

# Ports default to 8002 / 3002 to avoid common conflicts (PHP/WAMP, other
# dev servers, etc.). Override via $env:API_PORT / $env:WEB_PORT.
if (-not $env:API_PORT) { $env:API_PORT = "8002" }
if (-not $env:WEB_PORT) { $env:WEB_PORT = "3002" }

function Test-PortFree($port) {
    return -not (Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue)
}

Write-Host ""
Write-Host "CustomerFlow AI preview launcher" -ForegroundColor Cyan
Write-Host "=========================" -ForegroundColor Cyan

# --- 1. Sanity-check tooling ------------------------------------------------
function Require-Cmd($name, $hint) {
    if (-not (Get-Command $name -ErrorAction SilentlyContinue)) {
        Write-Host "  [X] $name not found." -ForegroundColor Red
        Write-Host "      $hint" -ForegroundColor Yellow
        exit 1
    }
    Write-Host "  [ok] $name" -ForegroundColor Green
}

Write-Host ""
Write-Host "Checking tooling..."
Require-Cmd "python" "Install Python 3.11+ from python.org"
Require-Cmd "uv"     "Install with: pip install uv"
Require-Cmd "node"   "Install Node.js 20+ from nodejs.org"
Require-Cmd "pnpm"   "Install with: npm install -g pnpm@9"

Write-Host ""
Write-Host "Checking ports (API=$($env:API_PORT)  WEB=$($env:WEB_PORT))..."
foreach ($p in @($env:API_PORT, $env:WEB_PORT)) {
    if (-not (Test-PortFree $p)) {
        $owner = Get-NetTCPConnection -LocalPort $p -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
        $proc  = Get-Process -Id $owner.OwningProcess -ErrorAction SilentlyContinue
        Write-Host "  [X] Port $p is already in use by pid=$($owner.OwningProcess) name=$($proc.ProcessName)" -ForegroundColor Red
        Write-Host "      Set `$env:API_PORT / `$env:WEB_PORT before re-running, or free that port." -ForegroundColor Yellow
        exit 1
    }
    Write-Host "  [ok] port $p free" -ForegroundColor Green
}

# --- 2. Preview env (no Postgres / Redis / external providers needed) -------
$env:ENVIRONMENT                = "development"
$env:DATABASE_URL               = "sqlite+aiosqlite:///./customerflow_preview.db"
$env:JWT_SECRET                 = "preview_jwt_secret_not_for_production_use_xxxxxxxxxxxxxxxxxxxxxx"
$env:JWT_REFRESH_SECRET         = "preview_refresh_secret_not_for_production_use_xxxxxxxxxxxxxxxxxxx"
$env:ALLOWED_ORIGINS            = "http://localhost:$($env:WEB_PORT)"
$env:FRONTEND_URL               = "http://localhost:$($env:WEB_PORT)"
$env:COOKIE_SECURE              = "false"
$env:COOKIE_SAMESITE            = "lax"
$env:SMS_PROVIDER               = "mock"
$env:EMAIL_PROVIDER             = "mock"
$env:PAYMENT_PROVIDER           = "mock"
$env:AI_PROVIDER                = "mock"
$env:SOCIAL_PROVIDER            = "mock"
$env:REDIS_URL                  = "redis://localhost:6379/0"
$env:API_PROXY_TARGET           = "http://localhost:$($env:API_PORT)"
# Leave NEXT_PUBLIC_API_URL empty so the web app uses relative URLs that go
# through the Next.js rewrite -- this keeps the browser on a single origin so
# httpOnly cookies set by FastAPI are visible to the Next.js middleware too.
$env:NEXT_PUBLIC_API_URL        = ""
$env:PYTHONPATH                 = $Api
# Seed script prints emoji; force UTF-8 stdout so cp1252 hosts don't choke.
$env:PYTHONIOENCODING           = "utf-8"
$env:PYTHONUTF8                 = "1"

# --- 3. API setup -----------------------------------------------------------
Write-Host ""
Write-Host "Installing API dependencies..." -ForegroundColor Cyan
Push-Location $Api
uv sync
if ($LASTEXITCODE -ne 0) { Pop-Location; Write-Host "uv sync failed" -ForegroundColor Red; exit 1 }

Write-Host ""
Write-Host "Seeding the preview database (this also resets it)..." -ForegroundColor Cyan
uv run python scripts/seed_data.py
if ($LASTEXITCODE -ne 0) { Pop-Location; Write-Host "Seed failed" -ForegroundColor Red; exit 1 }
Pop-Location

# --- 4. Web setup -----------------------------------------------------------
Write-Host ""
Write-Host "Installing web dependencies..." -ForegroundColor Cyan
Push-Location $Web
pnpm install
if ($LASTEXITCODE -ne 0) { Pop-Location; Write-Host "pnpm install failed" -ForegroundColor Red; exit 1 }
Pop-Location

# --- 5. Launch both services in background processes ------------------------
Write-Host ""
Write-Host "Starting services..." -ForegroundColor Cyan

$apiArgs = @(
    "run", "uvicorn", "app.main:app",
    "--host", "127.0.0.1", "--port", "$($env:API_PORT)", "--reload"
)
$apiProc = Start-Process -PassThru -WindowStyle Hidden -WorkingDirectory $Api `
    -FilePath "uv" -ArgumentList $apiArgs `
    -RedirectStandardOutput "$Root\preview-api.log" `
    -RedirectStandardError  "$Root\preview-api.err.log"

# pnpm on Windows resolves to a .ps1 script that Start-Process cannot exec
# directly. The .cmd shim works as a real Windows executable.
$pnpmCmd = (Get-Command pnpm.cmd -ErrorAction SilentlyContinue).Source
if (-not $pnpmCmd) {
    Write-Host "[X] pnpm.cmd not found on PATH" -ForegroundColor Red
    exit 1
}
$webProc = Start-Process -PassThru -WindowStyle Hidden -WorkingDirectory $Web `
    -FilePath $pnpmCmd -ArgumentList @("dev", "--port", "$($env:WEB_PORT)") `
    -RedirectStandardOutput "$Root\preview-web.log" `
    -RedirectStandardError  "$Root\preview-web.err.log"

Write-Host "Waiting for services to become reachable..." -ForegroundColor DarkGray
$apiReady = $false; $webReady = $false
for ($i = 0; $i -lt 30 -and (-not ($apiReady -and $webReady)); $i++) {
    Start-Sleep -Seconds 1
    if (-not $apiReady) {
        try { (Invoke-WebRequest "http://127.0.0.1:$($env:API_PORT)/healthz" -UseBasicParsing -TimeoutSec 1) | Out-Null; $apiReady = $true } catch {}
    }
    if (-not $webReady) {
        try { (Invoke-WebRequest "http://127.0.0.1:$($env:WEB_PORT)" -UseBasicParsing -TimeoutSec 1) | Out-Null; $webReady = $true } catch {}
    }
}
if ($apiReady) { Write-Host "  [ok] API reachable" -ForegroundColor Green } else { Write-Host "  [warn] API did not respond in 30s (check preview-api.err.log)" -ForegroundColor Yellow }
if ($webReady) { Write-Host "  [ok] Web reachable" -ForegroundColor Green } else { Write-Host "  [warn] Web did not respond in 30s (Next.js can take a minute on first build)" -ForegroundColor Yellow }

# --- 6. Print credentials & URLs --------------------------------------------
Write-Host ""
Write-Host "==============================================================" -ForegroundColor Green
Write-Host "  CustomerFlow AI preview is up" -ForegroundColor Green
Write-Host "==============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "  Web app    : http://localhost:$($env:WEB_PORT)"   -ForegroundColor Cyan
Write-Host "  API docs   : http://localhost:$($env:API_PORT)/docs" -ForegroundColor Cyan
Write-Host "  Health     : http://localhost:$($env:API_PORT)/healthz" -ForegroundColor Cyan
Write-Host ""
Write-Host "  --- SUPER ADMIN ---------------------------------------------"
Write-Host "  Sign in at /login -- auto-routes to /admin"
Write-Host "  Email        admin@customerflow.ai"
Write-Host "  Password     Admin@CustomerFlow1"
Write-Host ""
Write-Host "  --- TENANT OWNERS  (each lands on /dashboard) ---------------"
Write-Host "  mike@smithsplumbing.co.uk     / Plumber@Test1   (Growth)"
Write-Host "  sarah@brightspark.co.uk       / Electric@Test1  (Pro)"
Write-Host "  priya@sparkclean.co.uk        / Cleaner@Test1   (Starter)"
Write-Host "  amira@luxesalon.co.uk         / Salon@Test12    (Growth)"
Write-Host ""
Write-Host "  --- STAFF MEMBERS  (limited tenant access) ------------------"
Write-Host "  dave@smithsplumbing.co.uk     / Staff@Test123"
Write-Host "  jake@smithsplumbing.co.uk     / Staff@Test123"
Write-Host "  tom@brightspark.co.uk         / Staff@Test123"
Write-Host ""
Write-Host "  Logs:"
Write-Host "    preview-api.log / preview-api.err.log"
Write-Host "    preview-web.log / preview-web.err.log"
Write-Host ""
Write-Host "  Process IDs: api=$($apiProc.Id)  web=$($webProc.Id)"
Write-Host "  Stop with:   powershell -File scripts\preview-stop.ps1"
Write-Host ""

@{ api = $apiProc.Id; web = $webProc.Id } | ConvertTo-Json | Out-File "$Root\.preview-pids.json" -Encoding ascii

Write-Host "Services run in the background. This terminal is now free." -ForegroundColor Yellow
