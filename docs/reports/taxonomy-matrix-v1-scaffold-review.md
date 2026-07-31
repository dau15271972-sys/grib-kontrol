# Taxonomy Matrix v1 scaffold — независимая ревизия

## Итоговый вердикт

**TAXONOMY MATRIX V1 SCAFFOLD REVIEW: PASSED**

Все обязательные проверки прошли. Подтверждённые дефекты каркаса исправлены и
закрыты regression-тестами. Критических расхождений между schemas, шаблонами,
fixtures и валидатором не осталось.

Этот вердикт относится только к техническому каркасу. Он не утверждает
корректность реальных таксонов, не является микологическим review и не разрешает
пользовательские выводы о безопасности или употреблении грибов.

## Исходное состояние

- Репозиторий: `dau15271972-sys/grib-kontrol`.
- Ветка: `data/taxonomy-matrix-v1`.
- Проверенный исходный SHA:
  `cd5d458d59737b317f629b2ee72ac7420aa58fb9`.
- Исходный каркас: 19 untracked-файлов; commit, push и PR отсутствовали.
- `git check-ignore` подтвердил, что новые taxonomy-пути не игнорируются.
- До ревизии tracked-файлы не были изменены.
- `data/knowledge_base.json` не изменён.
- Базовый полный pytest: `38 passed` (18 существующих тестов и 20 исходных
  taxonomy-тестов).

## Проверенные материалы

Входные инструкции и правила:

- `AGENTS.md`;
- исходное задание на Taxonomy Matrix v1;
- задание на независимую ревизию.

Все 19 файлов исходного каркаса:

- `data/taxonomy/README.md`;
- `data/taxonomy/schema/taxonomy-row.schema.json`;
- `data/taxonomy/schema/confusion-group.schema.json`;
- `data/taxonomy/schema/review-record.schema.json`;
- `data/taxonomy/templates/taxonomy-matrix-v1.csv`;
- `data/taxonomy/templates/confusion-groups-v1.csv`;
- `data/taxonomy/templates/review-record-v1.json`;
- `data/taxonomy/fixtures/valid-synthetic/taxonomy-matrix-v1.csv`;
- `data/taxonomy/fixtures/valid-synthetic/confusion-groups-v1.csv`;
- `data/taxonomy/fixtures/valid-synthetic/review-record-v1.json`;
- `data/taxonomy/fixtures/invalid-synthetic/forbidden-column-edible/taxonomy-matrix-v1.csv`;
- `data/taxonomy/fixtures/invalid-synthetic/forbidden-column-edible/confusion-groups-v1.csv`;
- `data/taxonomy/fixtures/invalid-synthetic/forbidden-column-edible/review-record-v1.json`;
- `docs/taxonomy/taxonomy-matrix-v1-spec.md`;
- `docs/taxonomy/source-and-review-policy.md`;
- `docs/taxonomy/dangerous-confusion-policy.md`;
- `scripts/validate_taxonomy.py`;
- `tests/test_taxonomy_validation.py`;
- `docs/reports/taxonomy-matrix-v1-scaffold.md`.

Существующий CI, runtime и защитные проверки:

- `.github/workflows/ci.yml`;
- `pyproject.toml`;
- `app/inference.py`, `app/main.py`, `app/artifacts.py`;
- `scripts/safety_gate.py`;
- `scripts/medical_placeholder_gate.py`;
- `scripts/validate_gradle_wrapper.py`;
- `tests/test_android_design_reference.py`;
- `tests/test_app.py`;
- `tests/test_artifacts.py`;
- `tests/test_gradle_wrapper.py`;
- `tests/test_medical_placeholder_gate.py`;
- `tests/test_safety_gate.py`;
- `data/knowledge_base.json`.

## Найденные дефекты и исправления

