from __future__ import annotations

import csv
import json
import shutil
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

import pytest

from scripts.validate_taxonomy import ValidationPaths, main, validate

ROOT = Path(__file__).resolve().parent.parent
SCHEMA_DIR = ROOT / "data" / "taxonomy" / "schema"
VALID_FIXTURE = ROOT / "data" / "taxonomy" / "fixtures" / "valid-synthetic"
INVALID_FIXTURE = (
    ROOT
    / "data"
    / "taxonomy"
    / "fixtures"
    / "invalid-synthetic"
    / "forbidden-column-edible"
)
TEMPLATES = ROOT / "data" / "taxonomy" / "templates"
VALIDATOR = ROOT / "scripts" / "validate_taxonomy.py"


def _paths(data_dir: Path) -> ValidationPaths:
    return ValidationPaths(
        taxonomy_csv=data_dir / "taxonomy-matrix-v1.csv",
        confusion_groups_csv=data_dir / "confusion-groups-v1.csv",
        review_record_json=data_dir / "review-record-v1.json",
        schema_dir=SCHEMA_DIR,
    )


def _copy_valid_fixture(tmp_path: Path) -> ValidationPaths:
    data_dir = tmp_path / "dataset"
    shutil.copytree(VALID_FIXTURE, data_dir)
    return _paths(data_dir)


def _mutate_csv(
    path: Path,
    mutation: Callable[[list[dict[str, str]], list[str]], None],
) -> None:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)
    mutation(rows, fieldnames)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _mutate_reviews(path: Path, mutation: Callable[[dict[str, object]], None]) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    mutation(data)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _errors(paths: ValidationPaths) -> tuple[str, ...]:
    return validate(paths).errors


def _set_taxon_field(rows: list[dict[str, str]], taxon_id: str, field: str, value: str) -> None:
    row = next(item for item in rows if item["taxon_id"] == taxon_id)
    row[field] = value


def _approve_borealis(paths: ValidationPaths) -> None:
    def approve_taxon(rows: list[dict[str, str]], _: list[str]) -> None:
        _set_taxon_field(rows, "tx_testus_borealis", "evidence_status", "EVIDENCE_VERIFIED")
        _set_taxon_field(rows, "tx_testus_borealis", "review_status", "APPROVED")

    def approve_review(data: dict[str, object]) -> None:
        records = data["records"]
        assert isinstance(records, list)
        record = next(
            item
            for item in records
            if isinstance(item, dict) and item.get("entity_id") == "tx_testus_borealis"
        )
        record.update(
            {
                "source_type": "MONOGRAPH",
                "bibliographic_citation": "Synthetic approval test citation",
                "source_locator": "synthetic-test://approval-source",
                "accessed_date": "2026-07-31",
                "license_info": "TEST_ONLY",
                "evidence_status": "EVIDENCE_VERIFIED",
                "review_status": "APPROVED",
                "reviewer_id": "synthetic_reviewer_id",
                "reviewed_date": "2026-07-31",
                "reviewer_notes": "Synthetic completeness test; not an expert signature.",
            }
        )

    _mutate_csv(paths.taxonomy_csv, approve_taxon)
    _mutate_reviews(paths.review_record_json, approve_review)


def _review_record(data: dict[str, object], entity_id: str) -> dict[str, object]:
    records = data["records"]
    assert isinstance(records, list)
    return next(
        item
        for item in records
        if isinstance(item, dict) and item.get("entity_id") == entity_id
    )


def test_valid_synthetic_dataset_passes() -> None:
    result = validate(_paths(VALID_FIXTURE))

    assert result.errors == ()
    assert result.taxon_count == 3
    assert result.confusion_group_count == 1
    assert result.review_record_count == 4


def test_empty_templates_are_valid_scaffold() -> None:
    result = validate(_paths(TEMPLATES))

    assert result.errors == ()
    assert result.taxon_count == 0
    assert result.confusion_group_count == 0
    assert result.review_record_count == 0


