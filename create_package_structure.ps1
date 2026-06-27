# Script pour créer la structure complète du package LM Arena

$packageRoot = "F:\SAAS - Copie\lm_arena_package"

# Liste des dossiers à créer
$folders = @(
    "backend",
    "frontend", 
    "scripts",
    "docs",
    "tests",
    "config",
    "aws",
    "monitoring",
    "backend\api",
    "backend\core",
    "backend\models",
    "backend\schemas",
    "backend\services",
    "backend\tasks",
    "frontend\static",
    "frontend\templates",
    "scripts\deployment",
    "scripts\monitoring",
    "scripts\testing",
    "docs\api",
    "docs\guides",
    "docs\reference",
    "tests\integration",
    "tests\performance",
    "tests\unit",
    "config\environments",
    "config\secrets",
    "aws\ec2",
    "aws\lambda",
    "aws\s3",
    "monitoring\alerts",
    "monitoring\dashboards",
    "monitoring\metrics"
)

Write-Host "Création de la structure du package LM Arena..." -ForegroundColor Green

foreach ($folder in $folders) {
    $fullPath = Join-Path $packageRoot $folder
    if (-not (Test-Path $fullPath)) {
        New-Item -ItemType Directory -Path $fullPath -Force | Out-Null
        Write-Host "  ✓ Créé: $folder" -ForegroundColor Cyan
    } else {
        Write-Host "  ⚠ Existe déjà: $folder" -ForegroundColor Yellow
    }
}

Write-Host "`nStructure créée avec succès !" -ForegroundColor Green
Write-Host "Emplacement: $packageRoot" -ForegroundColor White
Write-Host "`nDossiers créés:" -ForegroundColor White
Get-ChildItem -Path $packageRoot -Recurse -Directory | Select-Object -ExpandProperty FullName