from __future__ import annotations

import argparse
import csv
import json
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
TAXONOMY_ROOT = ROOT / "data" / "taxonomy"
DEFAULT_DATA_ROOT = TAXONOMY_ROOT / "fixtures" / "valid-synthetic"
DEFAULT_SCHEMA_ROOT = TAXONOMY_ROOT / "schema"

FORBIDDEN_FIELD_OR_CATEGORY_NAMES = (
    "safe",
    "edible",
    "can_eat",
    "можно_есть",
    "съедобный",
    "безопасный",
)
SUPPORTED_SCHEMA_KEYWORDS = frozenset(
    {
        "$id",
        "$schema",
        "additionalProperties",
        "const",
        "enum",
        "format",
        "items",
        "minItems",
        "minLength",
        "pattern",
        "properties",
        "required",
        "title",
        "type",
        "uniqueItems",
    }
)
SUPPORTED_SCHEMA_TYPES = frozenset({"array", "boolean", "null", "object", "string"})
APPROVED_EVIDENCE_STATUS = "EVIDENCE_VERIFIED"
SYNTHETIC_EVIDENCE_STATUS = "SYNTHETIC"
SCHEMA_VERSION = "1.0.0"


@dataclass(frozen=True)
class ValidationPaths:
    taxonomy_csv: Path
    confusion_groups_csv: Path
    review_record_json: Path
    schema_dir: Path = DEFAULT_SCHEMA_ROOT


@dataclass(frozen=True)
class ValidationResult:
    errors: tuple[str, ...]
    taxon_count: int
    confusion_group_count: int
    review_record_count: int

    @property
    def ok(self) -> bool:
        return not self.errors


def default_paths() -> ValidationPaths:
    return ValidationPaths(
        taxonomy_csv=DEFAULT_DATA_ROOT / "taxonomy-matrix-v1.csv",
        confusion_groups_csv=DEFAULT_DATA_ROOT / "confusion-groups-v1.csv",
        review_record_json=DEFAULT_DATA_ROOT / "review-record-v1.json",
    )


def _normalise_name(value: str) -> str:
    return " ".join(value.split()).casefold()


def _normalise_safety_term(value: str) -> str:
    return re.sub(r"[\s_-]+", "", value).casefold()


FORBIDDEN_NORMALISED_TERMS = frozenset(
    _normalise_safety_term(value) for value in FORBIDDEN_FIELD_OR_CATEGORY_NAMES
)


def _is_forbidden_contract_term(value: str) -> bool:
    return _normalise_safety_term(value) in FORBIDDEN_NORMALISED_TERMS


def _load_json(path: Path, label: str, errors: list[str]) -> Any:
    if not path.is_file():
        errors.append(f"{label} file {path.name}: missing file: {path}")
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        errors.append(f"{label} file {path.name}: cannot read JSON: {exc}")
        return None


def _load_schema(path: Path, label: str, errors: list[str]) -> dict[str, Any]:
    value = _load_json(path, label, errors)
    if not isinstance(value, dict):
        if value is not None:
            errors.append(f"{label}: schema root must be an object")
        return {}
    return value


def _forbidden_schema_terms(value: Any, location: str) -> list[str]:
    errors: list[str] = []
    if not isinstance(value, dict):
        return errors

    properties = value.get("properties")
    if isinstance(properties, dict):
        for name, child in properties.items():
            if _is_forbidden_contract_term(name):
                errors.append(f"{location}: forbidden schema field: {name}")
            errors.extend(_forbidden_schema_terms(child, f"{location}.{name}"))

    enum_values = value.get("enum")
    if isinstance(enum_values, list):
        for item in enum_values:
            if isinstance(item, str) and _is_forbidden_contract_term(item):
                errors.append(f"{location}: forbidden schema category: {item}")

    items = value.get("items")
    if isinstance(items, dict):
        errors.extend(_forbidden_schema_terms(items, f"{location}[]"))
    return errors


