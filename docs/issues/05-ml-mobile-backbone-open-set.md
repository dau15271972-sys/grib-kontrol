# [ML] Сравнить мобильные backbone и open-set

## Цель

Сравнить мобильные backbone и reject/open-set подходы по safety-weighted
метрикам.

## Scope

Latency/memory/size, calibration compatibility, OOD rejection и dangerous
recall на целевых устройствах.

## Запреты

Не заменять open-set обычным softmax unknown-классом, не снижать thresholds
после итогового теста и не выбирать по top-1 accuracy.

## Зависимости

M0 baseline, frozen dataset split и taxonomy/confusion graph.

## Критерии приёмки

Выбор обоснован false-low-risk, false-high-risk, dangerous recall, calibration,
OOD и device constraints.

## Тесты

Frozen evaluation, device benchmarks, bootstrap intervals, ablations и hashes.

## Ожидаемые артефакты

Comparison report, candidate cards, configs и explicit no-go findings.
