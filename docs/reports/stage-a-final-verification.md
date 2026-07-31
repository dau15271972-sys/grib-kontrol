# Stage A — финальная верификация

## Вердикт

**STAGE A: CLOSED**

Все обязательные тесты, lint-проверки, debug-сборки, проверки Gradle Wrapper и
safety-гейты выполнены успешно. Production/release остаётся намеренно
заблокированным из-за `UNAPPROVED_MEDICAL_PLACEHOLDER`.

## Дата и среда

- Дата проверки: 2026-07-31, начало фиксации среды 13:36:20 +01:00.
- ОС: Windows 11, версия 10.0, build 26200, amd64.
- Python системы: 3.14.4.
- Python виртуального окружения проекта: 3.12.10.
- Java: OpenJDK 21.0.10, JetBrains Runtime.
- Gradle: 8.7; Kotlin 1.9.22; Groovy 3.0.17; Ant 1.10.13.
- PyInstaller: 6.15.0.

## Репозиторий и исходное состояние

- Репозиторий: `dau15271972-sys/grib-kontrol`.
- Ветка: `chore/remove-unsafe-recognizer`.
- Ожидаемый HEAD: `c516e1b8390fd2ae2aa56af1a3146c487002c9b5`.
- Локальный HEAD: `c516e1b8390fd2ae2aa56af1a3146c487002c9b5`.
- Локальный remote-tracking HEAD: `c516e1b8390fd2ae2aa56af1a3146c487002c9b5`.
- Фактический remote HEAD по `git ls-remote`:
  `c516e1b8390fd2ae2aa56af1a3146c487002c9b5`.
- Начальный `git status --short --branch`:
  `## chore/remove-unsafe-recognizer...origin/chore/remove-unsafe-recognizer`.
- Незакоммиченные и staged-изменения до начала: отсутствовали.
- Начальный `git diff --stat`: пустой.

HEAD полностью совпал с заданным коммитом; чужих локальных изменений не было.

## Обязательные команды

| Команда | Код | Результат | Длительность |
|---|---:|---|---:|
| `.venv\Scripts\python.exe -m ruff check .` | 0 | PASS, `All checks passed!` | 1,01 с |
| `.venv\Scripts\python.exe -m pytest -ra` | 0 | PASS, 18/18 | pytest 1,39 с; процесс 2,14 с |
| `.venv\Scripts\python.exe scripts\safety_gate.py` | 0 | PASS, `Safety source gates passed.` | 0,41 с |
| `.venv\Scripts\python.exe scripts\medical_placeholder_gate.py` | 0 | PASS, development разрешён при явной заглушке | 0,06 с |
| `.venv\Scripts\python.exe scripts\validate_gradle_wrapper.py` | 0 | PASS, файлы и checksum Wrapper валидны | 0,06 с |
| `.venv\Scripts\python.exe scripts\medical_placeholder_gate.py --production` | 1 | EXPECTED BLOCK, причина `UNAPPROVED_MEDICAL_PLACEHOLDER` | 0,08 с |
| `powershell -ExecutionPolicy Bypass -File .\android-app\scripts\verify_android.ps1` | 0 | PASS: `testDebugUnitTest`, `lintDebug`, `assembleDebug` | 43,3 с |
| `powershell -ExecutionPolicy Bypass -File .\scripts\build_desktop_exe.ps1` | 0 | PASS, non-production onedir EXE | 20,0 с |

Код 1 production medical gate является ожидаемым успешным доказательством
блокировки, а не провалом Stage A.

## Python

- Собрано: 18 тестов.
- Прошло: 18.
- Упало: 0.
- Ошибки: 0.
- Пропущено: 0.
- Pytest warnings: 0.
- Время по pytest: 1,39 с.
- Ruff: ошибок и предупреждений нет.

Подтверждённые safety-проверки:

- forbidden UI phrase gate:
  `test_production_ui_has_no_forbidden_phrases` — PASS;
- unbound model asset gate:
  `test_repository_has_no_unbound_model_assets` — PASS;
- запрет опасных Android permissions:
  `test_android_has_no_network_or_location_permissions` — PASS;
- в production manifest объявлен только `android.permission.CAMERA`; network и
  location permissions отсутствуют;
- `ArtifactCompatibilityGate`: 4 Python-теста — exact match, incomplete bundle,
  calibration mismatch и запрет запуска inference при несовместимом bundle —
  PASS;
- Python fail-closed API без модели возвращает
  `RECOGNITION_UNAVAILABLE`; тесты технического сбоя сохраняют маршрут
  `/emergency`.

