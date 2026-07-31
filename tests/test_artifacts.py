from dataclasses import replace

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
    model_id="model-a",
    model_version="1",
    input_contract_version="input-v1",
    taxonomy_version="taxonomy-v1",
    calibration_version="calibration-v1",
    risk_rules_version="risk-v1",
    pack_format_version="1.0.0",
    pack_id="pack_contract_test",
    pack_version="1.0.0-test",
    model_contract_version="model-contract-v1",
    model_sha256="0" * 64,
    embedding_model_id="synthetic-embedding-model",
    embedding_dimension=4,
    confusion_groups_version="1.0.0",
    open_set_version="synthetic-open-set-v1",
    vector_search_engine="EXACT_BASELINE",
    vector_search_engine_version="1.0.0",
    search_index_format_version="exact-json-v1",
    production_approved=True,
    signature_trusted=True,
    active=True,
)


def test_gate_reports_no_model_for_incomplete_bundle() -> None:
    result = ArtifactCompatibilityGate(MATRIX).validate(None, None)

    assert result.status is CompatibilityStatus.NO_MODEL


def test_gate_rejects_synthetic_exact_contract_in_production() -> None:
    result = ArtifactCompatibilityGate(MATRIX).validate(DESCRIPTOR, MANIFEST)

    assert result.status is CompatibilityStatus.INCOMPATIBLE
    assert "synthetic exact search is forbidden in production" in result.reasons


def test_gate_rejects_calibration_mismatch() -> None:
    manifest = replace(MANIFEST, calibration_version="other-calibration")

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
    incompatible = replace(MANIFEST, calibration_version="untrusted-calibration")
    engine = RegisteredEngine()

    result = SafeInferenceRunner(
        engine,
        ArtifactCompatibilityGate(MATRIX),
        incompatible,
    ).infer()

    assert result.status is ResultStatus.RECOGNITION_UNAVAILABLE
    assert engine.invoked is False
    assert result.emergency_url == "/emergency"


def test_unapproved_pack_is_incompatible() -> None:
    result = ArtifactCompatibilityGate(MATRIX).validate(
        DESCRIPTOR,
        replace(MANIFEST, production_approved=False),
    )

    assert result.status is CompatibilityStatus.INCOMPATIBLE
    assert "pack is not production approved" in result.reasons
