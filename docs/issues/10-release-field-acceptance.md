# [RELEASE] Провести закрытую и полевую приёмку

## Цель

Провести независимую закрытую и полевую приёмку до production release.

## Scope

Frozen test, региональные field sessions, usability, accessibility, offline
behavior, emergency path и safety ceilings.

## Запреты

Не менять false-high-risk ceiling после итогового теста, не засчитывать ноль
false-low-risk при недостаточном `N` и не скрывать failures.

## Зависимости

Approved bundle, CI gates, mycologist/medical-text review и release candidate.

## Критерии приёмки

Заранее заданные ceilings/`N` выполнены; deviations documented; решение
подписано ответственными reviewers.

## Тесты

Blinded frozen evaluation, field protocol, airplane-mode/device matrix,
emergency drills и rollback test.

## Ожидаемые артефакты

Acceptance protocol, raw results, signed decision, limitations и rollback
package.
