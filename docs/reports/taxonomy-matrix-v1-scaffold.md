# Taxonomy Matrix v1 scaffold — отчёт

## Итоговый статус

**TAXONOMY MATRIX V1 SCAFFOLD: READY FOR REVIEW**

Это означает только готовность структуры к техническому и экспертному review.
Матрица не заполнена реальными таксонами и не утверждена микологом.

## Исходное состояние и ветка

- Репозиторий: `dau15271972-sys/grib-kontrol`.
- Исходная ветка: `chore/remove-unsafe-recognizer`.
- Исходный и проверенный SHA:
  `cd5d458d59737b317f629b2ee72ac7420aa58fb9`.
- `origin/chore/remove-unsafe-recognizer` перед началом указывал на тот же SHA.
- Исходное рабочее дерево было чистым.
- Создана локальная ветка `data/taxonomy-matrix-v1` от точного исходного SHA.
- Commit, push, PR и merge не выполнялись.

## Созданные файлы

Всего создано 19 файлов:

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

Существующие файлы не изменялись. Предпочтительная структура задания
сохранена без отклонений. Legacy `data/knowledge_base.json` не изменён и явно
не входит в контур Taxonomy Matrix v1.

## Выбранный формат

- UTF-8 CSV для taxa и confusion groups: удобен для табличного экспертного
  заполнения и строгой проверки заголовков.
- UTF-8 JSON для provenance/review ledger: поддерживает несколько структурных
  review-записей.
- JSON Schema draft 2020-12 для машиночитаемых контрактов трёх типов записей.
- Списки в CSV разделяются `|`; пустая строка означает пустой список либо
  отсутствие optional parent.
- CLI использует только Python standard library, детерминирован и не требует
  сети.

Команда без параметров валидирует связный `valid-synthetic` dataset. Для
будущих матриц предусмотрены явные параметры `--taxonomy`,
`--confusion-groups`, `--review-record`, `--schema-dir`.

## Поля taxonomy row

1. `schema_version`;
2. `taxon_id`;
3. `accepted_name`;
4. `rank`;
5. `parent_taxon_id`;
6. `synonyms`;
7. `region_karelia`;
8. `region_murmansk`;
9. `region_kola_peninsula`;
10. `region_northwest_russia`;
11. `regional_status`;
12. `field_id_unsafe`;
13. `dangerous_taxon`;
14. `requires_expert_review`;
15. `confusion_group_ids`;
16. `evidence_status`;
17. `review_status`;
18. `notes_internal`.

Rank enum ограничен значениями `species`, `genus`, `section`, `complex`,
`group`. Review enum ограничен `UNREVIEWED`, `REVIEW_REQUIRED`, `APPROVED`,
`REJECTED`.

## Stable ID

- Taxon ID имеет вид `tx_<ascii_slug>`, group ID — `cg_<ascii_slug>`, review
  ID — `rv_<ascii_slug>`.
- ID создаётся один раз, не меняется при смене accepted name и не
  переиспользуется для другой сущности.
- Merge/split и переименование требуют новой matrix version и review trail.
- Валидатор проверяет pattern и уникальность ID.

## Accepted names и synonyms

- Accepted names уникальны после whitespace normalization и Unicode casefold.
- Один synonym не может принадлежать разным taxa.
- Synonym не может совпадать с accepted name другой записи.
- Порядок synonyms не несёт смысла; дубликаты внутри списка запрещены.
- Synonym не заменяет stable ID и не доказывает региональное присутствие.

## Parent hierarchy

- Пустой parent разрешён для корневой записи.
- Непустой `parent_taxon_id` должен существовать в той же матрице.
- Self-parent и любые циклы отклоняются DFS-проверкой.
- Rank-согласованность не выводится автоматически и требует экспертного
  решения для реальных данных.

## Dangerous confusion groups

Поля: `schema_version`, `group_id`, `group_name_internal`,
`member_taxon_ids`, `dangerous_member_taxon_ids`, `confusion_basis`,
`required_view_types`, `minimum_resolution_rank`, `requires_expert_review`,
`evidence_status`, `review_status`, `notes_internal`.