def _validate_schema_contract(schema: dict[str, Any], label: str) -> list[str]:
    errors: list[str] = []

    def visit(rule: dict[str, Any], location: str) -> None:
        for keyword in sorted(set(rule) - SUPPORTED_SCHEMA_KEYWORDS):
            errors.append(f"{location}: unsupported schema keyword: {keyword}")

        declared_types = rule.get("type")
        if isinstance(declared_types, str):
            declared_types = [declared_types]
        if declared_types is not None:
            if not isinstance(declared_types, list) or not all(
                isinstance(item, str) and item in SUPPORTED_SCHEMA_TYPES
                for item in declared_types
            ):
                errors.append(f"{location}: unsupported or invalid schema type")

        value_format = rule.get("format")
        if value_format is not None and value_format != "date":
            errors.append(f"{location}: unsupported schema format: {value_format}")

        properties = rule.get("properties")
        if properties is not None:
            if not isinstance(properties, dict):
                errors.append(f"{location}: schema properties must be an object")
            else:
                for field, child in properties.items():
                    if not isinstance(child, dict):
                        errors.append(f"{location}.{field}: schema rule must be an object")
                    else:
                        visit(child, f"{location}.{field}")

        items = rule.get("items")
        if items is not None:
            if not isinstance(items, dict):
                errors.append(f"{location}: schema items must be an object")
            else:
                visit(items, f"{location}[]")

    visit(schema, label)
    properties = schema.get("properties")
    required = schema.get("required")
    if schema.get("type") != "object":
        errors.append(f"{label}: root type must be object")
    if schema.get("additionalProperties") is not False:
        errors.append(f"{label}: additionalProperties must be false")
    if isinstance(properties, dict) and isinstance(required, list):
        if set(required) != set(properties):
            errors.append(f"{label}: required fields must exactly match properties")
    else:
        errors.append(f"{label}: properties and required must be present")
    return errors


def _validate_scalar(
    value: Any,
    rule: dict[str, Any],
    location: str,
    errors: list[str],
) -> None:
    allowed_types = rule.get("type")
    if isinstance(allowed_types, str):
        allowed_types = [allowed_types]
    if not isinstance(allowed_types, list):
        allowed_types = []

    type_matches = {
        "string": isinstance(value, str),
        "boolean": isinstance(value, bool),
        "array": isinstance(value, list),
        "object": isinstance(value, dict),
        "null": value is None,
    }
    if allowed_types and not any(type_matches.get(item, False) for item in allowed_types):
        errors.append(f"{location}: expected type {' or '.join(allowed_types)}")
        return
    if value is None:
        return

    if "const" in rule and value != rule["const"]:
        errors.append(f"{location}: expected constant {rule['const']!r}, got {value!r}")
    if "enum" in rule and value not in rule["enum"]:
        options = ", ".join(str(item) for item in rule["enum"])
        errors.append(f"{location}: invalid value {value!r}; expected one of: {options}")

    if isinstance(value, str):
        if len(value) < int(rule.get("minLength", 0)):
            errors.append(f"{location}: must not be empty")
        pattern = rule.get("pattern")
        if pattern and re.fullmatch(pattern, value) is None:
            errors.append(f"{location}: value {value!r} does not match {pattern!r}")
        if rule.get("format") == "date":
            try:
                date.fromisoformat(value)
            except ValueError:
                errors.append(f"{location}: invalid ISO calendar date: {value!r}")

    if isinstance(value, list):
        minimum = int(rule.get("minItems", 0))
        if len(value) < minimum:
            errors.append(f"{location}: requires at least {minimum} item(s)")
        if rule.get("uniqueItems") and len(value) != len(set(value)):
            errors.append(f"{location}: duplicate list item")
        item_rule = rule.get("items")
        if isinstance(item_rule, dict):
            for index, item in enumerate(value):
                _validate_scalar(item, item_rule, f"{location}[{index}]", errors)


def _validate_record(
    record: dict[str, Any],
    schema: dict[str, Any],
    location: str,
    errors: list[str],
) -> None:
    properties = schema.get("properties", {})
    required = schema.get("required", [])
    if not isinstance(properties, dict) or not isinstance(required, list):
        errors.append(f"{location}: invalid schema contract")
        return

    for field in required:
        if field not in record:
            errors.append(f"{location}: missing required field: {field}")
    for field in record:
        if field not in properties:
            errors.append(f"{location}: unknown field: {field}")
    for field, rule in properties.items():
        if field in record and isinstance(rule, dict):
            _validate_scalar(record[field], rule, f"{location}.{field}", errors)


