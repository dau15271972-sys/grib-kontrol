# [DATA] Создать таксономическую матрицу v1

## Цель

Создать утверждаемую человеком матрицу таксонов Северо-Запада России и опасных
confusion-групп.

## Scope

Species/genus/section/group mappings, regional relevance, `field_id_unsafe`,
dangerous twins и provenance.

## Запреты

Не добавлять вид только заменой прототипа и не считать отсутствие записи
доказательством безопасности.

## Зависимости

Mycologist review, политика источников и лицензий.

## Критерии приёмки

Каждая строка имеет stable ID, accepted name, synonyms, rank, region, safety
flags, reviewer и evidence.

## Тесты

Schema validation, duplicate/synonym tests и dangerous-group completeness audit.

## Ожидаемые артефакты

Versioned matrix v1, schema, changelog и signed review record.