@pytest.mark.parametrize(
    ("path", "expected_data_rows"),
    [
        (TEMPLATES / "taxonomy-matrix-v1.csv", 0),
        (TEMPLATES / "confusion-groups-v1.csv", 0),
        (VALID_FIXTURE / "taxonomy-matrix-v1.csv", 3),
        (VALID_FIXTURE / "confusion-groups-v1.csv", 1),
        (INVALID_FIXTURE / "taxonomy-matrix-v1.csv", 1),
        (INVALID_FIXTURE / "confusion-groups-v1.csv", 0),
    ],
)
def test_shipped_csv_has_exact_physical_row_count(
    path: Path,
    expected_data_rows: int,
) -> None:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.reader(handle, strict=True))

    assert len(rows) == expected_data_rows + 1
    assert all(row for row in rows)


def test_blank_csv_row_is_rejected(tmp_path: Path) -> None:
    paths = _copy_valid_fixture(tmp_path)
    text = paths.taxonomy_csv.read_text(encoding="utf-8")
    paths.taxonomy_csv.write_text(text + "\n", encoding="utf-8")

    assert any("blank CSV row" in error for error in _errors(paths))


def test_duplicate_taxon_id_is_rejected(tmp_path: Path) -> None:
    paths = _copy_valid_fixture(tmp_path)

    def duplicate_id(rows: list[dict[str, str]], _: list[str]) -> None:
        _set_taxon_field(rows, "tx_testus_obscurus", "taxon_id", "tx_testus_borealis")

    _mutate_csv(paths.taxonomy_csv, duplicate_id)

    assert any("duplicate taxon_id" in error for error in _errors(paths))


def test_unknown_parent_taxon_id_is_rejected(tmp_path: Path) -> None:
    paths = _copy_valid_fixture(tmp_path)

    def unknown_parent(rows: list[dict[str, str]], _: list[str]) -> None:
        _set_taxon_field(rows, "tx_testus_borealis", "parent_taxon_id", "tx_unknown")

    _mutate_csv(paths.taxonomy_csv, unknown_parent)

    assert any("unknown parent_taxon_id" in error for error in _errors(paths))


def test_parent_cycle_is_rejected(tmp_path: Path) -> None:
    paths = _copy_valid_fixture(tmp_path)

    def create_cycle(rows: list[dict[str, str]], _: list[str]) -> None:
        _set_taxon_field(rows, "tx_testus", "parent_taxon_id", "tx_testus_borealis")

    _mutate_csv(paths.taxonomy_csv, create_cycle)

    assert any("parent cycle detected" in error for error in _errors(paths))


def test_self_parent_is_rejected(tmp_path: Path) -> None:
    paths = _copy_valid_fixture(tmp_path)

    def self_parent(rows: list[dict[str, str]], _: list[str]) -> None:
        _set_taxon_field(
            rows,
            "tx_testus_borealis",
            "parent_taxon_id",
            "tx_testus_borealis",
        )

    _mutate_csv(paths.taxonomy_csv, self_parent)

    assert any("self parent is forbidden" in error for error in _errors(paths))


def test_unknown_confusion_group_is_rejected(tmp_path: Path) -> None:
    paths = _copy_valid_fixture(tmp_path)

    def unknown_group(rows: list[dict[str, str]], _: list[str]) -> None:
        _set_taxon_field(
            rows,
            "tx_testus_borealis",
            "confusion_group_ids",
            "cg_unknown_group",
        )

    _mutate_csv(paths.taxonomy_csv, unknown_group)

    assert any("unknown confusion_group_id" in error for error in _errors(paths))


def test_confusion_group_with_unknown_taxon_is_rejected(tmp_path: Path) -> None:
    paths = _copy_valid_fixture(tmp_path)

    def unknown_member(rows: list[dict[str, str]], _: list[str]) -> None:
        rows[0]["member_taxon_ids"] = "tx_testus_borealis|tx_unknown"

    _mutate_csv(paths.confusion_groups_csv, unknown_member)

    assert any("unknown member taxon_id" in error for error in _errors(paths))


