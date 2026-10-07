# Dumps the tessellated geometry of every visible component in a SolidWorks
# assembly to <OutDir>\parts.json + parts.bin (see SwDump.cs for the format).
# Requires SOLIDWORKS to be installed; it is started if not already running.
param(
  [string]$Assembly = (Join-Path $PSScriptRoot "..\..\models\Main_Assembly.SLDASM"),
  [string]$OutDir = (Join-Path $PSScriptRoot "export"),
  [string]$SwInstall = "C:\Program Files\SOLIDWORKS Corp\SOLIDWORKS"
)

$ErrorActionPreference = "Stop"
$redist = Join-Path $SwInstall "api\redist"
$sldworks = Join-Path $redist "SolidWorks.Interop.sldworks.dll"
$swconst = Join-Path $redist "SolidWorks.Interop.swconst.dll"

Add-Type -Path $sldworks
Add-Type -Path $swconst
Add-Type -TypeDefinition (Get-Content (Join-Path $PSScriptRoot "SwDump.cs") -Raw) -ReferencedAssemblies $sldworks, $swconst

New-Item -ItemType Directory -Force $OutDir | Out-Null
if (-not (Get-Process SLDWORKS -ErrorAction SilentlyContinue)) {
  Write-Host "Starting SOLIDWORKS..."
  $null = New-Object -ComObject SldWorks.Application
  Start-Sleep 5
}

$Assembly = (Resolve-Path $Assembly).Path
$OutDir = (Resolve-Path $OutDir).Path
Write-Host "Tessellating $Assembly (this takes ~15 minutes for Main_Assembly)..."
[SwDump]::Run($Assembly, $OutDir)
Get-ChildItem $OutDir | Select-Object Name, Length