## Android

ASCII-drive script успешно выполнил одним Gradle-вызовом:

1. `testDebugUnitTest`;
2. `lintDebug`;
3. `assembleDebug`.

### Unit tests

- Собрано: 15.
- Прошло: 15.
- Упало: 0.
- Ошибки: 0.
- Пропущено: 0.
- Сумма времени testcase suites в XML: 0,078 с.

Проверенные suites:

- `ArtifactCompatibilityGateTest`: 3/3;
- `CaptureFileStoreTest`: 3/3;
- `ObservationSessionTest`: 1/1;
- `EmergencyAvailabilityPolicyTest`: 2/2;
- `InferenceInputTest`: 1/1;
- `NoModelInferenceEngineTest`: 1/1;
- `SafeInferenceRunnerTest`: 2/2;
- `QualityAndViewValidatorTest`: 2/2.

Emergency access подтверждён тестами
`availableWithoutModel`, `availableAfterTechnicalFailure` и
`technicalFailureKeepsEmergencyRouteAvailable`. Они доказывают доступность
аварийного экрана при `RECOGNITION_UNAVAILABLE` и после
`TECHNICAL_FAILURE`.

`NoModelInferenceEngine` используется как реализация Stage A в
`MushroomViewModel`; его тест подтверждает результат
`RECOGNITION_UNAVAILABLE` без попытки угадать таксон.

Поиск по production/source-коду не обнаружил старых second/third confidence
полей. Safety gate и отдельный unit-тест не обнаружили незарегистрированных
model-assets.

### Android lint

- Ошибок: 0.
- Предупреждений: 15.
- Все предупреждения имеют категорию `GradleDependency` и сообщают только о
  существовании более новых стабильных версий AndroidX/CameraX/Room/Compose
  зависимостей. Версии намеренно не изменялись в рамках финальной верификации.
- Отчёты:
  `android-app/app/build/reports/lint-results-debug.html`,
  `android-app/app/build/reports/lint-results-debug.txt`,
  `android-app/app/build/reports/lint-results-debug.xml`.

### Gradle Wrapper

- Локальный `scripts/validate_gradle_wrapper.py`: PASS.
- CI `Validate Gradle Wrapper` (`gradle/actions/wrapper-validation@v4`): PASS.
- CI `Validate pinned Wrapper contract`: PASS.
- Gradle Wrapper фактически запущен как Gradle 8.7.

### Debug APK

- Путь: `android-app/app/build/outputs/apk/debug/app-debug.apk`.
- Размер: 13 894 498 байт (примерно 13,25 MiB).
- SHA-256:
  `8CFDB730F25F12E67411C2A840F54E67F26B152C0482E69D64432586F79758CC`.

Android release не собирался и не разблокировался. CI-шаг
`Prove Android release is blocked by unapproved medical copy` прошёл, то есть
`verifyEmergencyCopyApproval` ожидаемо отказал в production-допуске.

## Desktop non-production build

`scripts/build_desktop_exe.ps1` запущен без `-Production`. PyInstaller завершил
Analysis, PYZ, PKG, EXE и COLLECT успешно.

- Путь: `dist/GribKontrolDesktop/GribKontrolDesktop.exe`.
- Размер: 5 100 717 байт (примерно 4,86 MiB).
- SHA-256:
  `8525F07273EDAE43A037E9EA62BF6F48F8ADF894053D7016AA0B645C00F3BFE8`.
- Рекурсивный поиск в onedir bundle не обнаружил файлов с model-расширениями
  `.tflite`, `.onnx`, `.pt`, `.pth`, `.ckpt`, `.h5`, `.keras`, `.mlmodel`,
  `.bin`, `.safetensors`.
- Fail-closed поведение подтверждено Python-тестами приложения: default engine
  возвращает `RECOGNITION_UNAVAILABLE`; desktop entry point использует тот же
  `create_app()`.

PyInstaller создал `warn-GribKontrolDesktop.txt` с условными/опциональными и
не-Windows модулями (`pwd`, `grp`, `posix`, `fcntl`, `termios` и аналогичные),
но обязательных import-ошибок и ошибок сборки не было.

Production desktop build не запускался. Его блокировка остаётся в
`build_desktop_exe.ps1`: параметр `-Production` сначала вызывает production
medical gate, который локально ожидаемо завершился кодом 1.

## Safety-гейты и fail-closed

