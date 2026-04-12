# Онлайн-приложение: определение гриба по фото

В проекте данные разделены на два независимых файла:

- `data/knowledge_base.json` - база знаний (съедобность, опасность, описание, двойники).
- `data/recognition_index.json` - файл распознавания (визуальные признаки для поиска похожего вида).

Финальная выдача результата выполняется только после обязательных 2-го и 3-го тестов:
- 2-й тест: проверка устойчивости распознавания на зеркальной версии фото.
- 3-й тест: проверка устойчивости распознавания на слегка повернутом фото.

## Запуск

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app/main.py
```

Откройте в браузере: `http://localhost:8000`

## Версия Для Компьютера (Windows)

Быстрый запуск desktop-режима:

```powershell
python desktop/run_desktop.py
```

Приложение поднимет локальный сервер и само откроет интерфейс в браузере.

Сборка `.exe`:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build_desktop_exe.ps1
```

Готовый файл:
- `dist/GribKontrolDesktop.exe`

## Android-приложение

В папке `android-app` лежит нативное автономное приложение (Kotlin + Compose), которое работает без интернета:
- делает фото гриба с двух сторон (верх и низ шляпки);
- выполняет локальное распознавание по данным из `assets/knowledge_base.json` и `assets/recognition_index.json`;
- применяет обязательные 2-й и 3-й контрольные тесты;
- автоматически поднимает предупреждение `поганка/ложный гриб` при высоком риске;
- сохраняет историю распознаваний в локальную базу Room (`mushroom_detector.db`).

### Сборка Android

1. Откройте `android-app` в Android Studio.
2. Дождитесь синхронизации Gradle.
3. Запустите `app` на эмуляторе или телефоне.

### Сборка APK (после Sync в Android Studio)

```powershell
cd android-app
powershell -ExecutionPolicy Bypass -File .\scripts\build_apk.ps1 -Variant debug
```

Готовый файл:
- `android-app/app/build/outputs/apk/debug/app-debug.apk`

### Упаковка XAPK

```powershell
cd android-app
powershell -ExecutionPolicy Bypass -File .\scripts\pack_xapk.ps1 -ApkPath .\app\build\outputs\apk\debug\app-debug.apk
```

Готовый файл:
- `android-app/build/outputs/grib-kontrol-v1.0.xapk`

## Как загружать знания

1. Откройте `data/knowledge_base.json`.
2. Добавьте новый вид в блок `species` с ключом `species_id`, например:
   - `name_ru`
   - `name_latin`
   - `edibility`
   - `danger_level`
   - `lookalikes`
   - `notes`
   - `recommendation`

Важно: `species_id` должен совпадать с `species_id` в `data/recognition_index.json`.

## Как обновлять файл распознавания

Подготовьте датасет:

```text
dataset/
  boletus_edulis/
    1.jpg
    2.jpg
  amanita_phalloides/
    1.jpg
  cantharellus_cibarius/
    1.jpg
```

Соберите новый `recognition_index.json`:

```powershell
python scripts/build_recognition_index.py --dataset dataset --out data/recognition_index.json --threshold 0.82
```

После этого перезапустите сервер.

## Важное ограничение

Это MVP. Он помогает ориентироваться, но не должен использоваться как единственный источник для решения “есть гриб или нет”.
