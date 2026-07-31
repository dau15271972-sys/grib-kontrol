# Taxonomy Matrix v1 — техническая спецификация каркаса

## Назначение и границы

Taxonomy Matrix v1 — версионируемый справочный граф таксонов и внутренних
опасных confusion-групп для будущего экспертного заполнения. Каркас не является
моделью, не выполняет inference, не назначает пользовательский результат и не
даёт разрешений на сбор, приготовление или употребление.

В текущем наборе есть только явно синтетические имена. Реальные записи можно
добавлять лишь по правилам provenance и expert review.

## Формат

- Taxa: UTF-8 CSV `taxonomy-matrix-v1.csv`.
- Confusion groups: UTF-8 CSV `confusion-groups-v1.csv`.
- Provenance/review ledger: UTF-8 JSON `review-record-v1.json`.
- Машиночитаемые контракты: JSON Schema draft 2020-12 в
  `data/taxonomy/schema/`.
- Значения списков в CSV разделяются `|`; порядок не несёт смысла.
- Пустой `parent_taxon_id` обозначает корневую запись.
- Nullable review fields представлены JSON `null`; даты имеют формат ISO
  `YYYY-MM-DD` и должны быть существующими календарными датами.

CSV выбран как формат экспертного табличного ввода, а JSON — для вложенного
ledger из review-записей. Валидатор приводит значения CSV к типам JSON Schema и
проверяет межфайловые связи.

## Поля taxonomy row

| Поле | Тип и правило |
|---|---|
| `schema_version` | Строго `1.0.0` |
| `taxon_id` | Неизменяемый внутренний ID `tx_<slug>` |
| `accepted_name` | Непустое принятое имя; уникально без учёта регистра |
| `rank` | `species`, `genus`, `section`, `complex` или `group` |
| `parent_taxon_id` | Пусто или существующий `taxon_id`; циклы запрещены |
| `synonyms` | Уникальный список имён через `|` |
| `region_karelia` | Boolean региональный факт |
| `region_murmansk` | Boolean региональный факт |
| `region_kola_peninsula` | Boolean региональный факт |
| `region_northwest_russia` | Boolean региональный факт |
| `regional_status` | `NOT_ASSESSED`, `REPORTED`, `VERIFIED`, `EXCLUDED` |
| `field_id_unsafe` | Внутренний флаг ненадёжности полевой идентификации |
| `dangerous_taxon` | Внутренний опасный контур; не пользовательский итог |
| `requires_expert_review` | Обязательность экспертного review |
| `confusion_group_ids` | Список существующих `group_id` через `|` |
| `evidence_status` | `NO_EVIDENCE`, `SOURCE_RECORDED`, `EVIDENCE_VERIFIED`, `SYNTHETIC` |
| `review_status` | Один из четырёх утверждённых review-статусов |
| `notes_internal` | Только внутренние пояснения |

## Stable ID

- ID создаётся один раз как непрозрачный ASCII slug с префиксом `tx_` или
  `cg_` и больше не переиспользуется.
- Переименование accepted name не меняет ID.
- Слияние или разделение таксонов оформляется новой версией и review-записью;
  старый ID не назначается другой сущности.
- Регистр, пробелы и Unicode не допускаются в ID; используются `[a-z0-9_]`.

## Synonyms

- Synonym нормализуется удалением внешних пробелов и сравнением через
  Unicode `casefold`.
- Один synonym не может принадлежать двум разным taxa.
- Synonym не может совпадать с accepted name другой записи.
- Accepted name не может повторяться без учёта регистра.
- Synonyms не заменяют stable ID и не используются как доказательство
  регионального присутствия.

## Parent hierarchy

- Ссылка parent должна существовать в той же версии матрицы.
- Self-parent и любой цикл запрещены.
- Корневые записи имеют пустой parent.
- Каркас не выводит биологические rank-отношения автоматически: соответствие
  parent/rank должно быть подтверждено источником и reviewer.

## Версионирование

`schema_version` версионирует формат, `matrix_version` в review ledger —
конкретный набор данных. Несовместимое изменение полей требует новой major
schema version. Изменение фактов или связей требует новой matrix version и
review trail.

## Валидатор

`scripts/validate_taxonomy.py` работает детерминированно и offline. Он
проверяет JSON Schema subset, заголовки, enum, ID, имена, synonyms, иерархию,
confusion graph и review ledger. Ошибки сортируются перед выводом; любой список
ошибок даёт ненулевой exit code.

Schema является источником обязательных полей, типов, enum, patterns, arrays и
nullable semantics. Валидатор fail-closed отклоняет неизвестный schema keyword,
чтобы новое ограничение не могло быть молча проигнорировано. В текущем
контракте default values отсутствуют; пропущенное required value не заполняется
автоматически.
