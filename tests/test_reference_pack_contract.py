from __future__ import annotations

import hashlib
import json
import shutil
import stat
import zipfile
from pathlib import Path

import pytest

from app.inference import NoModelInferenceEngine, ResultStatus, SafeInferenceRunner
from scripts.validate_reference_pack import (
    DEFAULT_PACK,
    DEFAULT_SCHEMA_ROOT,
    REFERENCE_PACK_ROOT,
    ReferencePackCompatibilityPolicy,
    ValidationLimits,
    _validate_schema_value,
    validate_reference_pack,
)


def _copy_pack(tmp_path: Path) -> Path:
    target = tmp_path / "pack"
    shutil.copytree(DEFAULT_PACK, target)
    return target


def _mutate_manifest(pack: Path, **changes: object) -> None:
    path = pack / "manifest.json"
    value = json.loads(path.read_text(encoding="utf-8"))
    value.update(changes)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def _mutate_file_manifest(pack: Path, mutate) -> None:
    path = pack / "file-manifest.json"
    value = json.loads(path.read_text(encoding="utf-8"))
    mutate(value["files"])
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def _errors(pack: Path, **kwargs: object) -> tuple[str, ...]:
    return validate_reference_pack(pack, **kwargs).errors


def _zip_pack(source: Path, archive: Path, extras: dict[str, bytes] | None = None) -> None:
    with zipfile.ZipFile(archive, "w", allowZip64=True) as handle:
        for path in sorted(source.rglob("*")):
            if path.is_file():
                handle.write(path, path.relative_to(source).as_posix())
        for name, payload in (extras or {}).items():
            handle.writestr(name, payload)


def test_valid_synthetic_structure_passes_contract_validation() -> None:
    result = validate_reference_pack(DEFAULT_PACK)

    assert result.ok
    assert result.pack_id == "pack_synthetic_karelia_northwest"
    assert result.production_approved is False


def test_all_versioned_reference_pack_json_is_strict_utf8_json() -> None:
    paths = sorted(REFERENCE_PACK_ROOT.rglob("*.json"))

    assert paths
    for path in paths:
        json.loads(path.read_text(encoding="utf-8"))


def test_manifest_and_file_manifest_templates_match_schemas() -> None:
    pairs = (
        ("manifest.json", "manifest.schema.json"),
        ("file-manifest.json", "file-manifest.schema.json"),
        ("signature.json", "signature.schema.json"),
        ("search-index-descriptor.json", "search-index-descriptor.schema.json"),
    )
    for template_name, schema_name in pairs:
        value = json.loads(
            (REFERENCE_PACK_ROOT / "templates" / template_name).read_text(
                encoding="utf-8"
            )
        )
        schema = json.loads(
            (DEFAULT_SCHEMA_ROOT / schema_name).read_text(encoding="utf-8")
        )
        errors: list[str] = []
        _validate_schema_value(value, schema, template_name, errors)
        assert errors == []


def test_shipped_invalid_fixtures_are_explicit() -> None:
    missing = REFERENCE_PACK_ROOT / "fixtures" / "invalid-synthetic" / "missing-manifest"
    traversal = (
        REFERENCE_PACK_ROOT / "fixtures" / "invalid-synthetic" / "path-traversal"
    )

    assert any("missing required file: manifest.json" in error for error in _errors(missing))
    file_manifest = json.loads(
        (traversal / "file-manifest.json").read_text(encoding="utf-8")
    )
    assert file_manifest["files"][0]["path"] == "../outside.json"


def test_without_pack_inference_is_unavailable() -> None:
    result = SafeInferenceRunner(NoModelInferenceEngine()).infer()

    assert result.status is ResultStatus.RECOGNITION_UNAVAILABLE


def test_missing_manifest_is_rejected(tmp_path: Path) -> None:
    pack = _copy_pack(tmp_path)
    (pack / "manifest.json").unlink()

    assert any("missing required file: manifest.json" in error for error in _errors(pack))


def test_unsupported_format_is_rejected(tmp_path: Path) -> None:
    pack = _copy_pack(tmp_path)
    _mutate_manifest(pack, pack_format_version="99.0.0")

    assert any("unsupported pack format" in error for error in _errors(pack))


