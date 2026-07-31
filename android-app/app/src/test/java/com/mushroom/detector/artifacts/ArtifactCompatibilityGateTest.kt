package com.mushroom.detector.artifacts

import com.mushroom.detector.inference.ModelDescriptor
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class ArtifactCompatibilityGateTest {
    private val matrix = CompatibilityMatrix(
        inputContractVersion = "input-v1",
        taxonomyVersion = "taxonomy-v1",
        calibrationVersion = "calibration-v1",
        riskRulesVersion = "risk-v1"
    )
    private val descriptor = ModelDescriptor("model-a", "1", "input-v1", "0".repeat(64))
    private val manifest = ArtifactBundleManifest(
        modelId = "model-a",
        modelVersion = "1",
        inputContractVersion = "input-v1",
        taxonomyVersion = "taxonomy-v1",
        calibrationVersion = "calibration-v1",
        riskRulesVersion = "risk-v1"
    )

    @Test
    fun reportsNoModelForIncompleteBundle() {
        val result = ArtifactCompatibilityGate(matrix).validate(null, null)

        assertEquals(CompatibilityStatus.NO_MODEL, result.status)
    }

    @Test
    fun acceptsOnlyExactContractMatch() {
        val result = ArtifactCompatibilityGate(matrix).validate(descriptor, manifest)

        assertEquals(CompatibilityStatus.COMPATIBLE, result.status)
        assertTrue(result.reasons.isEmpty())
    }

    @Test
    fun rejectsCalibrationMismatch() {
        val result = ArtifactCompatibilityGate(matrix).validate(
            descriptor,
            manifest.copy(calibrationVersion = "other")
        )

        assertEquals(CompatibilityStatus.INCOMPATIBLE, result.status)
        assertTrue(result.reasons.contains("unsupported calibration"))
    }
}