| Severity | Подтверждённый дефект | Влияние | Минимальное исправление и regression coverage |
|---|---|---|---|
| HIGH / SAFETY | Запрещённые taxonomy-имена сравнивались только по точному `casefold`; варианты с пробелами, дефисами и подчёркиваниями обходили запрет. | В schema или CSV мог появиться пользовательский разрешающий safety-контракт под эквивалентным именем. | Добавлена единая нормализация регистра и разделителей для CSV headers, JSON property names и enum categories; добавлены варианты на английском и русском. |
| MEDIUM | Поддерживаемый валидатором subset JSON Schema не аудировался; неизвестный keyword мог быть молча проигнорирован. | Schema могла ужесточиться без соответствующей проверки данных валидатором. | Добавлен fail-closed аудит keywords, types, formats, root object, `additionalProperties=false` и равенства `required`/`properties`; mutation-тест с `maxLength`. |
| MEDIUM | Даты проверялись только регулярным выражением. | Невозможные календарные даты, например `2026-02-30`, принимались. | Для `format: date` добавлен `date.fromisoformat`; обе даты review schema получили явный `format`; добавлен negative test. |
| MEDIUM | Review-инварианты были неполны для `REJECTED` и `UNREVIEWED`. | Отклонение могло не иметь автора/даты/объяснения, а непроверенная запись могла утверждать фиктивного reviewer. | `REJECTED` требует reviewer, реальную дату и notes; `UNREVIEWED` запрещает reviewer/date assertions; добавлены тесты и документация. |
| MEDIUM | Повтор synonyms внутри одной строки проверялся без нормализации. | Один synonym мог повторяться с другим регистром или количеством пробелов. | Добавлена нормализованная внутристатейная уникальность и regression test. |
| MEDIUM | Шесть CSV содержали лишнюю пустую физическую строку, которую прежний reader молча пропускал. | Физический формат fixtures/templates был неоднозначен и мог скрывать повреждённые строки. | Пустые строки удалены; CSV reader сделан строгим и отклоняет blank rows; добавлены точные проверки количества физических строк. |
| MEDIUM | Реальный taxonomy validator не запускался отдельным CI-step. | Unit-тесты могли остаться зелёными при повреждении versioned shipped templates/fixtures. | В Python job добавлен отдельный шаг `python scripts/validate_taxonomy.py`; остальные jobs и gates не менялись. |
| LOW | Часть ошибок malformed/missing input не всегда содержала имя файла и объект. | Диагностика CLI была недостаточно локализована. | Сообщения дополнены именем файла и, когда строка разобрана, `object=<id>`; добавлены CLI/malformed/missing tests. |
| LOW | Self-parent обнаруживался только как общий цикл. | Ошибка была корректно отклонена, но без наиболее точной причины. | Добавлена явная self-parent диагностика и отдельный regression test. |

## Schema–validator parity

Общие свойства контракта:

| Аспект | Schema/template | Validator | Результат |
|---|---|---|---|
| Обязательные поля | Все schema fields входят в `required`; CSV headers совпадают с порядком `properties`. | Контракт schema проверяется при каждом запуске; missing и unknown fields отклоняются. | PASS |
| Типы и nullable | JSON Schema types являются источником истины; nullable задаётся `string|null`. | CSV scalar/list/boolean и JSON null преобразуются явно, без скрытых defaults. | PASS |
| Enum/const/pattern | Заданы в schemas. | Применяются универсальным schema-subset validator. | PASS |
| Массивы | CSV использует документированный `|`; JSON использует native arrays. | Проверяются item rules, `minItems`, `uniqueItems`; пустая CSV-строка означает пустой список. | PASS |
| Неизвестные свойства | `additionalProperties=false`. | Unknown CSV columns и JSON fields отклоняются. | PASS |
| Defaults | В schemas отсутствуют. | Значения не дополняются и не подменяются. Keyword `default` и другие неподдерживаемые keywords отклоняются fail-closed. | PASS |
| Даты | `pattern` плюс `format: date`. | Проверяются синтаксис и реальная календарная дата. | PASS |
| Review rules | Status enums заданы schema; межполевая семантика описана policy. | `APPROVED`, `REJECTED`, `UNREVIEWED`, evidence и target consistency проверяются явно. | PASS |

