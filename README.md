# Гриб Контроль

«Гриб Контроль» — автономный каркас Android- и Windows-приложения для
консервативной предварительной оценки риска по нескольким фотографиям грибов.

## Текущее состояние

Этап A намеренно не содержит production-модели. Старый распознаватель по
цветовым гистограммам удалён. Пока совместимый проверенный bundle не установлен
и не прошёл `ArtifactCompatibilityGate`, оба приложения возвращают только:

```text
RECOGNITION_UNAVAILABLE
```

Приложение не определяет, можно ли употреблять гриб, и не выдаёт итоговый статус
`SAFE`.

## Структура

- `android-app/` — Android-приложение на Kotlin, Compose и CameraX.
- `app/` — fail-closed Flask API и контракты совместимости артефактов.
- `desktop/` — локальный запуск Flask в desktop-режиме.
- `data/` — закрытые справочные данные; они не являются моделью и не выводятся
  пользователю как разрешение на употребление.
- `scripts/safety_gate.py` — проверки запрещённых UI-фраз и неподвязанных
  model-assets.
- `tests/` — Python-тесты безопасного поведения.

Сетевой доступ не входит в путь инференса. Android хранит снимки только во
временном app-private cache и удаляет снимок при замене и завершении сессии.

## Python и desktop

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.venv\Scripts\python.exe -m pytest
.venv\Scripts\python.exe -m ruff check .
.venv\Scripts\python.exe desktop\run_desktop.py
```

Desktop EXE:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build_desktop_exe.ps1
```

Ожидаемый путь для onedir-сборки:

```text
dist/GribKontrolDesktop/GribKontrolDesktop.exe
```

## Android

```powershell
cd android-app
.\gradlew.bat testDebugUnitTest
.\gradlew.bat lintDebug
.\gradlew.bat assembleDebug
```

В Windows-пути с кириллицей JUnit worker некоторых версий AGP может потерять
test-классы. Для полного локального прогона через временную ASCII-букву диска:

```powershell
powershell -ExecutionPolicy Bypass -File .\android-app\scripts\verify_android.ps1
```

Debug APK:

```text
android-app/app/build/outputs/apk/debug/app-debug.apk
```

CameraX сохраняет полноценный кадр через `ImageCapture`; mirror/rotate не
считаются независимыми наблюдениями. Обязательные ракурсы представлены
`ObservationSession` и `CaptureViewType`.

## Safety-гейты

> **SAFETY:** медицинский текст экстренного экрана сейчас помечен как
> `UNAPPROVED_MEDICAL_PLACEHOLDER`. Debug/local-сборки разрешены для проверки,
> но Android release-задачи и `build_desktop_exe.ps1 -Production` намеренно
> заблокированы до отдельного human review.

```powershell
python scripts\safety_gate.py
```

Гейт завершает работу с ошибкой, если в production UI найдена запрещённая
разрешающая формулировка или в репозитории появился неподвязанный model-asset.

SAFETY: изменение статусов, пользовательских safety-текстов, порогов, rejection,
dangerous-confusion логики или compatibility contract требует отдельного
ревью.