Правила:

- минимум два member taxa и минимум один dangerous member;
- dangerous members являются subset общего member set;
- все ссылки должны существовать;
- taxon/group ссылки проверяются в обе стороны;
- `requires_expert_review` для группы всегда `true`;
- допустимые view types: `CAP_TOP`, `UNDERSIDE`, `STEM_BASE`, `SIDE`;
- mirror, rotate и crop не входят в enum и не считаются независимыми
  наблюдениями;
- структура не реализует RiskEngine, thresholds или пользовательский итог.

## Provenance

Каждая taxon/group entity должна иметь ledger-запись с:

- schema и matrix version;
- review ID, entity type и entity ID;
- source type;
- bibliographic citation;
- URL или стабильным source locator;
- access date;
- license information;
- contributor ID;
- evidence status;
- review status;
- reviewer ID;
- reviewed date;
- reviewer notes.

Synthetic records имеют `SYNTHETIC_FIXTURE`, `SYNTHETIC` и остаются
`UNREVIEWED`.

## Expert review

`APPROVED` отклоняется без:

- `EVIDENCE_VERIFIED` у entity и review record;
- реального source type;
- citation и source locator;
- access date и license information;
- contributor ID;
- reviewer ID и review date;
- reviewer notes;
- соответствующей `APPROVED` review-записи для entity.

Фиктивные подписи эксперта не создавались. Все synthetic fixtures остаются
`UNREVIEWED`.

## Safety-запреты

SAFETY: taxonomy validator отдельно проверяет property names и enum categories
в JSON Schema, а также CSV headers. Запрещённые имена нормализуются без учёта
регистра, пробелов, дефисов и подчёркиваний:

- `safe`;
- `edible`;
- `can_eat`;
- `можно_есть`;
- `съедобный`;
- `безопасный`.

Проверка намеренно не сканирует документацию, объясняющую этот запрет.
Существующий `scripts/safety_gate.py` не изменялся и не ослаблялся.

## Валидатор

`scripts/validate_taxonomy.py` проверяет:

- обязательные поля и неизвестные колонки/поля;
- типы, constants, enums, patterns, min-items и unique-items из используемого
  JSON Schema subset;
- уникальность taxon/group/review IDs;
- parent existence и циклы;
- duplicate accepted names и synonym conflicts;
- межфайловые confusion links;
- dangerous-member subset;
- completeness и согласованность review ledger;
- полноту `APPROVED` evidence/reviewer данных;
- reviewer, date и explanation для `REJECTED`;
- отсутствие reviewer/date assertions у `UNREVIEWED`;
- реальные ISO calendar dates;
- fail-closed отказ при неизвестном JSON Schema keyword;
- synthetic records остаются `UNREVIEWED`;
- taxonomy-specific safety-запреты.

Ошибки дедуплицируются и сортируются, выводятся понятным списком, exit code при
ошибке ненулевой.

## Автоматические тесты

Добавлено 20 taxonomy tests, включая все 15 обязательных negative/positive
сценариев, проверку shipped invalid fixture, запрет transformed view,
schema-level safety-запрет, пустые templates и ненулевой CLI exit code.

Полный repository pytest:

```text
collected 38 items
38 passed in 0.75s
```

После создания этого отчёта тот же полный pytest-набор повторён: 38/38,
`38 passed in 0.77s`.

Из них:

- существующие Stage A tests: 18;
- новые taxonomy validation tests: 20;
- failed: 0;
- skipped: 0;
- warnings: 0.

## Полный обязательный прогон

| Команда | Результат | Длительность |
|---|---|---:|
| `.venv\Scripts\python.exe -m ruff check .` | PASS, `All checks passed!` | 0,09 с |
| `.venv\Scripts\python.exe -m pytest -ra` | PASS, 38/38 | pytest 0,75 с; процесс 1,11 с |
| `.venv\Scripts\python.exe scripts\validate_taxonomy.py` | PASS, 3 taxa / 1 group / 4 reviews | 0,09 с |
| `.venv\Scripts\python.exe scripts\safety_gate.py` | PASS | 0,40 с |
| `.venv\Scripts\python.exe scripts\medical_placeholder_gate.py` | PASS | 0,06 с |
| `.venv\Scripts\python.exe scripts\validate_gradle_wrapper.py` | PASS | 0,06 с |