Taxonomy row, поле за полем:

| Поле | Schema-проверка | Дополнительная проверка валидатора |
|---|---|---|
| `schema_version` | required string, const `1.0.0` | Совпадает с поддерживаемой версией. |
| `taxon_id` | required non-null string, `tx_...` pattern | Не пустой/whitespace-only, уникален. |
| `accepted_name` | required string, `minLength=1` | Нормализованная уникальность; collisions с synonyms отклоняются. |
| `rank` | required enum | Только schema enum; произвольная биологическая parent-rank политика не добавлена. |
| `parent_taxon_id` | required string/null, `tx_...` pattern | Пустой CSV → null; existence, self-parent и циклы любой длины. |
| `synonyms` | required unique string array | `|` format; нормализованные дубликаты и межтаксонные collisions. |
| `region_karelia` | required boolean | Строгие `true`/`false`; synthetic false не трактуется как реальное отсутствие. |
| `region_murmansk` | required boolean | То же. |
| `region_kola_peninsula` | required boolean | То же. |
| `region_northwest_russia` | required boolean | То же. |
| `regional_status` | required enum | Unknown status отклоняется. |
| `field_id_unsafe` | required boolean | Не является пользовательским verdict. |
| `dangerous_taxon` | required boolean | `false` не трактуется как безопасность. |
| `requires_expert_review` | required boolean | Согласуется с review policy. |
| `confusion_group_ids` | required unique patterned array | Все ссылки существуют и согласованы в обе стороны. |
| `evidence_status` | required enum | Согласуется с review record; synthetic остаётся `SYNTHETIC`. |
| `review_status` | required enum | Согласуется с review record и status-инвариантами. |
| `notes_internal` | required string | Не является пользовательским safety output. |

Confusion group, поле за полем:

| Поле | Schema-проверка | Дополнительная проверка валидатора |
|---|---|---|
| `schema_version` | required string, const `1.0.0` | Совпадает с поддерживаемой версией. |
| `group_id` | required string, `cg_...` pattern | Уникален. |
| `group_name_internal` | required string, `minLength=1` | Только внутреннее имя. |
| `member_taxon_ids` | required unique array, минимум 2 | Все taxa существуют; повторы отклоняются. |
| `dangerous_member_taxon_ids` | required unique array, минимум 1 | Все taxa существуют и входят в общий member set. |
| `confusion_basis` | required enum | Unknown value отклоняется. |
| `required_view_types` | required unique enum array, минимум 1 | Только независимые views; `MIRROR`, `ROTATE`, `CROP` отклоняются. |
| `minimum_resolution_rank` | required enum | Unknown rank отклоняется; произвольная parent-rank политика не добавлена. |
| `requires_expert_review` | required boolean, const `true` | Всегда true. |
| `evidence_status` | required enum | Согласуется с review record. |
| `review_status` | required enum | Согласуется с review record и status-инвариантами. |
| `notes_internal` | required string | Не является пользовательским safety output. |

Review record, поле за полем:

| Поле | Schema-проверка | Дополнительная проверка валидатора |
|---|---|---|
| `schema_version` | required string, const `1.0.0` | Совпадает с поддерживаемой версией. |
| `matrix_version` | required semver-like string | Согласован внутри ledger. |
| `review_id` | required string, `rv_...` pattern | Уникален. |
| `entity_type` | required enum | Только `TAXON`/`CONFUSION_GROUP`. |
| `entity_id` | required non-empty string | Target существует и соответствует entity type. |
| `source_type` | required enum | Synthetic/real-source ограничения применяются для approval. |
| `bibliographic_citation` | required string/null | Для `APPROVED` требуется непустое значение. |
| `source_locator` | required string/null | Для `APPROVED` требуется непустое значение. |
| `accessed_date` | required string/null, date pattern/format | Реальная дата; для `APPROVED` обязательна. |
| `license_info` | required string/null | Для `APPROVED` требуется непустое значение. |
| `contributor_id` | required non-empty string | Для approved provenance не может быть пустым. |
| `evidence_status` | required enum | `APPROVED` требует `EVIDENCE_VERIFIED`; согласуется с entity. |
| `review_status` | required enum | Согласуется с entity; применяются status-инварианты. |
| `reviewer_id` | required string/null | Обязателен для `APPROVED`/`REJECTED`, запрещён для `UNREVIEWED`. |
| `reviewed_date` | required string/null, date pattern/format | Реальная дата; обязательна для `APPROVED`/`REJECTED`, запрещена для `UNREVIEWED`. |
| `reviewer_notes` | required string/null | Обязательны для `APPROVED`/`REJECTED`. |

