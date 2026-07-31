from __future__ import annotations

import argparse
import hashlib
import json
import re
import stat
import unicodedata
import urllib.parse
import zipfile
from contextlib import AbstractContextManager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any, BinaryIO

ROOT = Path(__file__).resolve().parent.parent
REFERENCE_PACK_ROOT = ROOT / "data" / "reference-pack"
DEFAULT_PACK = REFERENCE_PACK_ROOT / "fixtures" / "valid-synthetic"
DEFAULT_SCHEMA_ROOT = REFERENCE_PACK_ROOT / "schema"

CONTROL_PATHS = frozenset(
    {"manifest.json", "file-manifest.json", "checksums.sha256", "signature.json"}
)
SHA256_RE = re.compile(r"^[a-f0-9]{64}$")
SEMVER_RE = re.compile(r"^([0-9]+)\.([0-9]+)\.([0-9]+)(?:-[a-z0-9.-]+)?$")
MAX_SIGNED_LONG = (1 << 63) - 1
NESTED_ARCHIVE_SUFFIXES = frozenset({".apk", ".gribpack", ".jar", ".zip"})
SUPPORTED_SCHEMA_KEYWORDS = frozenset(
    {
        "$id",
        "$schema",
        "additionalProperties",
        "const",
        "enum",
        "format",
        "items",
        "maximum",
        "minItems",
        "minLength",
        "minimum",
        "pattern",
        "properties",
        "required",
        "title",
        "type",
        "uniqueItems",
    }
)

ARTIFACT_HASH_FIELDS = (
    ("model_path", "model_sha256"),
    ("embedding_model_path", "embedding_model_sha256"),
    ("taxonomy_path", "taxonomy_sha256"),
    ("confusion_groups_path", "confusion_groups_sha256"),
    ("open_set_path", "open_set_sha256"),
    ("calibration_path", "calibration_sha256"),
    ("risk_rules_path", "risk_rules_sha256"),
    ("index_build_config_path", "index_build_config_sha256"),
    ("index_benchmark_report_path", "index_benchmark_report_sha256"),
    ("license_manifest_path", "license_manifest_sha256"),
)


@dataclass(frozen=True)
class ValidationLimits:
    max_file_count: int = 10_000
    max_unpacked_size_bytes: int = 5 * 1024 * 1024 * 1024
    max_single_file_size_bytes: int = 2 * 1024 * 1024 * 1024
    max_compression_ratio: float = 200.0
    max_json_size_bytes: int = 2 * 1024 * 1024
    hash_buffer_size_bytes: int = 1024 * 1024


@dataclass(frozen=True)
class ReferencePackCompatibilityPolicy:
    app_version: str = "1.0.0"
    pack_format_version: str = "1.0.0"
    model_contract_version: str = "model-contract-v1"
    model_id: str = "synthetic-model"
    embedding_model_id: str = "synthetic-embedding-model"
    embedding_dimension: int = 4
    embedding_dtype: str = "float32"
    taxonomy_version: str = "1.0.0"
    confusion_groups_version: str = "1.0.0"
    open_set_version: str = "synthetic-open-set-v1"
    calibration_version: str = "synthetic-calibration-v1"
    risk_rules_version: str = "synthetic-risk-rules-v1"
    vector_search_engine: str = "EXACT_BASELINE"
    vector_search_engine_version: str = "1.0.0"
    search_index_format_version: str = "exact-json-v1"
    index_algorithm: str = "EXACT"
    index_metric: str = "COSINE_DISTANCE_INTERNAL_ONLY"
    index_quantization: str = "NONE"
    exact_rerank_embedding_dtype: str = "float32"
    known_signing_key_ids: frozenset[str] = frozenset()


@dataclass(frozen=True)
class ReferencePackValidationResult:
    errors: tuple[str, ...]
    pack_id: str | None
    file_count: int
    unpacked_size_bytes: int
    production_approved: bool

    @property
    def ok(self) -> bool:
        return not self.errors


@dataclass(frozen=True)
class PackEntry:
    path: str
    size: int
    compressed_size: int
    is_symlink: bool
    is_special: bool = False


