param(
    [Parameter(Mandatory = $true)]
    [string]$ApkPath,

    [string]$PackageName = "com.mushroom.detector",
    [string]$AppName = "Гриб Контроль",
    [string]$VersionCode = "1",
    [string]$VersionName = "1.0",
    [string]$MinSdk = "26",
    [string]$TargetSdk = "35"
)

$ErrorActionPreference = "Stop"

$apk = Resolve-Path $ApkPath -ErrorAction Stop
$workRoot = Join-Path $PSScriptRoot "..\build\xapk-temp"
$outDir = Join-Path $PSScriptRoot "..\build\outputs"
$xapkName = "grib-kontrol-v$VersionName.xapk"
$zipPath = Join-Path $outDir "grib-kontrol-v$VersionName.zip"
$xapkPath = Join-Path $outDir $xapkName

if (Test-Path $workRoot) { Remove-Item $workRoot -Recurse -Force }
if (Test-Path $zipPath) { Remove-Item $zipPath -Force }
if (Test-Path $xapkPath) { Remove-Item $xapkPath -Force }

New-Item -ItemType Directory -Path $workRoot -Force | Out-Null
New-Item -ItemType Directory -Path $outDir -Force | Out-Null

$apkFileName = Split-Path $apk -Leaf
Copy-Item $apk $workRoot -Force
$apkFilePath = Join-Path $workRoot $apkFileName
$apkSize = (Get-Item $apkFilePath).Length

$manifest = @{
    xapk_version = 2
    package_name = $PackageName
    name = $AppName
    version_code = $VersionCode
    version_name = $VersionName
    min_sdk_version = $MinSdk
    target_sdk_version = $TargetSdk
    permissions = @("android.permission.CAMERA")
    total_size = $apkSize
    split_apks = @(
        @{
            file = $apkFileName
            id = $PackageName
        }
    )
    expansions = @()
}

$manifest | ConvertTo-Json -Depth 6 | Set-Content (Join-Path $workRoot "manifest.json") -Encoding UTF8

Compress-Archive -Path (Join-Path $workRoot "*") -DestinationPath $zipPath -Force
Rename-Item -Path $zipPath -NewName $xapkName

Write-Host "XAPK готов: $xapkPath"