## Data-integrity audit

- Taxa: ID uniqueness/format, parent existence, explicit self-parent, arbitrary
  cycles, normalized accepted-name uniqueness, normalized synonym uniqueness,
  accepted-name/synonym and cross-taxon synonym collisions, rank enum and
  confusion-group references — PASS.
- Confusion groups: group uniqueness, member/dangerous-member uniqueness,
  existence, subset relation, minimum sizes, allowed independent views,
  minimum rank and bidirectional references — PASS.
- Review records: review ID uniqueness, target existence/type, unknown fields,
  real ISO dates, all status/evidence invariants and entity consistency — PASS.
- Six JSON files parse with the standard `json` parser — PASS.
- Six CSV files parse with strict standard `csv`; UTF-8, exact headers and no
  blank physical rows — PASS.
- Exact CSV data-row counts: templates 0/0, valid synthetic taxonomy/group 3/1,
  invalid synthetic taxonomy/group 1/0.
- Все fixture-имена остаются явно synthetic; реальные taxa, утверждения и
  datasets не добавлялись.

## Safety-аудит

- SAFETY: запрещённые имена `safe`, `edible`, `can_eat`, `можно_есть`,
  `съедобный`, `безопасный` отклоняются без учёта регистра, пробелов, дефисов и
  подчёркиваний в CSV headers, JSON property names и enum categories — PASS.
- Документация, описывающая сам запрет, намеренно не сканируется как contract и
  не создаёт ложное срабатывание.
- `dangerous_taxon=false` не означает безопасность — явно задокументировано.
- Отсутствие taxon в dangerous group не означает низкий риск — явно
  задокументировано.
- `APPROVED` означает только review evidence record, не разрешение на
  употребление — явно задокументировано.
- Taxonomy Matrix не подключена к production inference.
- Без production bundle runtime по-прежнему возвращает
  `RECOGNITION_UNAVAILABLE`; fail-closed тесты проходят.
- Сеть не использовалась; новых network permissions/imports нет.
- Существующий `scripts/safety_gate.py` не изменён: PASS.
- Production medical gate не разблокирован и не изменён: PASS.

## CLI-аудит

Реальные subprocess-вызовы из корня репозитория:

| Сценарий | Exit code | Результат |
|---|---:|---|
| default valid synthetic fixture | 0 | `3 taxa, 1 confusion group(s), 4 review record(s)` |
| shipped invalid fixture | 1 | Ошибка содержит `taxonomy-matrix-v1.csv` и `forbidden column: edible`. |
| `--help` | 0 | Все четыре path-параметра документированы. |
| missing input | 1 | Имя отсутствующего файла присутствует в сообщении. |
| malformed JSON/CSV | 1 | Имя файла присутствует; исключение обработано. |

Ошибки дедуплицируются и сортируются детерминированно. Хеши input fixtures до и
после subprocess-вызовов совпали; временные `.tmp`/`.bak` файлы не созданы. CLI
использует только Python standard library и не требует сети или locale-specific
парсинга.

## CI-аудит

В Python job добавлен ровно один отдельный обязательный шаг:

```yaml
- name: Validate Taxonomy Matrix v1
  run: python scripts/validate_taxonomy.py
```