class PackSource(AbstractContextManager["PackSource"]):
    archive_size_bytes: int | None = None

    def entries(self) -> list[PackEntry]:
        raise NotImplementedError

    def open(self, path: str) -> BinaryIO:
        raise NotImplementedError

    def __exit__(self, *args: object) -> None:
        return None


class DirectoryPackSource(PackSource):
    def __init__(self, root: Path) -> None:
        self.root = root

    def entries(self) -> list[PackEntry]:
        entries: list[PackEntry] = []
        for path in sorted(self.root.rglob("*")):
            if not path.is_file() and not path.is_symlink():
                continue
            relative = path.relative_to(self.root).as_posix()
            is_symlink = path.is_symlink()
            size = 0 if is_symlink else path.stat().st_size
            entries.append(PackEntry(relative, size, size, is_symlink))
        return entries

    def open(self, path: str) -> BinaryIO:
        return (self.root / PurePosixPath(path)).open("rb")


class ZipPackSource(PackSource):
    def __init__(self, path: Path) -> None:
        self.path = path
        self.archive_size_bytes = path.stat().st_size
        self._zip = zipfile.ZipFile(path)
        self._infos = [info for info in self._zip.infolist() if not info.is_dir()]
        self._first_by_name: dict[str, zipfile.ZipInfo] = {}
        for info in self._infos:
            self._first_by_name.setdefault(info.filename, info)

    def entries(self) -> list[PackEntry]:
        return [
            PackEntry(
                info.filename,
                info.file_size,
                info.compress_size,
                stat.S_ISLNK(info.external_attr >> 16),
                _zip_entry_is_special(info),
            )
            for info in self._infos
        ]

    def open(self, path: str) -> BinaryIO:
        return self._zip.open(self._first_by_name[path])

    def __exit__(self, *args: object) -> None:
        self._zip.close()


def _open_pack(path: Path) -> PackSource:
    if path.is_dir():
        return DirectoryPackSource(path)
    if path.is_file() and (path.suffix.lower() == ".gribpack" or zipfile.is_zipfile(path)):
        return ZipPackSource(path)
    raise ValueError(f"pack source is neither a directory nor a ZIP64 container: {path}")


def _zip_entry_is_special(info: zipfile.ZipInfo) -> bool:
    if info.create_system != 3:
        return False
    mode = info.external_attr >> 16
    file_type = stat.S_IFMT(mode)
    return file_type not in {0, stat.S_IFREG, stat.S_IFLNK}


def _safe_pack_path(path: str) -> bool:
    if not path or "\\" in path or "\x00" in path:
        return False
    pure = PurePosixPath(path)
    if pure.is_absolute() or re.match(r"^[A-Za-z]:", path):
        return False
    return all(part not in {"", ".", ".."} for part in pure.parts)


def _normalized_collision_key(path: str) -> str:
    return unicodedata.normalize("NFC", path).casefold()


def _encoded_path_is_unsafe(path: str) -> bool:
    decoded = path
    for _ in range(3):
        next_value = urllib.parse.unquote(decoded)
        if next_value == decoded:
            break
        decoded = next_value
    return decoded != path and not _safe_pack_path(decoded)


def _path_collision_errors(paths: list[str], location: str) -> list[str]:
    first_by_key: dict[str, str] = {}
    errors: list[str] = []
    for path in paths:
        key = _normalized_collision_key(path)
        previous = first_by_key.get(key)
        if previous is not None and previous != path:
            errors.append(f"{location}: normalized path collision: {previous} <> {path}")
        else:
            first_by_key[key] = path
    return errors


def _bounded_sum(values: list[int], maximum: int) -> int | None:
    total = 0
    for value in values:
        if value < 0 or value > maximum - total:
            return None
        total += value
    return total


def _json_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _read_json(
    source: PackSource,
    path: str,
    limits: ValidationLimits,
    errors: list[str],
) -> Any:
    try:
        with source.open(path) as handle:
            payload = handle.read(limits.max_json_size_bytes + 1)
        if len(payload) > limits.max_json_size_bytes:
            errors.append(f"{path}: JSON exceeds bounded parser limit")
            return None
        return json.loads(payload.decode("utf-8"), object_pairs_hook=_json_pairs)
    except (KeyError, OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        errors.append(f"{path}: cannot read deterministic UTF-8 JSON: {exc}")
        return None


def _read_schema(path: Path, errors: list[str]) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_json_pairs)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        errors.append(f"{path.name}: cannot read schema: {exc}")
        return {}
    if not isinstance(value, dict):
        errors.append(f"{path.name}: schema root must be an object")
        return {}
    return value