def test_conflicting_synonym_is_rejected(tmp_path: Path) -> None:
    paths = _copy_valid_fixture(tmp_path)

    def conflict(rows: list[dict[str, str]], _: list[str]) -> None:
        _set_taxon_field(
            rows,
            "tx_testus_obscurus",
            "synonyms",
            "Testus borealis exemplaris",
        )

    _mutate_csv(paths.taxonomy_csv, conflict)

    assert any("conflicting synonym" in error for error in _errors(paths))


def test_duplicate_normalised_synonym_in_one_taxon_is_rejected(tmp_path: Path) -> None:
    paths = _copy_valid_fixture(tmp_path)

    def duplicate_synonym(rows: list[dict[str, str]], _: list[str]) -> None:
        _set_taxon_field(
            rows,
            "tx_testus_borealis",
            "synonyms",
            "Testus borealis exemplaris|  TESTUS   BOREALIS EXEMPLARIS  ",
        )

    _mutate_csv(paths.taxonomy_csv, duplicate_synonym)

    assert any("duplicate normalised synonym" in error for error in _errors(paths))


def test_normalised_accepted_name_duplicate_is_rejected(tmp_path: Path) -> None:
    paths = _copy_valid_fixture(tmp_path)

    def duplicate_name(rows: list[dict[str, str]], _: list[str]) -> None:
        _set_taxon_field(
            rows,
            "tx_testus_obscurus",
            "accepted_name",
            "  TESTUS   BOREALIS  ",
        )

    _mutate_csv(paths.taxonomy_csv, duplicate_name)

    assert any("duplicate accepted_name" in error for error in _errors(paths))


def test_synonym_collision_with_other_accepted_name_is_rejected(tmp_path: Path) -> None:
    paths = _copy_valid_fixture(tmp_path)

    def accepted_collision(rows: list[dict[str, str]], _: list[str]) -> None:
        _set_taxon_field(rows, "tx_testus_obscurus", "synonyms", " testus   borealis ")

    _mutate_csv(paths.taxonomy_csv, accepted_collision)

    assert any(
        "synonym conflicts with accepted_name" in error for error in _errors(paths)
    )


def test_approved_without_reviewer_is_rejected(tmp_path: Path) -> None:
    paths = _copy_valid_fixture(tmp_path)
    _approve_borealis(paths)

    def remove_reviewer(data: dict[str, object]) -> None:
        records = data["records"]
        assert isinstance(records, list)
        record = next(
            item
            for item in records
            if isinstance(item, dict) and item.get("entity_id") == "tx_testus_borealis"
        )
        record["reviewer_id"] = None

    _mutate_reviews(paths.review_record_json, remove_reviewer)

    assert any("APPROVED requires reviewer_id" in error for error in _errors(paths))


def test_approved_without_evidence_is_rejected(tmp_path: Path) -> None:
    paths = _copy_valid_fixture(tmp_path)
    _approve_borealis(paths)

    def remove_evidence(data: dict[str, object]) -> None:
        records = data["records"]
        assert isinstance(records, list)
        record = next(
            item
            for item in records
            if isinstance(item, dict) and item.get("entity_id") == "tx_testus_borealis"
        )
        record["evidence_status"] = "NO_EVIDENCE"

    _mutate_reviews(paths.review_record_json, remove_evidence)

    assert any("APPROVED requires verified evidence" in error for error in _errors(paths))


def test_rejected_without_reviewer_and_explanation_is_rejected(tmp_path: Path) -> None:
    paths = _copy_valid_fixture(tmp_path)

    def reject_taxon(rows: list[dict[str, str]], _: list[str]) -> None:
        _set_taxon_field(rows, "tx_testus_borealis", "evidence_status", "SOURCE_RECORDED")
        _set_taxon_field(rows, "tx_testus_borealis", "review_status", "REJECTED")

    def reject_review(data: dict[str, object]) -> None:
        record = _review_record(data, "tx_testus_borealis")
        record["evidence_status"] = "SOURCE_RECORDED"
        record["review_status"] = "REJECTED"
        record["reviewer_id"] = None
        record["reviewed_date"] = None
        record["reviewer_notes"] = None

    _mutate_csv(paths.taxonomy_csv, reject_taxon)
    _mutate_reviews(paths.review_record_json, reject_review)

    errors = _errors(paths)
    assert any("REJECTED requires reviewer_id" in error for error in errors)
    assert any("REJECTED requires reviewer_notes" in error for error in errors)


