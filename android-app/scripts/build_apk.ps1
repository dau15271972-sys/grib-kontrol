param(
    [ValidateSet("debug", "release")]
    [string]$Variant = "debug"
)

$ErrorActionPreference = "Stop"

$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$gradlew = Join-Path $projectRoot "gradlew.bat"

if (-not (Test-Path $gradlew)) {
    Write-Host "gradlew.bat не найден."
    Write-Host "Откройте папку android-app в Android Studio и выполните Sync, затем запустите этот скрипт снова."
    exit 1
}

$task = if ($Variant -eq "release") { "assembleRelease" } else { "assembleDebug" }

Push-Location $projectRoot
try {
    & $gradlew $task
    if ($LASTEXITCODE -ne 0) {
        throw "Gradle task failed: $task"
    }

    $apkPath = if ($Variant -eq "release") {
        Join-Path $projectRoot "app\build\outputs\apk\release\app-release.apk"
    } else {
        Join-Path $projectRoot "app\build\outputs\apk\debug\app-debug.apk"
    }

    if (Test-Path $apkPath) {
        Write-Host "APK готов: $apkPath"
    } else {
        Write-Host "Сборка завершилась, но APK не найден по ожидаемому пути:"
        Write-Host $apkPath
        exit 1
    }
}
finally {
    Pop-Location
}
