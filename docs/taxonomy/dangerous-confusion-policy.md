# Taxonomy Matrix v1 — dangerous confusion policy

## Назначение

Dangerous confusion group хранит проверяемую связь между taxa, которые нельзя
надёжно разделить в заданном полевом контексте. Это только справочная структура
данных: она не является RiskEngine, не задаёт пороги и не выдаёт
пользовательский итог.

## Поля группы

- `schema_version` — строго `1.0.0`;
- `group_id` — постоянный `cg_<slug>`;
- `group_name_internal` — непустое внутреннее имя;
- `member_taxon_ids` — минимум два существующих taxon ID;
- `dangerous_member_taxon_ids` — минимум один ID и только subset members;
- `confusion_basis` — ограниченная категория основания связи;
- `required_view_types` — независимые типы ракурсов;
- `minimum_resolution_rank` — минимальный допустимый taxonomic rank;
- `requires_expert_review` — всегда `true`;
- `evidence_status`, `review_status`, `notes_internal`.

## Независимые ракурсы

Разрешены только значения, совпадающие с capture contract Stage A:

- `CAP_TOP`;
- `UNDERSIDE`;
- `STEM_BASE`;
- `SIDE`.

Mirror, rotate и crop одного исходного изображения не являются независимыми
наблюдениями и не входят в enum. Преобразование не может удовлетворить
требование второго ракурса.

## Целостность графа

- Каждый member и dangerous member должен существовать в taxonomy matrix.
- Dangerous members должны входить в общий member set.
- Ссылка двусторонняя: group содержит taxon, а taxon содержит group ID.
- Group ID уникален.
- Группа без expert review, evidence trail или объяснения основания не может
  быть `APPROVED`.

## Safety boundary

Флаг `dangerous_taxon` и membership группы — внутренние проверяемые факты. Они
не преобразуются этим scaffold в `HIGH_RISK`, разрешение или иной результат.
Любая будущая policy-логика, приоритеты сигналов и thresholds относятся к
отдельному safety-reviewed этапу RiskEngine.

SAFETY: значение `dangerous_taxon = false` не доказывает отсутствие опасности.
Отсутствие taxon в dangerous confusion group также не означает низкий риск:
оно может отражать неполноту или неутверждённость матрицы. Ни одно из этих
условий не может использоваться как разрешающий пользовательский вывод.