def test_unreviewed_must_not_assert_reviewer_or_date(tmp_path: Path) -> None:
    paths = _copy_valid_fixture(tmp_path)

    def assert_fake_review(data: dict[str, object]) -> None:
        record = _review_record(data, "tx_testus_borealis")
        record["reviewer_id"] = "synthetic_not_a_real_reviewer"
        record["reviewed_date"] = "2026-07-31"

    _mutate_reviews(paths.review_record_json, assert_fake_review)

    errors = _errors(paths)
    assert any("UNREVIEWED must not assert reviewer_id" in error for error in errors)
    assert any("UNREVIEWED must not assert reviewed_date" in error for error in errors)


def test_invalid_calendar_date_is_rejected(tmp_path: Path) -> None:
    paths = _copy_valid_fixture(tmp_path)
    _approve_borealis(paths)

    def invalid_date(data: dict[str, object]) -> None:
        record = _review_record(data, "tx_testus_borealis")
        record["reviewed_date"] = "2026-02-30"

    _mutate_reviews(paths.review_record_json, invalid_date)

    assert any("invalid ISO calendar date" in error for error in _errors(paths))


def test_unknown_review_target_is_rejected(tmp_path: Path) -> None:
    paths = _copy_valid_fixture(tmp_path)

    def unknown_target(data: dict[str, object]) -> None:
        record = _review_record(data, "tx_testus_borealis")
        record["entity_id"] = "tx_unknown"

    _mutate_reviews(paths.review_record_json, unknown_target)

    assert any("unknown TAXON entity_id: tx_unknown" in error for error in _errors(paths))


def test_unknown_review_entity_type_is_rejected(tmp_path: Path) -> None:
    paths = _copy_valid_fixture(tmp_path)

    def invalid_target_type(data: dict[str, object]) -> None:
        record = _review_record(data, "tx_testus_borealis")
        record["entity_type"] = "SPECIMEN"

    _mutate_reviews(paths.review_record_json, invalid_target_type)

    assert any("entity_type: invalid value 'SPECIMEN'" in error for error in _errors(paths))


def test_duplicate_review_id_is_rejected(tmp_path: Path) -> None:
    paths = _copy_valid_fixture(tmp_path)

    def duplicate_review(data: dict[str, object]) -> None:
        first = _review_record(data, "tx_testus")
        second = _review_record(data, "tx_testus_borealis")
        second["review_id"] = first["review_id"]

    _mutate_reviews(paths.review_record_json, duplicate_review)

    assert any("duplicate review_id" in error for error in _errors(paths))


def _assert_forbidden_column_rejected(tmp_path: Path, column: str) -> None:
    paths = _copy_valid_fixture(tmp_path)

    def add_column(rows: list[dict[str, str]], fieldnames: list[str]) -> None:
        fieldnames.append(column)
        for row in rows:
            row[column] = "false"

    _mutate_csv(paths.taxonomy_csv, add_column)

    errors = _errors(paths)
    assert any(f"forbidden column: {column}" in error for error in errors)


def test_forbidden_edible_column_is_rejected(tmp_path: Path) -> None:
    _assert_forbidden_column_rejected(tmp_path, "edible")


def test_forbidden_safe_column_is_rejected(tmp_path: Path) -> None:
    _assert_forbidden_column_rejected(tmp_path, "safe")


@pytest.mark.parametrize(
    "column",
    ["SAFE", "C A N  E A T", "can-eat", "можно есть", "СЪЕДОБНЫЙ", "Безопасный"],
)
def test_forbidden_column_normalisation_is_separator_and_case_insensitive(
    tmp_path: Path,
    column: str,
) -> None:
    _assert_forbidden_column_rejected(tmp_path, column)