Production medical gate не изменялся и не разблокировался.

Первый целевой Ruff-прогон нашёл две строки длиннее 100 символов; были изменены
только переносы строк. Первые sandboxed pytest-попытки не смогли создавать
pytest temp directories (`PermissionError`/ACL); точный обязательный прогон с
разрешённым доступом к системному temp прошёл 38/38. Это ограничение среды, не
ошибка тестов или validator.

## Scope-проверка

- Android files: не изменялись.
- Desktop files: не изменялись.
- `app/`, `templates/`, `assets/`, CameraX, UI и design: не изменялись.
- Inference contracts: не изменялись.
- Существующие safety gates: не изменялись.
- Models, datasets, RiskEngine, open-set, calibration и thresholds: не
  добавлялись.
- Сеть и внешние API: не использовались.
- BioCLIP: не запускался.
- Реальные taxa: не добавлялись. Все новые имена — `Testus`,
  `Testus borealis`, `Testus obscurus` и `Fungus exemplaris`, явно synthetic.

## Известные ограничения

- Каркас содержит только synthetic fixtures и не пригоден как фактическая
  региональная матрица до экспертного заполнения.
- Validator реализует стандартной библиотекой только используемый в трёх
  schemas subset JSON Schema; это не универсальный JSON Schema engine.
- Regional booleans synthetic fixture имеют `false` и не являются
  утверждениями об отсутствии реальных taxa.
- Нет cryptographic signature, trust store или утверждённого reviewer registry.
- Нет taxonomy changelog/migration tool: они потребуются при первой реальной
  matrix version.
- Validator не реализует inference или safety decision policy.

## Вопросы пользователю или микологу

1. Кто может быть reviewer и какой формат reviewer ID является каноническим?
2. Какие источники достаточны для accepted names, synonyms, regional status и
   dangerous confusion membership?
3. Какие license classes допустимы и как фиксировать ограничения reuse?
4. Нужна ли цифровая подпись review record и где хранить trust anchors?
5. Какова политика merge/split/deprecation stable IDs?
6. Какова периодичность повторного review и отзыва устаревших evidence?
7. Требуются ли дополнительные независимые view types после mycologist review?

## Git diff и финальное рабочее дерево

Финальный стандартный `git diff --stat`:

```text
(пустой вывод: все 19 созданных файлов пока untracked)
```

Финальный `git status --short --branch`:

```text
## data/taxonomy-matrix-v1
?? data/taxonomy/README.md
?? data/taxonomy/fixtures/invalid-synthetic/forbidden-column-edible/confusion-groups-v1.csv
?? data/taxonomy/fixtures/invalid-synthetic/forbidden-column-edible/review-record-v1.json
?? data/taxonomy/fixtures/invalid-synthetic/forbidden-column-edible/taxonomy-matrix-v1.csv
?? data/taxonomy/fixtures/valid-synthetic/confusion-groups-v1.csv
?? data/taxonomy/fixtures/valid-synthetic/review-record-v1.json
?? data/taxonomy/fixtures/valid-synthetic/taxonomy-matrix-v1.csv
?? data/taxonomy/schema/confusion-group.schema.json
?? data/taxonomy/schema/review-record.schema.json
?? data/taxonomy/schema/taxonomy-row.schema.json
?? data/taxonomy/templates/confusion-groups-v1.csv
?? data/taxonomy/templates/review-record-v1.json
?? data/taxonomy/templates/taxonomy-matrix-v1.csv
?? docs/reports/taxonomy-matrix-v1-scaffold.md
?? docs/taxonomy/dangerous-confusion-policy.md
?? docs/taxonomy/source-and-review-policy.md
?? docs/taxonomy/taxonomy-matrix-v1-spec.md
?? scripts/validate_taxonomy.py
?? tests/test_taxonomy_validation.py
```

**TAXONOMY MATRIX V1 SCAFFOLD: READY FOR REVIEW**
