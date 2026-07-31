# Taxonomy Matrix v1 scaffold

Эта директория содержит только структуру для будущего экспертного заполнения.
Реальные таксоны и региональные утверждения в каркас не входят.

## Состав

- `schema/` — машиночитаемые JSON Schema для строки таксона, confusion-группы
  и записи provenance/review;
- `templates/` — пустые шаблоны CSV и JSON;
- `fixtures/valid-synthetic/` — связный набор вымышленных записей, который
  должен проходить валидацию;
- `fixtures/invalid-synthetic/` — намеренно ошибочные наборы для negative tests.

CSV-файлы имеют UTF-8 encoding и запятую как разделитель колонок. Значения в
списочных полях разделяются вертикальной чертой (`|`). Пустая строка означает
пустой список или отсутствие optional parent. Nullable-поля review ledger
задаются JSON-значением `null`, а даты — реальной календарной датой ISO
`YYYY-MM-DD`.

SAFETY: запрещённые contract names сравниваются без учёта регистра, пробелов,
дефисов и подчёркиваний. Например, `can_eat`, `Can-Eat` и `can eat` считаются
одним запрещённым термином. Это правило применяется к JSON Schema properties,
enum categories и CSV headers, но не к документации, описывающей запрет.

Проверка полного synthetic набора:

```powershell
.venv\Scripts\python.exe scripts\validate_taxonomy.py
```

Проверка будущего набора с явными путями:

```powershell
.venv\Scripts\python.exe scripts\validate_taxonomy.py `
  --taxonomy path\taxonomy.csv `
  --confusion-groups path\confusion-groups.csv `
  --review-record path\review-record.json
```

Валидатор работает только с локальными файлами и не обращается к сети.
Legacy-файл `data/knowledge_base.json` не является частью Taxonomy Matrix v1 и
этим каркасом не изменяется.