def test_forbidden_schema_field_is_rejected(tmp_path: Path) -> None:
    paths = _copy_valid_fixture(tmp_path)
    schema_dir = tmp_path / "schema"
    shutil.copytree(SCHEMA_DIR, schema_dir)
    schema_path = schema_dir / "taxonomy-row.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    schema["properties"]["safe"] = {"type": "boolean"}
    schema_path.write_text(json.dumps(schema, indent=2) + "\n", encoding="utf-8")
    paths = ValidationPaths(
        taxonomy_csv=paths.taxonomy_csv,
        confusion_groups_csv=paths.confusion_groups_csv,
        review_record_json=paths.review_record_json,
        schema_dir=schema_dir,
    )

    assert any("forbidden schema field: safe" in error for error in _errors(paths))


def test_forbidden_schema_category_is_normalised(tmp_path: Path) -> None:
    paths = _copy_valid_fixture(tmp_path)
    schema_dir = tmp_path / "schema"
    shutil.copytree(SCHEMA_DIR, schema_dir)
    schema_path = schema_dir / "taxonomy-row.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    schema["properties"]["rank"]["enum"].append("Can Eat")
    schema_path.write_text(json.dumps(schema, indent=2) + "\n", encoding="utf-8")
    paths = ValidationPaths(
        taxonomy_csv=paths.taxonomy_csv,
        confusion_groups_csv=paths.confusion_groups_csv,
        review_record_json=paths.review_record_json,
        schema_dir=schema_dir,
    )

    assert any("forbidden schema category: Can Eat" in error for error in _errors(paths))


def test_schema_with_unsupported_keyword_fails_closed(tmp_path: Path) -> None:
    paths = _copy_valid_fixture(tmp_path)
    schema_dir = tmp_path / "schema"
    shutil.copytree(SCHEMA_DIR, schema_dir)
    schema_path = schema_dir / "taxonomy-row.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    schema["properties"]["accepted_name"]["maxLength"] = 80
    schema_path.write_text(json.dumps(schema, indent=2) + "\n", encoding="utf-8")
    paths = ValidationPaths(
        taxonomy_csv=paths.taxonomy_csv,
        confusion_groups_csv=paths.confusion_groups_csv,
        review_record_json=paths.review_record_json,
        schema_dir=schema_dir,
    )

    assert any("unsupported schema keyword: maxLength" in error for error in _errors(paths))


@pytest.mark.parametrize(
    ("schema_name", "template_name"),
    [
        ("taxonomy-row.schema.json", "taxonomy-matrix-v1.csv"),
        ("confusion-group.schema.json", "confusion-groups-v1.csv"),
    ],
)
def test_csv_template_header_exactly_matches_required_schema_properties(
    schema_name: str,
    template_name: str,
) -> None:
    schema = json.loads((SCHEMA_DIR / schema_name).read_text(encoding="utf-8"))
    with (TEMPLATES / template_name).open("r", encoding="utf-8", newline="") as handle:
        headers = next(csv.reader(handle, strict=True))

    properties = list(schema["properties"])
    assert headers == properties
    assert set(schema["required"]) == set(properties)
    assert schema["additionalProperties"] is False


def test_unknown_column_is_rejected(tmp_path: Path) -> None:
    paths = _copy_valid_fixture(tmp_path)

    def add_column(rows: list[dict[str, str]], fieldnames: list[str]) -> None:
        fieldnames.append("unexpected_column")
        for row in rows:
            row["unexpected_column"] = "unexpected"

    _mutate_csv(paths.taxonomy_csv, add_column)

    assert any("unknown column: unexpected_column" in error for error in _errors(paths))


def test_duplicate_group_id_is_rejected(tmp_path: Path) -> None:
    paths = _copy_valid_fixture(tmp_path)

    def duplicate_group(rows: list[dict[str, str]], _: list[str]) -> None:
        rows.append(dict(rows[0]))

    _mutate_csv(paths.confusion_groups_csv, duplicate_group)

    assert any("duplicate group_id" in error for error in _errors(paths))


