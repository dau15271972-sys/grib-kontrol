from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class CompatibilityStatus(StrEnum):
    COMPATIBLE = "COMPATIBLE"
    NO_MODEL = "NO_MODEL"
    INCOMPATIBLE = "INCOMPATIBLE"


@dataclass(frozen=True)
class ModelDescriptor:
    model_id: str
    model_version: str
    input_contract_version: str
    sha256: str


@dataclass(frozen=True)
class ArtifactBundleManifest:
    model_id: str
    model_version: str
    input_contract_version: str
    taxonomy_version: str
    calibration_version: str
    risk_rules_version: str
    pack_format_version: str = ""
    pack_id: str = ""
    pack_version: str = ""
    model_contract_version: str = ""
    model_sha256: str = ""
    embedding_model_id: str = ""
    embedding_dimension: int = 0
    confusion_groups_version: str = ""
    open_set_version: str = ""
    vector_search_engine: str = ""
    vector_search_engine_version: str = ""
    search_index_format_version: str = ""
    production_approved: bool = False
    signature_trusted: bool = False
    active: bool = False


@dataclass(frozen=True)
class CompatibilityMatrix:
    input_contract_version: str
    taxonomy_version: str
    calibration_version: str
    risk_rules_version: str
    pack_format_version: str = "1.0.0"
    model_contract_version: str = "model-contract-v1"
    embedding_model_id: str = "synthetic-embedding-model"
    embedding_dimension: int = 4
    confusion_groups_version: str = "1.0.0"
    open_set_version: str = "synthetic-open-set-v1"
    vector_search_engine: str = "EXACT_BASELINE"
    vector_search_engine_version: str = "1.0.0"
    search_index_format_version: str = "exact-json-v1"


@dataclass(frozen=True)
class CompatibilityResult:
    status: CompatibilityStatus
    reasons: tuple[str, ...] = ()


class ArtifactCompatibilityGate:
    """SAFETY: blocks inference unless all independently versioned parts agree."""

    def __init__(self, matrix: CompatibilityMatrix) -> None:
        self._matrix = matrix

    def validate(
        self,
        descriptor: ModelDescriptor | None,
        manifest: ArtifactBundleManifest | None,
    ) -> CompatibilityResult:
        if descriptor is None or manifest is None:
            return CompatibilityResult(
                CompatibilityStatus.NO_MODEL,
                ("A complete approved model bundle is not installed.",),
            )

        reasons: list[str] = []
        if descriptor.model_id != manifest.model_id:
            reasons.append("model_id mismatch")
        if descriptor.model_version != manifest.model_version:
            reasons.append("model_version mismatch")
        if descriptor.input_contract_version != manifest.input_contract_version:
            reasons.append("descriptor input contract mismatch")
        if manifest.input_contract_version != self._matrix.input_contract_version:
            reasons.append("unsupported input contract")
        if manifest.taxonomy_version != self._matrix.taxonomy_version:
            reasons.append("unsupported taxonomy")
        if manifest.calibration_version != self._matrix.calibration_version:
            reasons.append("unsupported calibration")
        if manifest.risk_rules_version != self._matrix.risk_rules_version:
            reasons.append("unsupported risk rules")
        if manifest.pack_format_version != self._matrix.pack_format_version:
            reasons.append("unsupported pack format")
        if manifest.model_contract_version != self._matrix.model_contract_version:
            reasons.append("unsupported model contract")
        if descriptor.sha256 != manifest.model_sha256:
            reasons.append("model SHA-256 mismatch")
        if manifest.embedding_model_id != self._matrix.embedding_model_id:
            reasons.append("unsupported embedding model")
        if manifest.embedding_dimension != self._matrix.embedding_dimension:
            reasons.append("unsupported embedding dimension")
        if manifest.confusion_groups_version != self._matrix.confusion_groups_version:
            reasons.append("unsupported confusion groups")
        if manifest.open_set_version != self._matrix.open_set_version:
            reasons.append("unsupported open-set contract")
        if manifest.vector_search_engine != self._matrix.vector_search_engine:
            reasons.append("unsupported vector search engine")
        if manifest.vector_search_engine == "EXACT_BASELINE":
            reasons.append("synthetic exact search is forbidden in production")
        if (
            manifest.vector_search_engine_version
            != self._matrix.vector_search_engine_version
        ):
            reasons.append("unsupported vector search engine version")
        if manifest.search_index_format_version != self._matrix.search_index_format_version:
            reasons.append("unsupported search index format")
        if not manifest.production_approved:
            reasons.append("pack is not production approved")
        if not manifest.signature_trusted:
            reasons.append("pack signature is untrusted")
        if not manifest.active:
            reasons.append("pack is not active")

        if reasons:
            return CompatibilityResult(
                CompatibilityStatus.INCOMPATIBLE,
                tuple(reasons),
            )
        return CompatibilityResult(CompatibilityStatus.COMPATIBLE)
