$computerSystem = Get-WmiObject Win32_ComputerSystem -EnableAllPrivileges
$computerSystem.AutomaticManagedPagefile = $false
$computerSystem.Put() | Out-Null

$pageFileSettings = Get-WmiObject Win32_PageFileSetting
if ($pageFileSettings) {
    $pageFileSettings.Delete() | Out-Null
}

Set-WmiInstance -Class Win32_PageFileSetting -Arguments @{Name="C:\pagefile.sys"; InitialSize=2048; MaximumSize=4096} | Out-Null
Set-WmiInstance -Class Win32_PageFileSetting -Arguments @{Name="E:\pagefile.sys"; InitialSize=0; MaximumSize=0} | Out-Null

Write-Host "Pagefile configure: C:=2-4Go, E:=systeme gere"
Write-Host "Redemarrage necessaire pour appliquer"