def test_duplicate_taxon_in_confusion_group_is_rejected(tmp_path: Path) -> None:
    paths = _copy_valid_fixture(tmp_path)

    def duplicate_member(rows: list[dict[str, str]], _: list[str]) -> None:
        rows[0]["member_taxon_ids"] = (
            "tx_testus_borealis|tx_testus_obscurus|tx_testus_borealis"
        )

    _mutate_csv(paths.confusion_groups_csv, duplicate_member)

    assert any("member_taxon_ids: duplicate list item" in error for error in _errors(paths))


def test_dangerous_member_must_be_in_member_set(tmp_path: Path) -> None:
    paths = _copy_valid_fixture(tmp_path)

    def outside_member(rows: list[dict[str, str]], _: list[str]) -> None:
        rows[0]["dangerous_member_taxon_ids"] = "tx_testus"

    _mutate_csv(paths.confusion_groups_csv, outside_member)

    assert any("dangerous member is not a member" in error for error in _errors(paths))


def test_empty_confusion_group_is_rejected(tmp_path: Path) -> None:
    paths = _copy_valid_fixture(tmp_path)

    def empty_members(rows: list[dict[str, str]], _: list[str]) -> None:
        rows[0]["member_taxon_ids"] = ""

    _mutate_csv(paths.confusion_groups_csv, empty_members)

    assert any("member_taxon_ids: requires at least 2 item(s)" in error for error in _errors(paths))


def test_invalid_minimum_resolution_rank_is_rejected(tmp_path: Path) -> None:
    paths = _copy_valid_fixture(tmp_path)

    def invalid_minimum_rank(rows: list[dict[str, str]], _: list[str]) -> None:
        rows[0]["minimum_resolution_rank"] = "strain"

    _mutate_csv(paths.confusion_groups_csv, invalid_minimum_rank)

    assert any(
        "minimum_resolution_rank: invalid value 'strain'" in error
        for error in _errors(paths)
    )


def test_invalid_rank_is_rejected(tmp_path: Path) -> None:
    paths = _copy_valid_fixture(tmp_path)

    def invalid_rank(rows: list[dict[str, str]], _: list[str]) -> None:
        _set_taxon_field(rows, "tx_testus_borealis", "rank", "strain")

    _mutate_csv(paths.taxonomy_csv, invalid_rank)

    assert any(".rank: invalid value 'strain'" in error for error in _errors(paths))


def test_invalid_review_status_is_rejected(tmp_path: Path) -> None:
    paths = _copy_valid_fixture(tmp_path)

    def invalid_status(rows: list[dict[str, str]], _: list[str]) -> None:
        _set_taxon_field(rows, "tx_testus_borealis", "review_status", "MAYBE")

    _mutate_csv(paths.taxonomy_csv, invalid_status)

    assert any(".review_status: invalid value 'MAYBE'" in error for error in _errors(paths))


def test_validator_result_is_deterministic(tmp_path: Path) -> None:
    paths = _copy_valid_fixture(tmp_path)

    def create_errors(rows: list[dict[str, str]], _: list[str]) -> None:
        _set_taxon_field(rows, "tx_testus_borealis", "parent_taxon_id", "tx_unknown")
        _set_taxon_field(rows, "tx_testus_obscurus", "rank", "strain")

    _mutate_csv(paths.taxonomy_csv, create_errors)

    first = validate(paths)
    second = validate(paths)
    assert first == second
    assert first.errors == tuple(sorted(first.errors))


def test_shipped_invalid_fixture_is_rejected() -> None:
    errors = _errors(_paths(INVALID_FIXTURE))

    assert any("forbidden column: edible" in error for error in errors)