def test_app_version_mismatch_is_rejected(tmp_path: Path) -> None:
    pack = _copy_pack(tmp_path)
    _mutate_manifest(pack, minimum_app_version="2.0.0", maximum_app_version="3.0.0")

    assert any("app version mismatch" in error for error in _errors(pack))


def test_model_mismatch_is_rejected(tmp_path: Path) -> None:
    pack = _copy_pack(tmp_path)
    _mutate_manifest(pack, model_id="other-model")

    assert any("model mismatch" in error for error in _errors(pack))


def test_embedding_model_mismatch_is_rejected(tmp_path: Path) -> None:
    pack = _copy_pack(tmp_path)
    _mutate_manifest(pack, embedding_model_id="other-embedding")

    assert any("embedding model mismatch" in error for error in _errors(pack))


def test_embedding_dimension_mismatch_is_rejected(tmp_path: Path) -> None:
    pack = _copy_pack(tmp_path)
    _mutate_manifest(pack, embedding_dimension=512)

    assert any("embedding dimension mismatch" in error for error in _errors(pack))


def test_taxonomy_mismatch_is_rejected(tmp_path: Path) -> None:
    pack = _copy_pack(tmp_path)
    _mutate_manifest(pack, taxonomy_version="other-taxonomy")

    assert any("taxonomy mismatch" in error for error in _errors(pack))


def test_confusion_groups_mismatch_is_rejected(tmp_path: Path) -> None:
    pack = _copy_pack(tmp_path)
    _mutate_manifest(pack, confusion_groups_version="other-confusion")

    assert any("confusion groups mismatch" in error for error in _errors(pack))


def test_open_set_mismatch_is_rejected(tmp_path: Path) -> None:
    pack = _copy_pack(tmp_path)
    _mutate_manifest(pack, open_set_version="other-open-set")

    assert any("open-set mismatch" in error for error in _errors(pack))


def test_calibration_mismatch_is_rejected(tmp_path: Path) -> None:
    pack = _copy_pack(tmp_path)
    _mutate_manifest(pack, calibration_version="other-calibration")

    assert any("calibration mismatch" in error for error in _errors(pack))


def test_risk_rules_mismatch_is_rejected(tmp_path: Path) -> None:
    pack = _copy_pack(tmp_path)
    _mutate_manifest(pack, risk_rules_version="other-risk-rules")

    assert any("risk rules mismatch" in error for error in _errors(pack))


def test_missing_required_file_is_rejected(tmp_path: Path) -> None:
    pack = _copy_pack(tmp_path)
    (pack / "taxonomy" / "taxonomy.json").unlink()

    assert any("missing required file: taxonomy/taxonomy.json" in error for error in _errors(pack))


def test_incorrect_sha256_is_rejected(tmp_path: Path) -> None:
    pack = _copy_pack(tmp_path)
    path = pack / "calibration" / "calibration.json"
    path.write_text("{}\n", encoding="utf-8")

    assert any(
        "calibration/calibration.json: incorrect SHA-256" in error
        for error in _errors(pack)
    )


def test_duplicate_declared_path_is_rejected(tmp_path: Path) -> None:
    pack = _copy_pack(tmp_path)
    _mutate_file_manifest(pack, lambda files: files.append(dict(files[0])))

    assert any("file-manifest.json: duplicate path" in error for error in _errors(pack))


def test_path_traversal_is_rejected(tmp_path: Path) -> None:
    pack = _copy_pack(tmp_path)

    def mutate(files: list[dict[str, object]]) -> None:
        files[0]["path"] = "../outside.json"

    _mutate_file_manifest(pack, mutate)

    assert any("unsafe path: ../outside.json" in error for error in _errors(pack))


def test_absolute_path_is_rejected(tmp_path: Path) -> None:
    pack = _copy_pack(tmp_path)

    def mutate(files: list[dict[str, object]]) -> None:
        files[0]["path"] = "C:/outside.json"

    _mutate_file_manifest(pack, mutate)

    assert any("unsafe path: C:/outside.json" in error for error in _errors(pack))