def _parse_csv_value(
    raw_value: str | None,
    rule: dict[str, Any],
    location: str,
    errors: list[str],
) -> Any:
    value = "" if raw_value is None else raw_value.strip()
    allowed_types = rule.get("type")
    if isinstance(allowed_types, str):
        allowed_types = [allowed_types]
    if not isinstance(allowed_types, list):
        allowed_types = []

    if not value and "null" in allowed_types:
        return None
    if "boolean" in allowed_types:
        if value == "true":
            return True
        if value == "false":
            return False
        errors.append(f"{location}: boolean must be lowercase true or false")
        return value
    if "array" in allowed_types:
        return [] if not value else [item.strip() for item in value.split("|")]
    return value


def _load_csv_records(
    path: Path,
    schema: dict[str, Any],
    label: str,
    errors: list[str],
) -> list[dict[str, Any]]:
    file_label = f"{label} file {path.name}"
    if not path.is_file():
        errors.append(f"{file_label}: missing file: {path}")
        return []
    properties = schema.get("properties", {})
    if not isinstance(properties, dict):
        errors.append(f"{file_label}: schema properties must be an object")
        return []

    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.reader(handle, strict=True)
            try:
                headers = next(reader)
            except StopIteration:
                errors.append(f"{file_label}: CSV header is missing")
                return []
            if not headers:
                errors.append(f"{file_label}: CSV header is empty")
                return []

            duplicate_headers = sorted(
                {header for header in headers if headers.count(header) > 1}
            )
            for header in duplicate_headers:
                errors.append(f"{file_label}: duplicate column: {header}")
            for header in headers:
                if _is_forbidden_contract_term(header):
                    errors.append(f"{file_label}: forbidden column: {header}")
            for header in sorted(set(headers) - set(properties)):
                errors.append(f"{file_label}: unknown column: {header}")
            for field in sorted(set(properties) - set(headers)):
                errors.append(f"{file_label}: missing required column: {field}")

            records: list[dict[str, Any]] = []
            for row_number, values in enumerate(reader, start=2):
                if not values:
                    errors.append(f"{file_label} row {row_number}: blank CSV row")
                    continue
                if len(values) > len(headers):
                    errors.append(f"{file_label} row {row_number}: too many CSV values")
                raw = dict(zip(headers, values, strict=False))
                record: dict[str, Any] = {}
                for field, rule in properties.items():
                    if field in raw and isinstance(rule, dict):
                        record[field] = _parse_csv_value(
                            raw[field],
                            rule,
                            f"{file_label} row {row_number}.{field}",
                            errors,
                        )
                id_hint = record.get("taxon_id", record.get("group_id", "unknown"))
                row_label = f"{file_label} row {row_number} (object={id_hint!r})"
                _validate_record(record, schema, row_label, errors)
                records.append(record)
            return records
    except (OSError, UnicodeError, csv.Error) as exc:
        errors.append(f"{file_label}: cannot read CSV: {exc}")
        return []


