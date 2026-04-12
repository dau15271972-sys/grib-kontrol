# grib-kontrol

Оффлайн приложение для распознавания грибов на Android и Windows.

## Что в проекте

- `android-app/` — Android-приложение на Kotlin + Compose.
- `app/` — Python-часть приложения.
- `desktop/` — запуск desktop-версии.
- `data/` — база знаний и индекс распознавания.

## Запуск Python-версии

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app/main.py
```

После запуска откройте `http://localhost:8000`.

## Desktop-сборка

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build_desktop_exe.ps1
```

Готовый файл:
- `dist/GribKontrolDesktop.exe`

## Android-сборка

Откройте `android-app` в Android Studio, дождитесь Gradle Sync и соберите APK:

```powershell
cd android-app
powershell -ExecutionPolicy Bypass -File .\scripts\build_apk.ps1 -Variant debug
```

Ожидаемый APK:
- `android-app/app/build/outputs/apk/debug/app-debug.apk`

## Важно

Проект помогает с предварительным определением грибов, но не должен использоваться как единственный источник для решения о безопасности употребления.
