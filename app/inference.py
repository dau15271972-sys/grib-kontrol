from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import StrEnum
from typing import Protocol

from app.artifacts import (
    ArtifactBundleManifest,
    ArtifactCompatibilityGate,
    CompatibilityStatus,
    ModelDescriptor,
)


class ResultStatus(StrEnum):
    RECOGNITION_UNAVAILABLE = "RECOGNITION_UNAVAILABLE"
    TECHNICAL_FAILURE = "TECHNICAL_FAILURE"
    HIGH_RISK = "HIGH_RISK"
    NEED_MORE_PHOTOS = "NEED_MORE_PHOTOS"
    UNKNOWN = "UNKNOWN"
    POSSIBLE_TAXON = "POSSIBLE_TAXON"


@dataclass(frozen=True)
class InferenceResult:
    status: ResultStatus
    title: str
    message: str
    safety_banner: str
    emergency_url: str = "/emergency"

    def to_dict(self) -> dict[str, str]:
        payload = asdict(self)
        payload["status"] = self.status.value
        return payload


class InferenceEngine(Protocol):
    @property
    def descriptor(self) -> ModelDescriptor | None:
        """Describe the registered model, or None for the Stage A no-model engine."""

    def infer(self, image_bytes: bytes | None = None) -> InferenceResult:
        """Return only policy-safe, user-facing output."""


class NoModelInferenceEngine:
    """SAFETY: Stage B0 shell engine; it never guesses without a trusted pack."""

    descriptor: ModelDescriptor | None = None

    def infer(self, image_bytes: bytes | None = None) -> InferenceResult:
        del image_bytes
        return InferenceResult(
            status=ResultStatus.RECOGNITION_UNAVAILABLE,
            title="Распознавание недоступно",
            message=(
                "Активный проверенный автономный пакет знаний не установлен. "
                "По фотографии нельзя надёжно исключить опасный вариант."
            ),
            safety_banner=(
                "Не принимайте решение об употреблении гриба по результату приложения."
            ),
        )


def technical_failure_result() -> InferenceResult:
    return InferenceResult(
        status=ResultStatus.TECHNICAL_FAILURE,
        title="Обработка завершилась не полностью",
        message="Безопасно исключить опасный вариант невозможно.",
        safety_banner=(
            "Не принимайте решение об употреблении гриба по результату приложения."
        ),
    )


class SafeInferenceRunner:
    """SAFETY: central fail-closed boundary for all inference calls."""

    def __init__(
        self,
        engine: InferenceEngine,
        compatibility_gate: ArtifactCompatibilityGate | None = None,
        manifest: ArtifactBundleManifest | None = None,
    ) -> None:
        self._engine = engine
        self._compatibility_gate = compatibility_gate
        self._manifest = manifest

    def infer(self, image_bytes: bytes | None = None) -> InferenceResult:
        if isinstance(self._engine, NoModelInferenceEngine):
            return self._engine.infer(image_bytes)

        descriptor = getattr(self._engine, "descriptor", ...)
        if descriptor is ...:
            return NoModelInferenceEngine().infer(image_bytes)
        if descriptor is None:
            return NoModelInferenceEngine().infer(image_bytes)
        if self._compatibility_gate is None or self._manifest is None:
            return NoModelInferenceEngine().infer(image_bytes)

        compatibility = self._compatibility_gate.validate(descriptor, self._manifest)
        if compatibility.status is CompatibilityStatus.NO_MODEL:
            return NoModelInferenceEngine().infer(image_bytes)
        if compatibility.status is CompatibilityStatus.INCOMPATIBLE:
            return NoModelInferenceEngine().infer(image_bytes)
        return self._run_engine(image_bytes)

    def _run_engine(self, image_bytes: bytes | None) -> InferenceResult:
        try:
            return self._engine.infer(image_bytes)
        except Exception:
            return technical_failure_result()