def _duplicates(values: list[str]) -> set[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for value in values:
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    return duplicates


def _validate_taxa(taxa: list[dict[str, Any]], errors: list[str]) -> dict[str, dict[str, Any]]:
    ids = [item["taxon_id"] for item in taxa if isinstance(item.get("taxon_id"), str)]
    for taxon_id in sorted(_duplicates(ids)):
        errors.append(f"taxonomy: duplicate taxon_id: {taxon_id}")
    taxa_by_id = {
        item["taxon_id"]: item for item in taxa if isinstance(item.get("taxon_id"), str)
    }

    accepted_owners: dict[str, str] = {}
    synonym_owners: dict[str, str] = {}
    for item in taxa:
        taxon_id = item.get("taxon_id")
        accepted_name = item.get("accepted_name")
        if not isinstance(taxon_id, str) or not isinstance(accepted_name, str):
            continue
        normalised = _normalise_name(accepted_name)
        owner = accepted_owners.get(normalised)
        if owner and owner != taxon_id:
            errors.append(
                f"taxonomy: duplicate accepted_name {accepted_name!r}: {owner}, {taxon_id}"
            )
        else:
            accepted_owners[normalised] = taxon_id

        synonyms = item.get("synonyms", [])
        if isinstance(synonyms, list):
            local_synonyms: set[str] = set()
            for synonym in synonyms:
                if not isinstance(synonym, str):
                    continue
                synonym_key = _normalise_name(synonym)
                if synonym_key in local_synonyms:
                    errors.append(
                        f"taxonomy {taxon_id}: duplicate normalised synonym: {synonym!r}"
                    )
                local_synonyms.add(synonym_key)
                synonym_owner = synonym_owners.get(synonym_key)
                if synonym_owner and synonym_owner != taxon_id:
                    errors.append(
                        f"taxonomy: conflicting synonym {synonym!r}: "
                        f"{synonym_owner}, {taxon_id}"
                    )
                else:
                    synonym_owners[synonym_key] = taxon_id

    for name, synonym_owner in sorted(synonym_owners.items()):
        accepted_owner = accepted_owners.get(name)
        if accepted_owner and accepted_owner != synonym_owner:
            errors.append(
                f"taxonomy: synonym conflicts with accepted_name: "
                f"{synonym_owner}, {accepted_owner}"
            )

    parents: dict[str, str] = {}
    for taxon_id, item in sorted(taxa_by_id.items()):
        parent = item.get("parent_taxon_id")
        if not isinstance(parent, str):
            continue
        if parent == taxon_id:
            errors.append(f"taxonomy {taxon_id}: self parent is forbidden")
            continue
        if parent not in taxa_by_id:
            errors.append(f"taxonomy: unknown parent_taxon_id {parent!r} for {taxon_id}")
        else:
            parents[taxon_id] = parent

    state: dict[str, int] = {}
    stack: list[str] = []
    reported_cycles: set[tuple[str, ...]] = set()

    def visit(taxon_id: str) -> None:
        current_state = state.get(taxon_id, 0)
        if current_state == 2:
            return
        if current_state == 1:
            start = stack.index(taxon_id)
            cycle = tuple(stack[start:] + [taxon_id])
            canonical = tuple(sorted(set(cycle)))
            if canonical not in reported_cycles:
                reported_cycles.add(canonical)
                errors.append(f"taxonomy: parent cycle detected: {' -> '.join(cycle)}")
            return
        state[taxon_id] = 1
        stack.append(taxon_id)
        parent = parents.get(taxon_id)
        if parent is not None:
            visit(parent)
        stack.pop()
        state[taxon_id] = 2

    for taxon_id in sorted(taxa_by_id):
        visit(taxon_id)
    return taxa_by_id


def _validate_confusion_groups(
    groups: list[dict[str, Any]],
    taxa_by_id: dict[str, dict[str, Any]],
    errors: list[str],
) -> dict[str, dict[str, Any]]:
    ids = [item["group_id"] for item in groups if isinstance(item.get("group_id"), str)]
    for group_id in sorted(_duplicates(ids)):
        errors.append(f"confusion groups: duplicate group_id: {group_id}")
    groups_by_id = {
        item["group_id"]: item for item in groups if isinstance(item.get("group_id"), str)
    }

    for group_id, group in sorted(groups_by_id.items()):
        members = set(group.get("member_taxon_ids", []))
        dangerous_members = set(group.get("dangerous_member_taxon_ids", []))
        for taxon_id in sorted(members | dangerous_members):
            if taxon_id not in taxa_by_id:
                errors.append(
                    f"confusion group {group_id}: unknown member taxon_id: {taxon_id}"
                )
        for taxon_id in sorted(dangerous_members - members):
            errors.append(
                f"confusion group {group_id}: dangerous member is not a member: {taxon_id}"
            )
        for taxon_id in sorted(members & set(taxa_by_id)):
            taxon_groups = set(taxa_by_id[taxon_id].get("confusion_group_ids", []))
            if group_id not in taxon_groups:
                errors.append(
                    f"confusion group {group_id}: missing reverse reference from {taxon_id}"
                )

    for taxon_id, taxon in sorted(taxa_by_id.items()):
        for group_id in taxon.get("confusion_group_ids", []):
            if group_id not in groups_by_id:
                errors.append(
                    f"taxonomy {taxon_id}: unknown confusion_group_id: {group_id}"
                )
            elif taxon_id not in set(groups_by_id[group_id].get("member_taxon_ids", [])):
                errors.append(
                    f"taxonomy {taxon_id}: group {group_id} lacks matching member reference"
                )
    return groups_by_id


def _validate_review_container(
    value: Any,
    review_schema: dict[str, Any],
    label: str,
    errors: list[str],
) -> tuple[str | None, list[dict[str, Any]]]:
    if not isinstance(value, dict):
        if value is not None:
            errors.append(f"{label}: root must be an object")
        return None, []

    expected = {"schema_version", "matrix_version", "records"}
    for field in sorted(set(value) - expected):
        errors.append(f"{label}: unknown field: {field}")
    for field in sorted(expected - set(value)):
        errors.append(f"{label}: missing required field: {field}")
    if value.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"{label}.schema_version: expected {SCHEMA_VERSION!r}")
    matrix_version = value.get("matrix_version")
    valid_matrix_version = isinstance(matrix_version, str) and re.fullmatch(
        r"[0-9]+\.[0-9]+\.[0-9]+", matrix_version
    )
    if not valid_matrix_version:
        errors.append(f"{label}.matrix_version: expected semantic version")
        matrix_version = None
    records = value.get("records")
    if not isinstance(records, list):
        errors.append(f"{label}.records: expected array")
        return matrix_version, []

    typed_records: list[dict[str, Any]] = []
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            errors.append(f"{label} record {index}: expected object")
            continue
        review_id = record.get("review_id", "unknown")
        record_label = f"{label} record {index} (object={review_id!r})"
        _validate_record(record, review_schema, record_label, errors)
        typed_records.append(record)
    return matrix_version, typed_records