def _audit_schema_keywords(rule: Any, location: str, errors: list[str]) -> None:
    if not isinstance(rule, dict):
        return
    for keyword in sorted(set(rule) - SUPPORTED_SCHEMA_KEYWORDS):
        errors.append(f"{location}: unsupported schema keyword: {keyword}")
    properties = rule.get("properties")
    if isinstance(properties, dict):
        for name, child in properties.items():
            _audit_schema_keywords(child, f"{location}.{name}", errors)
    items = rule.get("items")
    if isinstance(items, dict):
        _audit_schema_keywords(items, f"{location}[]", errors)


def _type_matches(value: Any, expected: str) -> bool:
    return {
        "array": isinstance(value, list),
        "boolean": isinstance(value, bool),
        "integer": isinstance(value, int) and not isinstance(value, bool),
        "null": value is None,
        "object": isinstance(value, dict),
        "string": isinstance(value, str),
    }.get(expected, False)


def _validate_schema_value(
    value: Any,
    rule: dict[str, Any],
    location: str,
    errors: list[str],
) -> None:
    expected = rule.get("type")
    expected_types = [expected] if isinstance(expected, str) else expected
    if isinstance(expected_types, list) and not any(
        isinstance(item, str) and _type_matches(value, item) for item in expected_types
    ):
        errors.append(f"{location}: invalid type")
        return
    if "const" in rule and value != rule["const"]:
        errors.append(f"{location}: must equal {rule['const']!r}")
    if "enum" in rule and value not in rule["enum"]:
        errors.append(f"{location}: value is outside enum")
    if isinstance(value, str):
        if len(value) < rule.get("minLength", 0):
            errors.append(f"{location}: string is too short")
        pattern = rule.get("pattern")
        if isinstance(pattern, str) and re.fullmatch(pattern, value) is None:
            errors.append(f"{location}: value does not match pattern")
        if rule.get("format") == "date-time":
            try:
                datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                errors.append(f"{location}: invalid ISO date-time")
    if isinstance(value, int) and not isinstance(value, bool):
        if "minimum" in rule and value < rule["minimum"]:
            errors.append(f"{location}: value is below minimum")
        if "maximum" in rule and value > rule["maximum"]:
            errors.append(f"{location}: value exceeds maximum")
    if isinstance(value, list):
        if len(value) < rule.get("minItems", 0):
            errors.append(f"{location}: too few items")
        serialised_items = {json.dumps(v, sort_keys=True) for v in value}
        if rule.get("uniqueItems") and len(serialised_items) != len(value):
            errors.append(f"{location}: duplicate array item")
        item_rule = rule.get("items")
        if isinstance(item_rule, dict):
            for index, item in enumerate(value):
                _validate_schema_value(item, item_rule, f"{location}[{index}]", errors)
    if isinstance(value, dict):
        properties = rule.get("properties")
        required = rule.get("required", [])
        if isinstance(properties, dict):
            for name in required:
                if name not in value:
                    errors.append(f"{location}: missing field: {name}")
            if rule.get("additionalProperties") is False:
                for name in sorted(set(value) - set(properties)):
                    errors.append(f"{location}: unknown field: {name}")
            for name, child in properties.items():
                if name in value and isinstance(child, dict):
                    _validate_schema_value(value[name], child, f"{location}.{name}", errors)


def _hash_stream(source: PackSource, path: str, buffer_size: int) -> str:
    digest = hashlib.sha256()
    with source.open(path) as handle:
        while chunk := handle.read(buffer_size):
            digest.update(chunk)
    return digest.hexdigest()


def _parse_semver(value: Any) -> tuple[int, int, int] | None:
    if not isinstance(value, str):
        return None
    match = SEMVER_RE.fullmatch(value)
    if match is None:
        return None
    return tuple(int(part) for part in match.groups())


