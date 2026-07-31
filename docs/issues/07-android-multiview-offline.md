# [ANDROID] Реализовать многоракурсный автономный путь

## Цель

Реализовать offline capture → quality → compatibility → inference → policy
цепочку по независимым ракурсам.

## Scope

CameraX, `ObservationSession`, required views, quality feedback, ephemeral
storage и accessibility.

## Запреты

Не считать mirror/rotate независимым наблюдением, не хранить фото/GPS без
consent и не добавлять сеть в inference path.

## Зависимости

Stage A, approved bundle, `ArtifactCompatibilityGate` и `ResultPolicy`.

## Критерии приёмки

Пропуски дают `NEED_MORE_PHOTOS`; полный путь работает в airplane mode.

## Тесты

Unit/UI/instrumentation, process death, permission denial, low storage и
airplane-mode acceptance.

## Ожидаемые артефакты

Android implementation, UX review, privacy record и device test report.