def _validate_reviews(
    matrix_version: str | None,
    reviews: list[dict[str, Any]],
    taxa_by_id: dict[str, dict[str, Any]],
    groups_by_id: dict[str, dict[str, Any]],
    errors: list[str],
) -> None:
    review_ids = [
        item["review_id"] for item in reviews if isinstance(item.get("review_id"), str)
    ]
    for review_id in sorted(_duplicates(review_ids)):
        errors.append(f"review ledger: duplicate review_id: {review_id}")

    records_by_entity: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for record in reviews:
        entity_type = record.get("entity_type")
        entity_id = record.get("entity_id")
        if not isinstance(entity_type, str) or not isinstance(entity_id, str):
            continue
        if matrix_version is not None and record.get("matrix_version") != matrix_version:
            errors.append(
                f"review {record.get('review_id')}: matrix_version does not match ledger"
            )
        target = taxa_by_id if entity_type == "TAXON" else groups_by_id
        if entity_type in {"TAXON", "CONFUSION_GROUP"} and entity_id not in target:
            errors.append(
                f"review {record.get('review_id')}: unknown {entity_type} entity_id: {entity_id}"
            )
        records_by_entity.setdefault((entity_type, entity_id), []).append(record)

        review_status = record.get("review_status")
        evidence_status = record.get("evidence_status")
        if evidence_status == SYNTHETIC_EVIDENCE_STATUS and review_status != "UNREVIEWED":
            errors.append(
                f"review {record.get('review_id')}: synthetic record must remain UNREVIEWED"
            )
        if review_status == "UNREVIEWED":
            for field in ("reviewer_id", "reviewed_date"):
                if record.get(field):
                    errors.append(
                        f"review {record.get('review_id')}: "
                        f"UNREVIEWED must not assert {field}"
                    )
        if review_status == "APPROVED":
            if evidence_status != APPROVED_EVIDENCE_STATUS:
                errors.append(
                    f"review {record.get('review_id')}: APPROVED requires verified evidence"
                )
            if record.get("source_type") in {None, "", "NONE", "SYNTHETIC_FIXTURE"}:
                errors.append(
                    f"review {record.get('review_id')}: APPROVED requires a real source_type"
                )
            for field in (
                "bibliographic_citation",
                "source_locator",
                "accessed_date",
                "license_info",
                "contributor_id",
                "reviewer_id",
                "reviewed_date",
                "reviewer_notes",
            ):
                if not record.get(field):
                    errors.append(
                        f"review {record.get('review_id')}: APPROVED requires {field}"
                    )
        if review_status == "REJECTED":
            for field in ("reviewer_id", "reviewed_date", "reviewer_notes"):
                if not record.get(field):
                    errors.append(
                        f"review {record.get('review_id')}: REJECTED requires {field}"
                    )

    entities = [
        *(('TAXON', entity_id, entity) for entity_id, entity in taxa_by_id.items()),
        *(("CONFUSION_GROUP", entity_id, entity) for entity_id, entity in groups_by_id.items()),
    ]
    for entity_type, entity_id, entity in sorted(entities):
        records = records_by_entity.get((entity_type, entity_id), [])
        if not records:
            errors.append(f"review ledger: missing record for {entity_type} {entity_id}")
        entity_status = entity.get("review_status")
        evidence_status = entity.get("evidence_status")
        if evidence_status == SYNTHETIC_EVIDENCE_STATUS and entity_status != "UNREVIEWED":
            errors.append(f"{entity_type} {entity_id}: synthetic entity must remain UNREVIEWED")
        if entity_status == "APPROVED":
            if evidence_status != APPROVED_EVIDENCE_STATUS:
                errors.append(
                    f"{entity_type} {entity_id}: APPROVED requires verified evidence"
                )
            if not any(record.get("review_status") == "APPROVED" for record in records):
                errors.append(
                    f"{entity_type} {entity_id}: APPROVED requires an APPROVED review record"
                )
        if records and not any(record.get("review_status") == entity_status for record in records):
            errors.append(
                f"{entity_type} {entity_id}: review_status has no matching review record"
            )