Явный шаг нужен даже при наличии pytest: он проверяет именно versioned shipped
schemas/templates/fixtures с default CLI paths и не позволяет unit fixtures
скрыть их повреждение. Остальные CI jobs, команды и gates не изменены и не
ослаблены.

## Тесты до и после ревизии

| Набор | До | После |
|---|---:|---:|
| Существующие Stage A tests | 18 | 18 |
| Taxonomy validation tests | 20 | 59 |
| Полный pytest | 38 | 77 |

Итог: `77 passed`, failed/skipped/warnings — 0.

Добавленные тесты покрывают все обязательные negative/positive сценарии,
реальный CLI, schema mutation/fail-closed parity, нормализацию safety-терминов,
физический CSV-формат и неизменность inputs.

## Полный обязательный прогон

| Команда | Результат |
|---|---|
| `.venv\Scripts\python.exe -m ruff check .` | PASS, `All checks passed!` |
| `.venv\Scripts\python.exe -m pytest -ra` | PASS, `77 passed in 1.23s` |
| `.venv\Scripts\python.exe scripts\validate_taxonomy.py` | PASS, 3 taxa / 1 group / 4 reviews |
| `.venv\Scripts\python.exe scripts\safety_gate.py` | PASS, `Safety source gates passed.` |
| `.venv\Scripts\python.exe scripts\medical_placeholder_gate.py` | PASS, development placeholder remains explicit |
| `.venv\Scripts\python.exe scripts\validate_gradle_wrapper.py` | PASS, files/checksums valid |
| `python -m json.tool` для каждого из 6 JSON | PASS |
| strict `csv` parse для каждого из 6 CSV | PASS |
| `git diff --check` | PASS; только информационное LF→CRLF warning для CI worktree |
| отдельный UTF-8/trailing-whitespace/final-newline аудит untracked-файлов | PASS |

## Открытые вопросы

Не блокируют технический scaffold и должны решаться до первой реальной matrix:

1. Миколог должен утвердить parent/rank compatibility policy; произвольное
   правило в валидатор не добавлялось.
2. Нужны утверждённые источники, лицензии и reviewer identities для реальных
   данных.
3. До real-data rollout нужны reviewer registry/trust policy, taxonomy changelog
   и migration/versioning procedure.
4. Unicode normalization за пределами согласованного casefold/whitespace
   контракта требует отдельного решения до импорта внешних данных.

## Правило предотвращения повторения

Будущее принятие taxonomy-контракта требует одновременно: schema-keyword
fail-closed mutation tests, separator/case safety mutations, subprocess CLI test,
строгую проверку физических CSV-строк и отдельный CI invocation shipped data.
Одних happy-path unit tests недостаточно.

## Новые и изменённые файлы

Изменённый tracked-файл:

- `.github/workflows/ci.yml` — только отдельный taxonomy validation step.

Исходные 19 untracked-файлов каркаса остаются untracked; в ходе ревизии
минимально исправлены validator, tests, review schema, шесть CSV и связанная
документация. Дополнительно создан только этот отчёт:

- `docs/reports/taxonomy-matrix-v1-scaffold-review.md`.

Не изменены `data/knowledge_base.json`, production runtime, Android, desktop,
CameraX, UI/design, существующие safety gates и medical gate.

## `git diff --stat`

Untracked-файлы обычный `git diff --stat` не показывает:

```text
 .github/workflows/ci.yml | 2 ++
 1 file changed, 2 insertions(+)
```

## `git status --short --branch`

Ожидаемый статус после создания этого отчёта:

```text
## data/taxonomy-matrix-v1
 M .github/workflows/ci.yml
?? data/taxonomy/
?? docs/reports/taxonomy-matrix-v1-scaffold-review.md
?? docs/reports/taxonomy-matrix-v1-scaffold.md
?? docs/taxonomy/
?? scripts/validate_taxonomy.py
?? tests/test_taxonomy_validation.py
```

Commit, push, PR и merge в рамках ревизии не выполнялись.
