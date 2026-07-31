# [SAFETY] Реализовать version-lock и compatibility matrix

## Цель

Сделать обязательную атомарную совместимость model/taxonomy/calibration/risk и
input contracts.

## Scope

Signed manifest schema, hashes, allowed matrix, rollback behavior и интеграция
`ArtifactCompatibilityGate`.

## Запреты

Не запускать inference при частичном, несовместимом или недоверенном bundle.

## Зависимости

Stage A gate skeleton, signing design и artifact registry.

## Критерии приёмки

Любая несовместимость fail-closed; обновление атомарно; причины отказа
аудитируемы.

## Тесты

Все mismatch-комбинации, tamper/hash, partial update и rollback tests.

## Ожидаемые артефакты

Manifest schema, compatibility matrix, verifier, release procedure и audit log.
