# [M0] Провести BioCLIP 2.5 Huge baseline

## Цель

Получить воспроизводимый research-only baseline для регионального датасета.

## Scope

Offline batch evaluation; species/genus/group metrics; dangerous recall;
open-set и calibration diagnostics.

## Запреты

Не встраивать Huge-модель в Android, не объявлять production readiness по
accuracy и не выводить baseline пользователю.

## Зависимости

Stage A, лицензированный dataset split и taxonomy matrix v1.

## Критерии приёмки

Зафиксированы версии, seeds, split и safety-weighted metrics; отдельно показаны
false-low-risk и dangerous-confusion failures.

## Тесты

Reproducibility run, leakage checks, per-class/bootstrap intervals, OOD и
dangerous-recall evaluation.

## Ожидаемые артефакты

Research report, immutable config, hashes, raw metrics и model card
`NOT FOR PRODUCTION`.
