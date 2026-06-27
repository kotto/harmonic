# =============================================================================
# KA PHONE - Cloudflare Tunnel Deployment (Windows)
# =============================================================================
# Expose KA Phone securise via Cloudflare Tunnel (zero ouvertures de ports).
# 
# ETAPE 1: Telecharger cloudflared.exe
# ETAPE 2: Lancer KA Phone
# ETAPE 3: Creer le tunnel
# =============================================================================

$ErrorActionPreference = "Stop"
$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$KaPort = 8080

Write-Host "=======================================================" -ForegroundColor Green
Write-Host "  KA PHONE - Cloudflare Tunnel Deployment (Windows)" -ForegroundColor Green
Write-Host "=======================================================" -ForegroundColor Green

# ────────────────────────────────────────────────
# 1. Check/Download cloudflared
# ────────────────────────────────────────────────
Write-Host "`n[1/3] Checking cloudflared..." -ForegroundColor Yellow

$CloudflaredPath = "$env:USERPROFILE\cloudflared.exe"

if (-not (Test-Path $CloudflaredPath)) {
    Write-Host "  Downloading cloudflared..." -ForegroundColor Yellow
    $url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"
    Invoke-WebRequest -Uri $url -OutFile $CloudflaredPath
    Write-Host "  cloudflared downloaded to $CloudflaredPath" -ForegroundColor Green
} else {
    Write-Host "  cloudflared already installed" -ForegroundColor Green
}

# ────────────────────────────────────────────────
# 2. Start KA Phone server
# ────────────────────────────────────────────────
Write-Host "`n[2/3] Starting KA Phone server..." -ForegroundColor Yellow
cd $ProjectDir

# Check if Python is available
$PythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $PythonCmd) {
    Write-Host "  ERROR: Python not found" -ForegroundColor Red
    exit 1
}

# Start server in background
$ServerProcess = Start-Process python -ArgumentList "unified_server.py" -PassThru -NoNewWindow
Start-Sleep -Seconds 3

Write-Host "  KA Phone server started (PID: $($ServerProcess.Id))" -ForegroundColor Green

# ────────────────────────────────────────────────
# 3. Create Cloudflare Tunnel
# ────────────────────────────────────────────────
Write-Host "`n[3/3] Creating Cloudflare Tunnel..." -ForegroundColor Yellow
Write-Host ""
Write-Host "  ============================================================"
Write-Host "  MODE RAPIDE: Tunnel test sans domaine (trycloudflare.com)"
Write-Host "  ============================================================"
Write-Host ""
Write-Host "  KA Phone sera accessible via une URL temporaire genere par Cloudflare."
Write-Host "  Pas de domaine, pas de carte bancaire, pas de configuration DNS."
Write-Host ""
Write-Host "  L'URL apparaitra dans quelques secondes..."
Write-Host ""

# Run tunnel
& $CloudflaredPath tunnel --url "http://localhost:${KaPort}" --no-autoupdate 2>&1 | ForEach-Object {
    $line = $_
    Write-Host $line
    
    # Extract the trycloudflare URL
    if ($line -match 'https://[a-z0-9-]+\.trycloudflare\.com') {
        $url = $matches[0]
        Write-Host ""
        Write-Host "=======================================================" -ForegroundColor Green
        Write-Host "  KA PHONE IS LIVE!" -ForegroundColor Green
        Write-Host "  URL: $url" -ForegroundColor Green
        Write-Host "=======================================================" -ForegroundColor Green
        Write-Host ""
        Write-Host "  Press Ctrl+C to stop the tunnel" -ForegroundColor Yellow
    }
}

# Cleanup on exit
Write-Host "`nCleaning up..." -ForegroundColor Yellow
Stop-Process -Id $ServerProcess.Id -Force -ErrorAction SilentlyContinue
Write-Host "Done." -ForegroundColor Green