param(
    [ValidatePattern("^[A-Z]$")]
    [string]$DriveLetter = "R"
)

$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$drive = "${DriveLetter}:"

if (Test-Path -LiteralPath "$drive\") {
    throw "Drive $drive is already in use. Pass another free letter with -DriveLetter."
}

& subst.exe $drive $repoRoot
if ($LASTEXITCODE -ne 0) {
    throw "Could not map $repoRoot to $drive"
}

try {
    Push-Location "$drive\android-app"
    try {
        & .\gradlew.bat testDebugUnitTest lintDebug assembleDebug
        if ($LASTEXITCODE -ne 0) {
            throw "Android verification failed"
        }
    }
    finally {
        Pop-Location
    }
}
finally {
    & subst.exe $drive /D
}
