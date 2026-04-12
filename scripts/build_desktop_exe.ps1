param(
    [string]$ExeName = "GribKontrolDesktop"
)

$ErrorActionPreference = "Stop"

Write-Host "Building desktop EXE..."

$pythonExe = Join-Path (Get-Location) ".venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    throw "Не найден .venv\\Scripts\\python.exe. Сначала настройте окружение и установите зависимости."
}

& $pythonExe -m pip install --upgrade pip
& $pythonExe -m pip install pyinstaller

$cmd = @(
    "-m", "PyInstaller",
    "--noconfirm",
    "--onedir",
    "--name", $ExeName,
    "--add-data", "templates;templates",
    "--add-data", "data;data",
    "desktop/run_desktop.py"
)

& $pythonExe @cmd

if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller build failed"
}

$out = Join-Path (Get-Location) "dist\$ExeName\$ExeName.exe"
if (Test-Path $out) {
    Write-Host "EXE ready: $out"
} else {
    throw "EXE not found in dist/"
}