def validate(paths: ValidationPaths) -> ValidationResult:
    errors: list[str] = []
    taxonomy_schema = _load_schema(
        paths.schema_dir / "taxonomy-row.schema.json", "taxonomy schema", errors
    )
    confusion_schema = _load_schema(
        paths.schema_dir / "confusion-group.schema.json", "confusion schema", errors
    )
    review_schema = _load_schema(
        paths.schema_dir / "review-record.schema.json", "review schema", errors
    )
    for label, schema in (
        ("taxonomy schema", taxonomy_schema),
        ("confusion schema", confusion_schema),
        ("review schema", review_schema),
    ):
        errors.extend(_validate_schema_contract(schema, label))
        errors.extend(_forbidden_schema_terms(schema, label))

    taxa = _load_csv_records(paths.taxonomy_csv, taxonomy_schema, "taxonomy", errors)
    groups = _load_csv_records(
        paths.confusion_groups_csv, confusion_schema, "confusion groups", errors
    )
    review_label = f"review ledger file {paths.review_record_json.name}"
    review_value = _load_json(paths.review_record_json, "review ledger", errors)
    matrix_version, reviews = _validate_review_container(
        review_value, review_schema, review_label, errors
    )

    taxa_by_id = _validate_taxa(taxa, errors)
    groups_by_id = _validate_confusion_groups(groups, taxa_by_id, errors)
    _validate_reviews(matrix_version, reviews, taxa_by_id, groups_by_id, errors)

    return ValidationResult(
        errors=tuple(sorted(set(errors))),
        taxon_count=len(taxa),
        confusion_group_count=len(groups),
        review_record_count=len(reviews),
    )


def _parse_args() -> argparse.Namespace:
    defaults = default_paths()
    parser = argparse.ArgumentParser(
        description="Validate Taxonomy Matrix v1 files without network access."
    )
    parser.add_argument("--taxonomy", type=Path, default=defaults.taxonomy_csv)
    parser.add_argument(
        "--confusion-groups",
        type=Path,
        default=defaults.confusion_groups_csv,
    )
    parser.add_argument(
        "--review-record",
        type=Path,
        default=defaults.review_record_json,
    )
    parser.add_argument("--schema-dir", type=Path, default=DEFAULT_SCHEMA_ROOT)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    result = validate(
        ValidationPaths(
            taxonomy_csv=args.taxonomy.resolve(),
            confusion_groups_csv=args.confusion_groups.resolve(),
            review_record_json=args.review_record.resolve(),
            schema_dir=args.schema_dir.resolve(),
        )
    )
    if result.errors:
        print(f"Taxonomy validation failed with {len(result.errors)} error(s):")
        for error in result.errors:
            print(f"- {error}")
        return 1
    print(
        "Taxonomy validation passed: "
        f"{result.taxon_count} taxa, "
        f"{result.confusion_group_count} confusion group(s), "
        f"{result.review_record_count} review record(s)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
