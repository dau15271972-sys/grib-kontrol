package com.mushroom.detector.inference

import com.mushroom.detector.ResultStatus
import com.mushroom.detector.artifacts.ArtifactBundleManifest
import com.mushroom.detector.artifacts.ArtifactCompatibilityGate
import com.mushroom.detector.artifacts.CompatibilityMatrix
import com.mushroom.detector.capture.ObservationSession
import com.mushroom.detector.emergency.EmergencyAvailabilityPolicy
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class SafeInferenceRunnerTest {
    private val matrix = CompatibilityMatrix("input-v1", "taxonomy-v1", "calibration-v1", "risk-v1")
    private val descriptor = ModelDescriptor("model-a", "1", "input-v1", "0".repeat(64))
    private val manifest = ArtifactBundleManifest(
        "model-a",
        "1",
        "input-v1",
        "taxonomy-v1",
        "calibration-v1",
        "risk-v1"
    )

    @Test
    fun technicalFailureKeepsEmergencyRouteAvailable() {
        val failingEngine = object : InferenceEngine {
            override val descriptor: ModelDescriptor = this@SafeInferenceRunnerTest.descriptor

            override fun infer(session: ObservationSession) =
                throw IllegalStateException("synthetic failure")
        }

        val result = SafeInferenceRunner(
            failingEngine,
            ArtifactCompatibilityGate(matrix),
            manifest
        ).run(ObservationSession())

        assertEquals(ResultStatus.TECHNICAL_FAILURE, result.status)
        assertTrue(EmergencyAvailabilityPolicy.isAvailable(result.status))
    }

    @Test
    fun incompatibleArtifactsReturnTechnicalFailureWithoutRunningEngine() {
        var invoked = false
        val engine = object : InferenceEngine {
            override val descriptor: ModelDescriptor = this@SafeInferenceRunnerTest.descriptor

            override fun infer(session: ObservationSession): com.mushroom.detector.MushroomApiResponse {
                invoked = true
                return NoModelInferenceEngine().infer(session)
            }
        }

        val result = SafeInferenceRunner(
            engine,
            ArtifactCompatibilityGate(matrix),
            manifest.copy(calibrationVersion = "untrusted")
        ).run(ObservationSession())

        assertEquals(ResultStatus.TECHNICAL_FAILURE, result.status)
        assertEquals(false, invoked)
        assertTrue(EmergencyAvailabilityPolicy.isAvailable(result.status))
    }
}