def test_backslash_traversal_is_rejected(tmp_path: Path) -> None:
    pack = _copy_pack(tmp_path)
    _mutate_file_manifest(pack, lambda files: files[0].update(path="..\\outside.json"))

    assert any("unsafe path: ..\\outside.json" in error for error in _errors(pack))


def test_url_encoded_traversal_is_rejected(tmp_path: Path) -> None:
    archive = tmp_path / "encoded.gribpack"
    _zip_pack(DEFAULT_PACK, archive, {"%2e%2e/outside.json": b"outside"})

    assert any("encoded unsafe path" in error for error in _errors(archive))


def test_case_insensitive_duplicate_zip_paths_are_rejected(tmp_path: Path) -> None:
    archive = tmp_path / "case-collision.gribpack"
    _zip_pack(DEFAULT_PACK, archive, {"MODEL/synthetic-model-contract.json": b"x"})

    assert any("normalized path collision" in error for error in _errors(archive))


def test_unicode_normalization_collision_is_rejected(tmp_path: Path) -> None:
    archive = tmp_path / "unicode-collision.gribpack"
    _zip_pack(
        DEFAULT_PACK,
        archive,
        {"metadata/caf\u00e9.json": b"a", "metadata/cafe\u0301.json": b"b"},
    )

    assert any("normalized path collision" in error for error in _errors(archive))


def test_nested_archive_is_rejected(tmp_path: Path) -> None:
    archive = tmp_path / "nested.gribpack"
    _zip_pack(DEFAULT_PACK, archive, {"metadata/nested.zip": b"PK"})

    assert any("nested archive is forbidden" in error for error in _errors(archive))


def test_zip_symlink_is_rejected(tmp_path: Path) -> None:
    archive = tmp_path / "symlink.gribpack"
    with zipfile.ZipFile(archive, "w", allowZip64=True) as handle:
        symlink = zipfile.ZipInfo("manifest.json")
        symlink.create_system = 3
        symlink.external_attr = (stat.S_IFLNK | 0o777) << 16
        handle.writestr(symlink, "target")

    assert any("symlink is forbidden: manifest.json" in error for error in _errors(archive))


def test_zip_duplicate_path_is_rejected(tmp_path: Path) -> None:
    archive = tmp_path / "duplicate.gribpack"
    with zipfile.ZipFile(archive, "w", allowZip64=True) as handle:
        handle.writestr("manifest.json", "{}")
        with pytest.warns(UserWarning, match="Duplicate name"):
            handle.writestr("manifest.json", "{}")

    assert any("archive: duplicate path: manifest.json" in error for error in _errors(archive))


def test_unpacked_size_overflow_is_rejected(tmp_path: Path) -> None:
    pack = _copy_pack(tmp_path)
    _mutate_manifest(pack, declared_unpacked_size_bytes=10_000)
    limits = ValidationLimits(max_unpacked_size_bytes=5_000)

    assert any("declared unpacked-size overflow" in error for error in _errors(pack, limits=limits))


def test_signed_long_overflow_in_declared_sizes_is_rejected(tmp_path: Path) -> None:
    pack = _copy_pack(tmp_path)
    _mutate_manifest(pack, declared_unpacked_size_bytes=1 << 63)
    _mutate_file_manifest(pack, lambda files: files[0].update(size_bytes=1 << 63))

    errors = _errors(pack)
    assert any("declared unpacked-size overflow" in error for error in errors)
    assert any("value exceeds maximum" in error for error in errors)


def test_archive_and_file_manifest_size_mismatch_is_rejected(tmp_path: Path) -> None:
    pack = _copy_pack(tmp_path)
    _mutate_file_manifest(pack, lambda files: files[0].update(size_bytes=999))

    assert any("declared size mismatch" in error for error in _errors(pack))


def test_file_changed_after_validation_is_rejected_on_recheck(tmp_path: Path) -> None:
    pack = _copy_pack(tmp_path)
    assert validate_reference_pack(pack).ok

    (pack / "taxonomy" / "taxonomy.json").write_text("{}\n", encoding="utf-8")

    assert any("incorrect SHA-256" in error for error in _errors(pack))