def _validate_compatibility(
    manifest: dict[str, Any],
    policy: ReferencePackCompatibilityPolicy,
    errors: list[str],
) -> None:
    expected = {
        "pack_format_version": policy.pack_format_version,
        "model_contract_version": policy.model_contract_version,
        "model_id": policy.model_id,
        "embedding_model_id": policy.embedding_model_id,
        "embedding_dimension": policy.embedding_dimension,
        "embedding_dtype": policy.embedding_dtype,
        "taxonomy_version": policy.taxonomy_version,
        "confusion_groups_version": policy.confusion_groups_version,
        "open_set_version": policy.open_set_version,
        "calibration_version": policy.calibration_version,
        "risk_rules_version": policy.risk_rules_version,
        "vector_search_engine": policy.vector_search_engine,
        "vector_search_engine_version": policy.vector_search_engine_version,
        "search_index_format_version": policy.search_index_format_version,
        "index_algorithm": policy.index_algorithm,
        "index_metric": policy.index_metric,
        "index_quantization": policy.index_quantization,
        "exact_rerank_enabled": True,
        "exact_rerank_embedding_dtype": policy.exact_rerank_embedding_dtype,
    }
    labels = {
        "pack_format_version": "unsupported pack format",
        "model_contract_version": "model contract mismatch",
        "model_id": "model mismatch",
        "embedding_model_id": "embedding model mismatch",
        "embedding_dimension": "embedding dimension mismatch",
        "embedding_dtype": "embedding dtype mismatch",
        "taxonomy_version": "taxonomy mismatch",
        "confusion_groups_version": "confusion groups mismatch",
        "open_set_version": "open-set mismatch",
        "calibration_version": "calibration mismatch",
        "risk_rules_version": "risk rules mismatch",
        "vector_search_engine": "vector search engine mismatch",
        "vector_search_engine_version": "incompatible engine version",
        "search_index_format_version": "search index format mismatch",
        "index_algorithm": "index algorithm mismatch",
        "index_metric": "index metric mismatch",
        "index_quantization": "index quantization mismatch",
        "exact_rerank_enabled": "exact reranking is required",
        "exact_rerank_embedding_dtype": "exact rerank dtype mismatch",
    }
    for field, expected_value in expected.items():
        if manifest.get(field) != expected_value:
            errors.append(f"manifest.json.{field}: {labels[field]}")

    app = _parse_semver(policy.app_version)
    minimum = _parse_semver(manifest.get("minimum_app_version"))
    maximum = _parse_semver(manifest.get("maximum_app_version"))
    if app is None or minimum is None or maximum is None or not minimum <= app <= maximum:
        errors.append("manifest.json: app version mismatch")


def _validate_signature(
    source: PackSource,
    entry_paths: set[str],
    manifest: dict[str, Any],
    policy: ReferencePackCompatibilityPolicy,
    limits: ValidationLimits,
    signature_schema: dict[str, Any],
    require_production: bool,
    errors: list[str],
) -> None:
    signature_required = manifest.get("signature_required") is True
    if require_production and not signature_required:
        errors.append("manifest.json: production activation requires signature_required=true")
    if not signature_required:
        return
    if "signature.json" not in entry_paths:
        errors.append("signature.json: missing required production signature")
        return
    signature = _read_json(source, "signature.json", limits, errors)
    if not isinstance(signature, dict):
        return
    _validate_schema_value(signature, signature_schema, "signature.json", errors)
    required_fields = {
        "algorithm",
        "signing_key_id",
        "manifest_sha256",
        "file_manifest_sha256",
        "checksums_sha256",
        "signature",
    }
    for field in sorted(required_fields - set(signature)):
        errors.append(f"signature.json: missing field: {field}")
    for field in sorted(set(signature) - required_fields):
        errors.append(f"signature.json: unknown field: {field}")
    signing_key_id = signature.get("signing_key_id")
    if signing_key_id != manifest.get("signing_key_id"):
        errors.append("signature.json: signing key does not match manifest")
    if signing_key_id not in policy.known_signing_key_ids:
        errors.append(f"signature.json: unknown signing key: {signing_key_id}")
    if signature.get("algorithm") != manifest.get("signature_algorithm"):
        errors.append("signature.json: signature algorithm mismatch")
    if manifest.get("signature_algorithm") != "ED25519":
        errors.append("signature.json: unsupported signature algorithm")
    for path, field in (
        ("manifest.json", "manifest_sha256"),
        ("file-manifest.json", "file_manifest_sha256"),
        ("checksums.sha256", "checksums_sha256"),
    ):
        expected = signature.get(field)
        if not isinstance(expected, str) or SHA256_RE.fullmatch(expected) is None:
            errors.append(f"signature.json.{field}: invalid SHA-256")
        elif path in entry_paths and expected != _hash_stream(
            source, path, limits.hash_buffer_size_bytes
        ):
            errors.append(f"signature.json.{field}: signed payload mismatch")
    encoded_signature = signature.get("signature")
    if not isinstance(encoded_signature, str) or not encoded_signature:
        errors.append("signature.json.signature: missing signature bytes")
    # SAFETY: Stage B0 defines the signed envelope but has no approved trust-store
    # implementation. Metadata equality is never treated as cryptographic proof.
    errors.append("signature.json: cryptographic verification is not implemented")