- Forbidden production UI phrases: PASS.
- Unbound model assets: PASS.
- Android network/location permissions: PASS.
- Явность medical placeholder в development: PASS.
- Production medical gate: EXPECTED BLOCK.
- `ArtifactCompatibilityGate`, Python: 4/4 PASS.
- `ArtifactCompatibilityGate`, Android: 3/3 PASS.
- Несовместимый bundle не запускает inference и даёт
  `TECHNICAL_FAILURE`: PASS.
- Отсутствующий model bundle даёт `RECOGNITION_UNAVAILABLE`: PASS.
- Emergency route доступен при отсутствии модели и техническом сбое: PASS.
- Production/release не разблокирован и не собирался локально.

## GitHub Actions

Для commit `c516e1b8390fd2ae2aa56af1a3146c487002c9b5` подключённый GitHub-коннектор
вернул:

- workflow: `CI`;
- run ID: `30612894149`;
- run number: `2`;
- status: `completed`;
- conclusion: `success`.

Jobs и обязательные шаги:

| Job/шаг | Результат |
|---|---|
| `python` | success |
| Python Ruff | success |
| Python tests | success |
| Forbidden UI phrase and unbound model asset gates | success |
| Development medical placeholder gate | success |
| Намеренная production-блокировка | success |
| `android` | success |
| Gradle Wrapper validation | success |
| Pinned Wrapper contract | success |
| Android tests | success |
| Android lint | success |
| Debug APK build | success |
| Намеренная Android release-блокировка | success |
| `desktop` | success |
| Desktop EXE build | success |
| Проверка наличия desktop EXE | success |

Доступ через локальный `gh` отсутствует; токены и permissions не изменялись.
Точный вывод `gh auth status`:

```text
github.com
  X Failed to log in to github.com account dau15271972-sys (keyring)
  - Active account: true
  - The token in keyring is invalid.
  - To re-authenticate, run: gh auth refresh -h github.com
  - To forget about this account, run: gh auth logout -h github.com -u dau15271972-sys
```

Попытка `gh run list` также завершилась:

```text
failed to get runs: Get "https://api.github.com/repos/dau15271972-sys/grib-kontrol/actions/runs?per_page=20&exclude_pull_requests=true&branch=chore%2Fremove-unsafe-recognizer&head_sha=c516e1b8390fd2ae2aa56af1a3146c487002c9b5": proxyconnect tcp: dial tcp 127.0.0.1:9: connectex: No connection could be made because the target machine actively refused it.
```

CI-результаты получены read-only через подключённый GitHub-коннектор; никаких
изменений на GitHub не выполнялось.

## Обнаруженные ошибки и выполненные исправления

Дефектов Stage A в ходе полного прогона не обнаружено, поэтому код, дизайн,
архитектура и safety-политика не изменялись.

Инфраструктурные ограничения проверки:

1. Первый sandboxed-вызов Gradle не смог создать
   `C:\Users\TempAdmin\.gradle\wrapper\dists\gradle-8.7-bin\...\gradle-8.7-bin.zip.lck`
   и вернул `java.nio.file.AccessDeniedException`. Причина — запрет записи
   песочницы в пользовательский Gradle cache, не проект. Повтор с разрешённым
   доступом к локальному Gradle cache успешен; полный Android script затем
   прошёл.
2. `Get-CimInstance Win32_OperatingSystem` был запрещён средой. Версия ОС
   независимо подтверждена выводом Gradle/PyInstaller и
   `[System.Environment]::OSVersion`.
3. `gh` недоступен по причинам, приведённым выше. CI подтверждён GitHub-коннектором.

Исправления исходного кода не потребовались. Safety-файлы не менялись.

## Изменённые файлы и финальное состояние

Единственное намеренное изменение:

- `docs/reports/stage-a-final-verification.md` — этот доказательный отчёт.

`docs/issues/` не изменялся. Дизайн не изменялся. Model/data/network/inference
код не добавлялся. Commit, push, PR, merge и изменения `main` не выполнялись.

Финальный `git diff --stat`:

```text
(пустой вывод: единственный новый файл пока untracked и поэтому обычный
git diff его не включает)
```

Финальный `git status --short --branch`:

```text
## chore/remove-unsafe-recognizer...origin/chore/remove-unsafe-recognizer
?? docs/reports/
```

`git diff --check` завершился кодом 0 без вывода.

## Итог

Stage A прошёл полный локальный и CI-набор обязательной верификации. Все 18
Python-тестов и 15 Android-тестов прошли; lint и debug-сборки успешны; Wrapper,
artifact, UI, permission, emergency и model-asset проверки успешны; production
остаётся fail-closed и намеренно заблокированным.

**STAGE A: CLOSED**
