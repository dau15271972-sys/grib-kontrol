# [SAFETY] Реализовать RiskEngine и dangerous confusion graph

## Цель

Создать независимый dangerous contour и консервативный `ResultPolicy`.

## Scope

Mycologist-approved deadly taxa/sections/groups, thresholds, confusion graph и
trusted-signal precedence.

## Запреты

Не опираться только на top-1, не усреднять опасный сигнал качественного ракурса
и не выдавать `SAFE`.

## Зависимости

Taxonomy matrix, calibrated outputs, dangerous validation set и human review.

## Критерии приёмки

Qualifying dangerous signal даёт `HIGH_RISK`; exact species скрывается при
`field_id_unsafe`.

## Тесты

Golden/adversarial cases, confusion tests, per-angle precedence, false-low-risk
и minimum-N gates.

## Ожидаемые артефакты

Versioned risk rules, graph, review record, tests и safety case.
