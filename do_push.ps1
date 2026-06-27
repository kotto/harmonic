$ErrorActionPreference = "Continue"
Set-Location "e:\SAAS - Copie"

Remove-Item -Path ".git\index.lock" -Force -ErrorAction SilentlyContinue

$result = git push -u origin feature/ka-phone-full 2>&1
$exitCode = $LASTEXITCODE

$result | Out-File -FilePath "e:\SAAS - Copie\push_result.txt" -Encoding UTF8
"EXIT_CODE: $exitCode" | Out-File -FilePath "e:\SAAS - Copie\push_result.txt" -Append -Encoding UTF8
"COMPLETED_AT: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" | Out-File -FilePath "e:\SAAS - Copie\push_result.txt" -Append -Encoding UTF8