def test_cli_returns_nonzero_and_prints_sorted_errors(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "validate_taxonomy.py",
            "--taxonomy",
            str(INVALID_FIXTURE / "taxonomy-matrix-v1.csv"),
            "--confusion-groups",
            str(INVALID_FIXTURE / "confusion-groups-v1.csv"),
            "--review-record",
            str(INVALID_FIXTURE / "review-record-v1.json"),
        ],
    )

    assert main() == 1
    output = capsys.readouterr().out.splitlines()
    assert output[0].startswith("Taxonomy validation failed with")
    assert output[1:] == sorted(output[1:])


def test_unknown_json_record_field_is_rejected(tmp_path: Path) -> None:
    paths = _copy_valid_fixture(tmp_path)

    def add_unknown_field(data: dict[str, object]) -> None:
        record = _review_record(data, "tx_testus_borealis")
        record["unexpected_json_field"] = "synthetic"

    _mutate_reviews(paths.review_record_json, add_unknown_field)

    assert any("unknown field: unexpected_json_field" in error for error in _errors(paths))


def test_malformed_json_is_rejected_with_filename(tmp_path: Path) -> None:
    paths = _copy_valid_fixture(tmp_path)
    paths.review_record_json.write_text('{"records": [', encoding="utf-8")

    errors = _errors(paths)
    assert any("review-record-v1.json: cannot read JSON" in error for error in errors)


def test_missing_file_is_rejected_with_filename(tmp_path: Path) -> None:
    paths = _copy_valid_fixture(tmp_path)
    paths.confusion_groups_csv.unlink()

    errors = _errors(paths)
    assert any("confusion-groups-v1.csv: missing file" in error for error in errors)


def test_malformed_csv_is_rejected_with_filename(tmp_path: Path) -> None:
    paths = _copy_valid_fixture(tmp_path)
    paths.taxonomy_csv.write_text('"unterminated', encoding="utf-8")

    errors = _errors(paths)
    assert any("taxonomy-matrix-v1.csv: cannot read CSV" in error for error in errors)


def test_real_cli_valid_invalid_and_help_paths_do_not_mutate_inputs() -> None:
    tracked_inputs = [
        *(VALID_FIXTURE / name for name in (
            "taxonomy-matrix-v1.csv",
            "confusion-groups-v1.csv",
            "review-record-v1.json",
        )),
        *(INVALID_FIXTURE / name for name in (
            "taxonomy-matrix-v1.csv",
            "confusion-groups-v1.csv",
            "review-record-v1.json",
        )),
    ]
    before = {path: path.read_bytes() for path in tracked_inputs}
    valid = subprocess.run(
        [sys.executable, str(VALIDATOR)],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    invalid = subprocess.run(
        [
            sys.executable,
            str(VALIDATOR),
            "--taxonomy",
            str(INVALID_FIXTURE / "taxonomy-matrix-v1.csv"),
            "--confusion-groups",
            str(INVALID_FIXTURE / "confusion-groups-v1.csv"),
            "--review-record",
            str(INVALID_FIXTURE / "review-record-v1.json"),
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    help_result = subprocess.run(
        [sys.executable, str(VALIDATOR), "--help"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    assert valid.returncode == 0
    assert "Taxonomy validation passed" in valid.stdout
    assert invalid.returncode != 0
    assert "taxonomy-matrix-v1.csv" in invalid.stdout
    assert help_result.returncode == 0
    assert "--confusion-groups" in help_result.stdout
    assert {path: path.read_bytes() for path in tracked_inputs} == before


@pytest.mark.parametrize("transformation", ["MIRROR", "ROTATE", "CROP"])
def test_transformed_copy_is_not_an_allowed_view_type(
    tmp_path: Path,
    transformation: str,
) -> None:
    paths = _copy_valid_fixture(tmp_path)

    def add_transformed_view(rows: list[dict[str, str]], _: list[str]) -> None:
        rows[0]["required_view_types"] = f"CAP_TOP|{transformation}"

    _mutate_csv(paths.confusion_groups_csv, add_transformed_view)

    assert any(
        f"required_view_types[1]: invalid value '{transformation}'" in error
        for error in _errors(paths)
    )
