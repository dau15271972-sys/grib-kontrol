# [DATA] Создать pipeline GBIF/iNaturalist

## Цель

Построить воспроизводимый pipeline лицензированных наблюдений с provenance.

## Scope

API ingestion вне mobile inference, license filtering, deduplication,
geospatial/time policy и независимые train/validation/test splits.

## Запреты

Не использовать фото без совместимой лицензии, не сохранять лишние
персональные/GPS-данные и не допускать leakage.

## Зависимости

Taxonomy matrix v1, provider terms и data-retention decision.

## Критерии приёмки

Каждое изображение трассируется до источника/лицензии; rejected records
объяснимы; splits независимы.

## Тесты

Contract tests, license gate, hash dedupe, leakage audit и dry-run fixture.

## Ожидаемые артефакты

Pipeline code, lockfile, manifests, provenance ledger и data card.
