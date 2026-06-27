Write-Host "=== REDIRECTION TEMP WINDOWS -> E: ==="

# Créer les dossiers sur E:
New-Item -ItemType Directory -Path "E:\Temp" -Force | Out-Null
New-Item -ItemType Directory -Path "E:\WindowsTemp" -Force | Out-Null
Write-Host "Dossiers E:\Temp et E:\WindowsTemp crees"

# Variables d'environnement SYSTEME
[Environment]::SetEnvironmentVariable("TEMP", "E:\Temp", "Machine")
[Environment]::SetEnvironmentVariable("TMP", "E:\Temp", "Machine")
Write-Host "TEMP/TMP systeme -> E:\Temp"

# Variables d'environnement UTILISATEUR
[Environment]::SetEnvironmentVariable("TEMP", "E:\Temp", "User")
[Environment]::SetEnvironmentVariable("TMP", "E:\Temp", "User")
Write-Host "TEMP/TMP utilisateur -> E:\Temp"

Write-Host ""
Write-Host "=== CONFIGURATION TERMINEE ==="
Write-Host "Redemarrer le PC pour prise d'effet complete"
Write-Host "Apres reboot, tous les fichiers temporaires iront sur E: au lieu de C:"