# Taxonomy Matrix v1 — source and expert review policy

## Принцип

Каждое реальное таксономическое или региональное утверждение должно быть
трассируемо до источника и человека, выполнившего независимое review. Наличие
записи в справочнике не является пользовательским разрешением или гарантией
идентификации.

Синтетические fixtures маркируются `SYNTHETIC` и `UNREVIEWED`; они не могут
получать вымышленную подпись эксперта.

## Обязательная provenance-запись

Для каждой taxonomy row и confusion group ledger хранит:

- `schema_version` и `matrix_version`;
- постоянный `review_id`;
- `entity_type` и `entity_id`;
- `source_type`;
- `bibliographic_citation`;
- `source_locator` — URL, DOI, ISBN, catalogue ID или другой стабильный ID;
- `accessed_date`;
- `license_info`, когда применимо;
- `contributor_id`;
- `evidence_status`;
- `review_status`;
- `reviewer_id`;
- `reviewed_date`;
- `reviewer_notes`.

## Source types

Разрешены `PEER_REVIEWED_PUBLICATION`, `MONOGRAPH`, `TAXONOMIC_DATABASE`,
`REGIONAL_CHECKLIST`, `EXPERT_OBSERVATION`, а также служебные `NONE` и
`SYNTHETIC_FIXTURE`. Допустимость конкретного источника и лицензии должна быть
решена до заполнения реальных данных.

## Evidence statuses

- `NO_EVIDENCE` — источник ещё не приложен;
- `SOURCE_RECORDED` — источник записан, но не прошёл полную проверку;
- `EVIDENCE_VERIFIED` — evidence проверен reviewer;
- `SYNTHETIC` — запись существует только для теста структуры.

## Review statuses

Разрешены только:

- `UNREVIEWED`;
- `REVIEW_REQUIRED`;
- `APPROVED`;
- `REJECTED`.

`APPROVED` допустим только при наличии непустых source type, citation,
locator, access date, contributor, `EVIDENCE_VERIFIED`, reviewer ID, review
date и reviewer notes. Статус сущности и соответствующей ledger-записи должен
совпадать. Валидатор отклоняет фиктивно полную запись без этих полей.

`REJECTED` требует reviewer ID, корректную review date и непустое объяснение в
`reviewer_notes`. `UNREVIEWED` не может содержать reviewer ID или review date:
их наличие ошибочно создавало бы видимость выполненного экспертного review.

SAFETY: `APPROVED` означает только то, что конкретная внутренняя запись и её
evidence прошли экспертное review. Этот статус ничего не сообщает о допустимости
сбора, приготовления или употребления и не является пользовательским итогом.

## Процесс изменения

1. Contributor создаёт или меняет запись и прикладывает provenance.
2. Запись остаётся `UNREVIEWED` или `REVIEW_REQUIRED`.
3. Независимый квалифицированный reviewer проверяет taxonomy, региональные
   утверждения, confusion-связи и лицензии.
4. Reviewer фиксирует ID, дату и замечания; только после этого возможен
   `APPROVED`.
5. Отклонённая запись сохраняет audit trail как `REJECTED`, а не удаляется
   без объяснения.

## Нерешённые вопросы

- Кто имеет право выступать taxonomy/mycology reviewer и как хранится его ID.
- Какие конкретные источники считаются достаточными для каждого типа факта.
- Требуется ли цифровая подпись review record и какой trust store используется.
- Политика лицензий и цитирования для будущих внешних баз.
- Периодичность повторного review и политика отзыва устаревших утверждений.