def test_unknown_manifest_property_is_rejected_in_python(tmp_path: Path) -> None:
    pack = _copy_pack(tmp_path)
    _mutate_manifest(pack, unexpected_contract_bypass=True)

    assert any("unknown field: unexpected_contract_bypass" in error for error in _errors(pack))


def test_excessive_file_count_is_rejected() -> None:
    limits = ValidationLimits(max_file_count=2)

    assert any("excessive file count" in error for error in _errors(DEFAULT_PACK, limits=limits))


def test_missing_signature_is_rejected_for_activation(tmp_path: Path) -> None:
    pack = _copy_pack(tmp_path)
    _mutate_manifest(
        pack,
        signature_required=True,
        signature_algorithm="ED25519",
        signing_key_id="key_missing",
        production_approved=True,
    )

    errors = _errors(pack, require_production=True)
    assert any("missing required production signature" in error for error in errors)


def test_unknown_signing_key_is_rejected(tmp_path: Path) -> None:
    pack = _copy_pack(tmp_path)
    _mutate_manifest(
        pack,
        signature_required=True,
        signature_algorithm="ED25519",
        signing_key_id="key_unknown",
        production_approved=True,
    )
    (pack / "signature.json").write_text(
        json.dumps(
            {
                "algorithm": "ED25519",
                "signing_key_id": "key_unknown",
                "signature": "synthetic-not-a-signature",
            }
        )
        + "\n",
        encoding="utf-8",
    )

    errors = _errors(pack, require_production=True)
    assert any("unknown signing key: key_unknown" in error for error in errors)


def test_signature_envelope_must_bind_all_control_manifests(tmp_path: Path) -> None:
    pack = _copy_pack(tmp_path)
    _mutate_manifest(
        pack,
        signature_required=True,
        signature_algorithm="ED25519",
        signing_key_id="key_contract",
        production_approved=True,
    )
    def digest(name: str) -> str:
        return hashlib.sha256((pack / name).read_bytes()).hexdigest()
    (pack / "signature.json").write_text(
        json.dumps(
            {
                "algorithm": "ED25519",
                "signing_key_id": "key_contract",
                "manifest_sha256": "0" * 64,
                "file_manifest_sha256": digest("file-manifest.json"),
                "checksums_sha256": digest("checksums.sha256"),
                "signature": "contract-only-not-cryptographic-proof",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    policy = ReferencePackCompatibilityPolicy(
        known_signing_key_ids=frozenset({"key_contract"})
    )

    errors = _errors(pack, policy=policy, require_production=True)
    assert any("manifest_sha256: signed payload mismatch" in error for error in errors)
    assert any("cryptographic verification is not implemented" in error for error in errors)


def test_synthetic_unapproved_pack_cannot_activate() -> None:
    errors = _errors(DEFAULT_PACK, require_production=True)

    assert any("production_approved=false cannot activate" in error for error in errors)


def test_corrupted_index_is_rejected(tmp_path: Path) -> None:
    pack = _copy_pack(tmp_path)
    index = pack / "search-index" / "exact-baseline-index.json"
    index.write_text('{"corrupted": true}\n', encoding="utf-8")

    assert any("exact-baseline-index.json: incorrect SHA-256" in error for error in _errors(pack))


def test_incompatible_engine_version_is_rejected(tmp_path: Path) -> None:
    pack = _copy_pack(tmp_path)
    _mutate_manifest(pack, vector_search_engine_version="99.0.0")

    assert any("incompatible engine version" in error for error in _errors(pack))


def test_policy_can_reject_embedding_contract_without_changing_fixture(tmp_path: Path) -> None:
    pack = _copy_pack(tmp_path)
    policy = ReferencePackCompatibilityPolicy(embedding_dimension=8)

    assert any("embedding dimension mismatch" in error for error in _errors(pack, policy=policy))


def test_ci_keeps_reference_validation_between_pytest_and_safety_gates() -> None:
    workflow = (Path(".github/workflows/ci.yml")).read_text(encoding="utf-8")

    assert workflow.index("python -m pytest") < workflow.index(
        "python scripts/validate_reference_pack.py"
    ) < workflow.index("python scripts/safety_gate.py")
    assert "validate_reference_pack.py --require-production" in workflow
    assert "download" not in workflow.lower()
    assert "secrets." not in workflow
