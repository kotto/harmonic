# PowerShell script to replace all traces of the previous EC2 deployment IP
# Replaces __EC2_IP__ with __EC2_IP__ placeholder across all text files

param(
    [string]$RootPath = (Get-Location).Path,
    [string]$OldIP = "__EC2_IP__",
    [string]$NewIP = "__EC2_IP__",
    [switch]$WhatIf = $false
)

Write-Host "=== Sanitisation des traces EC2 ===" -ForegroundColor Cyan
Write-Host "Racine: $RootPath"
Write-Host "Remplacement: $OldIP -> $NewIP"
if ($WhatIf) { Write-Host "MODE SIMULATION (WhatIf) - Aucun fichier ne sera modifiÃ©" -ForegroundColor Yellow }
Write-Host ""

# Extensions de fichiers Ã  ignorer (binaires)
$BinaryExtensions = @('.exe', '.dll', '.so', '.dylib', '.bin', '.dat', '.npy', '.gguf', 
                      '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.ico', '.svg',
                      '.mp3', '.mp4', '.avi', '.mov', '.wav', '.flac', '.ogg',
                      '.zip', '.tar', '.gz', '.rar', '.7z',
                      '.woff', '.woff2', '.ttf', '.eot', '.otf',
                      '.o', '.a', '.lib', '.obj', '.pyc', '.pyo',
                      '.wasm')

# RÃ©pertoires Ã  ignorer
$ExcludeDirs = @('\.git', 'node_modules', '.venv', 'venv', '__pycache__', '.qoder', '.kilo')

Write-Host "Recherche des fichiers contenant '$OldIP'..." -ForegroundColor Yellow

# Trouver tous les fichiers contenant l'ancienne IP
$files = Get-ChildItem -Path $RootPath -Recurse -File | Where-Object {
    $shouldInclude = $true
    # Exclure les rÃ©pertoires
    foreach ($dir in $ExcludeDirs) {
        if ($_.FullName -match $dir) { $shouldInclude = $false; break }
    }
    # Exclure les extensions binaires
    if ($shouldInclude -and $BinaryExtensions -contains $_.Extension.ToLower()) { $shouldInclude = $false }
    # Exclure les trÃ¨s gros fichiers (>10MB)
    if ($shouldInclude -and $_.Length -gt 10MB) { $shouldInclude = $false }
    $shouldInclude
}

$count = 0
$fileCount = 0
$modifiedFiles = @()

foreach ($file in $files) {
    try {
        $content = Get-Content -Path $file.FullName -Raw -ErrorAction Stop
        if ($content -match [regex]::Escape($OldIP)) {
            $fileCount++
            $newContent = $content -replace [regex]::Escape("ec2-__EC2_IP__.compute-1.amazonaws.com"), "ec2-$NewIP.compute-1.amazonaws.com"
            $newContent = $newContent -replace [regex]::Escape($OldIP), $NewIP
            
            $matches = [regex]::Matches($content, [regex]::Escape($OldIP)).Count
            $count += $matches
            
            if (-not $WhatIf) {
                # PrÃ©server le encoding original (UTF8 sans BOM si possible)
                [System.IO.File]::WriteAllText($file.FullName, $newContent, [System.Text.UTF8Encoding]::new($false))
            }
            
            $relativePath = $file.FullName.Substring($RootPath.Length).TrimStart('\')
            $modifiedFiles += "$relativePath ($matches occurrences)"
            Write-Host "  [$fileCount] $relativePath - $matches occurrence(s)" -ForegroundColor Green
        }
    } catch {
        Write-Host "  ERREUR: $($file.FullName) - $_" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "=== RESUME ===" -ForegroundColor Cyan
if ($WhatIf) {
    Write-Host "Simulation: $fileCount fichiers contiennent '$OldIP' ($count occurrences totales)" -ForegroundColor Yellow
} else {
    Write-Host "ModifiÃ©s: $fileCount fichiers, $count occurrences remplacÃ©es par '$NewIP'" -ForegroundColor Green
}

# Sauvegarder la liste des fichiers modifiÃ©s
$reportPath = Join-Path $RootPath "rapport_sanitisation_ec2.md"
@"
# Rapport de Sanitisation EC2

**Date :** $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
**Ancienne IP :** $OldIP
**Nouveau placeholder :** $NewIP
**Fichiers modifiÃ©s :** $fileCount
**Occurrences totales :** $count

## Fichiers modifiÃ©s

$($modifiedFiles -join "`n")

---
*GÃ©nÃ©rÃ© automatiquement*
"@ | Out-File -FilePath $reportPath -Encoding utf8

Write-Host "Rapport sauvegardÃ©: $reportPath" -ForegroundColor Cyan
Write-Host "TerminÃ©!" -ForegroundColor Green
