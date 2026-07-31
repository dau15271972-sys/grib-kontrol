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


@dataclass(frozen=True)
class CompatibilityMatrix:
    input_contract_version: str
    taxonomy_version: str
    calibration_version: str
    risk_rules_version: str


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

        if reasons:
            return CompatibilityResult(
                CompatibilityStatus.INCOMPATIBLE,
                tuple(reasons),
            )
        return CompatibilityResult(CompatibilityStatus.COMPATIBLE)
