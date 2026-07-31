from app.artifacts import (
    ArtifactBundleManifest,
    ArtifactCompatibilityGate,
    CompatibilityMatrix,
    CompatibilityStatus,
    ModelDescriptor,
)
from app.inference import (
    InferenceResult,
    ResultStatus,
    SafeInferenceRunner,
)

MATRIX = CompatibilityMatrix("input-v1", "taxonomy-v1", "calibration-v1", "risk-v1")
DESCRIPTOR = ModelDescriptor("model-a", "1", "input-v1", "0" * 64)
MANIFEST = ArtifactBundleManifest(
    "model-a",
    "1",
    "input-v1",
    "taxonomy-v1",
    "calibration-v1",
    "risk-v1",
)


def test_gate_reports_no_model_for_incomplete_bundle() -> None:
    result = ArtifactCompatibilityGate(MATRIX).validate(None, None)

    assert result.status is CompatibilityStatus.NO_MODEL


def test_gate_accepts_exact_contract_match() -> None:
    result = ArtifactCompatibilityGate(MATRIX).validate(DESCRIPTOR, MANIFEST)

    assert result.status is CompatibilityStatus.COMPATIBLE
    assert result.reasons == ()


def test_gate_rejects_calibration_mismatch() -> None:
    manifest = ArtifactBundleManifest(
        "model-a",
        "1",
        "input-v1",
        "taxonomy-v1",
        "other-calibration",
        "risk-v1",
    )

    result = ArtifactCompatibilityGate(MATRIX).validate(DESCRIPTOR, manifest)

    assert result.status is CompatibilityStatus.INCOMPATIBLE
    assert "unsupported calibration" in result.reasons


class RegisteredEngine:
    descriptor = DESCRIPTOR

    def __init__(self) -> None:
        self.invoked = False

    def infer(self, image_bytes: bytes | None = None) -> InferenceResult:
        del image_bytes
        self.invoked = True
        raise AssertionError("incompatible engine must not run")


def test_incompatible_bundle_maps_to_technical_failure_without_inference() -> None:
    incompatible = ArtifactBundleManifest(
        "model-a",
        "1",
        "input-v1",
        "taxonomy-v1",
        "untrusted-calibration",
        "risk-v1",
    )
    engine = RegisteredEngine()

    result = SafeInferenceRunner(
        engine,
        ArtifactCompatibilityGate(MATRIX),
        incompatible,
    ).infer()

    assert result.status is ResultStatus.TECHNICAL_FAILURE
    assert engine.invoked is False
    assert result.emergency_url == "/emergency"
