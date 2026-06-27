# AWS CLI LOGIN SECURISE POUR HARMONIC AI
# Utilisation de aws login au lieu des cles statiques

Write-Host "CONNEXION AWS CLI SECURISEE"
Write-Host "=================================="

# Verification si AWS CLI est installe
try {
    aws --version | Out-Null
} catch {
    Write-Host "AWS CLI non installe. Installation:"
    Write-Host "   1. Telechargez: https://awscli.amazonaws.com/AWSCLIV2.msi"
    Write-Host "   2. Installez le package"
    Write-Host "   3. Redemarrez PowerShell"
    exit 1
}

Write-Host "Utilisation recommandee:"
Write-Host "1. Ouvrez la console AWS dans votre navigateur"
Write-Host "2. Utilisez vos identifiants de console existants"
Write-Host "3. Executez: aws sso login --profile harmonic-ai"
Write-Host ""
Write-Host "Ouverture de la console AWS..."

# Ouverture du navigateur vers la console AWS
Start-Process "https://console.aws.amazon.com/"

Write-Host "Console AWS ouverte"
Write-Host "Une fois connecte, executez:"
Write-Host "   aws sso login --profile harmonic-ai"
Write-Host "   aws configure set profile.harmonic-ai.region us-east-1"