def validate_reference_pack(
    pack_path: Path = DEFAULT_PACK,
    *,
    schema_root: Path = DEFAULT_SCHEMA_ROOT,
    policy: ReferencePackCompatibilityPolicy | None = None,
    limits: ValidationLimits | None = None,
    require_production: bool = False,
) -> ReferencePackValidationResult:
    policy = policy or ReferencePackCompatibilityPolicy()
    limits = limits or ValidationLimits()
    errors: list[str] = []
    pack_id: str | None = None
    production_approved = False
    entry_count = 0
    total_unpacked = 0

    manifest_schema = _read_schema(schema_root / "manifest.schema.json", errors)
    file_manifest_schema = _read_schema(schema_root / "file-manifest.schema.json", errors)
    signature_schema = _read_schema(schema_root / "signature.schema.json", errors)
    search_index_schema = _read_schema(
        schema_root / "search-index-descriptor.schema.json", errors
    )
    _audit_schema_keywords(manifest_schema, "manifest.schema.json", errors)
    _audit_schema_keywords(file_manifest_schema, "file-manifest.schema.json", errors)
    _audit_schema_keywords(signature_schema, "signature.schema.json", errors)
    _audit_schema_keywords(
        search_index_schema, "search-index-descriptor.schema.json", errors
    )

    try:
        source_context = _open_pack(pack_path)
    except (OSError, ValueError, zipfile.BadZipFile) as exc:
        return ReferencePackValidationResult((str(exc),), None, 0, 0, False)

    with source_context as source:
        entries = source.entries()
        entry_count = len(entries)
        bounded_total = _bounded_sum(
            [entry.size for entry in entries],
            min(limits.max_unpacked_size_bytes, MAX_SIGNED_LONG),
        )
        total_unpacked = bounded_total if bounded_total is not None else MAX_SIGNED_LONG
        paths = [entry.path for entry in entries]
        path_set = set(paths)

        for duplicate in sorted(path for path in path_set if paths.count(path) > 1):
            errors.append(f"archive: duplicate path: {duplicate}")
        errors.extend(_path_collision_errors(paths, "archive"))
        for entry in entries:
            if not _safe_pack_path(entry.path):
                errors.append(f"archive: unsafe path: {entry.path}")
            if _encoded_path_is_unsafe(entry.path):
                errors.append(f"archive: encoded unsafe path: {entry.path}")
            if entry.is_symlink:
                errors.append(f"archive: symlink is forbidden: {entry.path}")
            if entry.is_special:
                errors.append(f"archive: special or link entry is forbidden: {entry.path}")
            if PurePosixPath(entry.path).suffix.casefold() in NESTED_ARCHIVE_SUFFIXES:
                errors.append(f"archive: nested archive is forbidden: {entry.path}")
            if entry.size > limits.max_single_file_size_bytes:
                errors.append(f"archive: file exceeds size limit: {entry.path}")
            ratio = float("inf") if entry.compressed_size == 0 and entry.size else (
                entry.size / max(entry.compressed_size, 1)
            )
            if ratio > limits.max_compression_ratio:
                errors.append(f"archive: suspicious compression ratio: {entry.path}")
        if entry_count > limits.max_file_count:
            errors.append("archive: excessive file count")
        if bounded_total is None or total_unpacked > limits.max_unpacked_size_bytes:
            errors.append("archive: unpacked-size overflow")

        unsafe_control = {
            entry.path
            for entry in entries
            if entry.path in CONTROL_PATHS and (entry.is_symlink or entry.is_special)
        }
        if unsafe_control:
            return ReferencePackValidationResult(
                tuple(sorted(set(errors))), None, entry_count, total_unpacked, False
            )

        for required in ("manifest.json", "file-manifest.json", "checksums.sha256"):
            if required not in path_set:
                errors.append(f"archive: missing required file: {required}")
        if "manifest.json" not in path_set or "file-manifest.json" not in path_set:
            return ReferencePackValidationResult(
                tuple(sorted(set(errors))), None, entry_count, total_unpacked, False
            )

        manifest = _read_json(source, "manifest.json", limits, errors)
        file_manifest = _read_json(source, "file-manifest.json", limits, errors)
        if not isinstance(manifest, dict) or not isinstance(file_manifest, dict):
            return ReferencePackValidationResult(
                tuple(sorted(set(errors))), None, entry_count, total_unpacked, False
            )

        pack_id = manifest.get("pack_id") if isinstance(manifest.get("pack_id"), str) else None
        production_approved = manifest.get("production_approved") is True
        _validate_schema_value(manifest, manifest_schema, "manifest.json", errors)
        _validate_schema_value(file_manifest, file_manifest_schema, "file-manifest.json", errors)
        _validate_compatibility(manifest, policy, errors)

        raw_files = file_manifest.get("files")
        files = (
            [item for item in raw_files if isinstance(item, dict)]
            if isinstance(raw_files, list)
            else []
        )
        declared_paths = [item.get("path") for item in files if isinstance(item.get("path"), str)]
        duplicates = (
            path for path in set(declared_paths) if declared_paths.count(path) > 1
        )
        for duplicate in sorted(duplicates):
            errors.append(f"file-manifest.json: duplicate path: {duplicate}")
        errors.extend(_path_collision_errors(declared_paths, "file-manifest.json"))
        for path in declared_paths:
            if not _safe_pack_path(path):
                errors.append(f"file-manifest.json: unsafe path: {path}")
            if _encoded_path_is_unsafe(path):
                errors.append(f"file-manifest.json: encoded unsafe path: {path}")
            if PurePosixPath(path).suffix.casefold() in NESTED_ARCHIVE_SUFFIXES:
                errors.append(f"file-manifest.json: nested archive is forbidden: {path}")

        expected_payload_paths = set(declared_paths)
        unexpected = path_set - expected_payload_paths - CONTROL_PATHS
        for path in sorted(unexpected):
            errors.append(f"archive: file is not declared: {path}")
        for path in sorted(expected_payload_paths - path_set):
            errors.append(f"archive: missing required file: {path}")

        records_by_path: dict[str, dict[str, Any]] = {}
        for item in files:
            path = item.get("path")
            if isinstance(path, str) and path not in records_by_path:
                records_by_path[path] = item

        entry_by_path = {entry.path: entry for entry in entries if entry.path not in CONTROL_PATHS}
        for path, record in records_by_path.items():
            entry = entry_by_path.get(path)
            if entry is None or entry.is_symlink or not _safe_pack_path(path):
                continue
            if record.get("size_bytes") != entry.size:
                errors.append(f"{path}: declared size mismatch")
            expected_sha = record.get("sha256")
            if isinstance(expected_sha, str) and SHA256_RE.fullmatch(expected_sha):
                actual_sha = _hash_stream(source, path, limits.hash_buffer_size_bytes)
                if actual_sha != expected_sha:
                    errors.append(f"{path}: incorrect SHA-256")

        declared_count = manifest.get("file_count")
        if declared_count != len(files):
            errors.append("manifest.json.file_count: declared file count mismatch")
        declared_size = manifest.get("declared_unpacked_size_bytes")
        payload_sizes = [
            item.get("size_bytes", 0)
            for item in files
            if isinstance(item.get("size_bytes"), int)
            and not isinstance(item.get("size_bytes"), bool)
        ]
        bounded_payload_size = _bounded_sum(
            payload_sizes,
            min(limits.max_unpacked_size_bytes, MAX_SIGNED_LONG),
        )
        payload_size = (
            bounded_payload_size if bounded_payload_size is not None else MAX_SIGNED_LONG
        )
        if declared_size != payload_size:
            errors.append("manifest.json.declared_unpacked_size_bytes: declared size mismatch")
        if (
            bounded_payload_size is None
            or isinstance(declared_size, int)
            and (
                declared_size > limits.max_unpacked_size_bytes
                or declared_size > MAX_SIGNED_LONG
            )
        ):
            errors.append("manifest.json: declared unpacked-size overflow")
        if isinstance(declared_count, int) and declared_count > limits.max_file_count:
            errors.append("manifest.json: excessive declared file count")
        if source.archive_size_bytes is not None:
            declared_archive = manifest.get("declared_archive_size_bytes")
            if (
                not isinstance(declared_archive, int)
                or declared_archive != source.archive_size_bytes
            ):
                errors.append("manifest.json: declared archive size does not match container")

        for path_field, sha_field in ARTIFACT_HASH_FIELDS:
            path = manifest.get(path_field)
            record = records_by_path.get(path) if isinstance(path, str) else None
            if record is None:
                errors.append(f"manifest.json.{path_field}: path is not in file manifest")
            elif record.get("sha256") != manifest.get(sha_field):
                errors.append(f"manifest.json.{sha_field}: artifact hash mismatch")

        for control_path_field, control_hash_field in (
            ("file_manifest_path", "file_manifest_sha256"),
            ("checksums_path", "checksums_sha256"),
        ):
            control_path = manifest.get(control_path_field)
            if isinstance(control_path, str) and control_path in path_set:
                actual = _hash_stream(source, control_path, limits.hash_buffer_size_bytes)
                if actual != manifest.get(control_hash_field):
                    errors.append(f"manifest.json.{control_hash_field}: incorrect SHA-256")

        if "checksums.sha256" in path_set:
            try:
                with source.open("checksums.sha256") as handle:
                    checksum_text = handle.read(limits.max_json_size_bytes + 1).decode("utf-8")
                checksum_lines = [line for line in checksum_text.splitlines() if line]
                checksum_map: dict[str, str] = {}
                for line in checksum_lines:
                    match = re.fullmatch(r"([a-f0-9]{64})  (.+)", line)
                    if match is None:
                        errors.append("checksums.sha256: malformed line")
                        continue
                    digest, path = match.groups()
                    if path in checksum_map:
                        errors.append(f"checksums.sha256: duplicate path: {path}")
                    checksum_map[path] = digest
                expected_checksums = {
                    path: item.get("sha256") for path, item in records_by_path.items()
                }
                if checksum_map != expected_checksums:
                    errors.append("checksums.sha256: does not exactly match file manifest")
            except (KeyError, OSError, UnicodeDecodeError) as exc:
                errors.append(f"checksums.sha256: cannot read: {exc}")

        if require_production and not production_approved:
            errors.append("manifest.json: production_approved=false cannot activate")
        if require_production and manifest.get("vector_search_engine") == "EXACT_BASELINE":
            errors.append("manifest.json: EXACT_BASELINE is synthetic-only")
        _validate_signature(
            source,
            path_set,
            manifest,
            policy,
            limits,
            signature_schema,
            require_production,
            errors,
        )

    return ReferencePackValidationResult(
        tuple(sorted(set(errors))),
        pack_id,
        entry_count,
        total_unpacked,
        production_approved,
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate an offline .gribpack ZIP64 container or unpacked fixture."
    )
    parser.add_argument("--pack", type=Path, default=DEFAULT_PACK)
    parser.add_argument("--schema-root", type=Path, default=DEFAULT_SCHEMA_ROOT)
    parser.add_argument("--require-production", action="store_true")
    args = parser.parse_args()

    result = validate_reference_pack(
        args.pack,
        schema_root=args.schema_root,
        require_production=args.require_production,
    )
    if result.errors:
        print(f"Reference pack validation failed with {len(result.errors)} error(s):")
        print("\n".join(result.errors))
        return 1
    status = "production-approved" if result.production_approved else "synthetic/non-production"
    print(
        "Reference pack contract passed: "
        f"{result.pack_id}, {result.file_count} container file(s), {status}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
