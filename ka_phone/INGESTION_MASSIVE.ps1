# KA-Next v2 — Ingestion Massive (PowerShell)
# Construit 12 hologrammes 64×64 + ingère toutes les sources
# Usage : .\INGESTION_MASSIVE.ps1

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  KA-Next v2 - INGESTION MASSIVE" -ForegroundColor Yellow
Write-Host "  Construit 12 hologrammes 64x64 + ingere toutes les sources" -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Sources :" -ForegroundColor White
Write-Host "  [1] Corpus UNESCO (32 faits)"
Write-Host "  [2] Corpus Sciences (20 faits)"
Write-Host "  [3] Corpus Philosophie (10 faits)"
Write-Host "  [4] Corpus enrichi (geographie, histoire, mathematiques...)"
Write-Host "  [5] QuickFacts (1030 faits)"
Write-Host "  [6] Fichiers texte locaux (data/corpus/*.txt, *.md)"
Write-Host ""
Write-Host "Total estime : ~2000 faits dans 12 domaines specialises" -ForegroundColor Green
Write-Host "Temps estime : ~2 secondes" -ForegroundColor Green
Write-Host ""

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

$env:PYTHONIOENCODING = "utf-8"
python ingest_massive_nx64.py

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host "  INGESTION TERMINEE AVEC SUCCES" -ForegroundColor Green
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "  Pour tester :" -ForegroundColor White
    Write-Host "    python ka_next_core.py --query ""Quelle est la capitale du Senegal ?""" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  Pour le benchmark :" -ForegroundColor White
    Write-Host "    python benchmark_ensemble.py" -ForegroundColor Gray
    Write-Host "============================================================" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Red
    Write-Host "  ERREUR lors de l'ingestion." -ForegroundColor Red
    Write-Host "============================================================" -ForegroundColor Red
}