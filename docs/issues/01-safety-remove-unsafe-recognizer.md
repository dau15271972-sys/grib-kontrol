# [SAFETY] Удалить небезопасный распознаватель и технический долг

## Цель

Завершить Stage A: удалить RGB histogram/cosine recognizer и fail-closed
перевести Android, Python и desktop в `RECOGNITION_UNAVAILABLE`.

## Scope

Удаление `recognition_index`, mirror/rotate checks и second/third confidence;
no-model contracts; CameraX `ImageCapture`; emergency access; README, Wrapper и
CI.

## Запреты

Не добавлять новую модель, сырые confidence, статус `SAFE`, сеть в inference
path или ослабление reject.

## Зависимости

Нет. Задача блокирует все следующие ML-этапы.

## Критерии приёмки

Старого классификатора и индекса нет; без модели оба контура возвращают только
`RECOGNITION_UNAVAILABLE`; `TECHNICAL_FAILURE` не создаёт разрешающий вывод.

## Тесты

Python tests/lint; Android unit/lint/APK; desktop EXE; forbidden phrase, unbound
asset, compatibility и emergency tests.

## Ожидаемые артефакты

Код Stage A, полный тест-отчёт и git diff без публикации до отдельной команды.
