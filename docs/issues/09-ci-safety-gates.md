# [CI] Добавить обязательные safety-гейты

## Цель

Сделать safety-проверки обязательными для каждого изменения и release candidate.

## Scope

Forbidden phrases/statuses, unbound assets, compatibility, calibration
provenance, emergency access и build/test matrix.

## Запреты

Не разрешать bypass/allow-failure и не считать отсутствующий тест успешным.

## Зависимости

Stage A source gates, CI permissions и protected-branch configuration.

## Критерии приёмки

Нарушение блокирует merge; отчёты сохраняются; версии гейтов закреплены.

## Тесты

Positive/negative fixtures, clean clone run и deliberate-failure drill.

## Ожидаемые артефакты

Workflow files, gate scripts, fixtures, branch-protection checklist и reports.
