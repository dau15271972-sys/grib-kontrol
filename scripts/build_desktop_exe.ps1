param(
    [string]$ExeName = "GribKontrolDesktop",
    [switch]$Production
)

$ErrorActionPreference = "Stop"

Write-Host "Building desktop EXE..."

$pythonExe = Join-Path (Get-Location) ".venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    throw "Не найден .venv\\Scripts\\python.exe. Сначала настройте окружение и установите зависимости."
}

& $pythonExe -c "import PyInstaller" 2>$null
if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller is not installed. Run: .venv\Scripts\python.exe -m pip install -r requirements-dev.txt"
}

if ($Production) {
    & $pythonExe "scripts\medical_placeholder_gate.py" "--production"
    if ($LASTEXITCODE -ne 0) {
        throw "SAFETY: production desktop build is blocked by unapproved medical copy."
    }
}

$cmd = @(
    "-m", "PyInstaller",
    "--noconfirm",
    "--onedir",
    "--name", $ExeName,
    "--add-data", "templates;templates",
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
