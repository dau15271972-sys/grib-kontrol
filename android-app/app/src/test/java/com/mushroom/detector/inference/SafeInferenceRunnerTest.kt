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
        modelId = "model-a",
        modelVersion = "1",
        inputContractVersion = "input-v1",
        taxonomyVersion = "taxonomy-v1",
        calibrationVersion = "calibration-v1",
        riskRulesVersion = "risk-v1",
        packFormatVersion = "1.0.0",
        packId = "pack_contract_test",
        packVersion = "1.0.0-test",
        modelContractVersion = "model-contract-v1",
        modelSha256 = "0".repeat(64),
        embeddingModelId = "synthetic-embedding-model",
        embeddingDimension = 4,
        confusionGroupsVersion = "1.0.0",
        openSetVersion = "synthetic-open-set-v1",
        vectorSearchEngine = com.mushroom.detector.artifacts.SearchIndexFormat.EXACT_BASELINE,
        vectorSearchEngineVersion = "1.0.0",
        searchIndexFormatVersion = "exact-json-v1",
        productionApproved = true,
        signatureTrusted = true,
        active = true
    )

    @Test
    fun syntheticExactBundleCannotReachInjectedEngine() {
        var invoked = false
        val failingEngine = object : InferenceEngine {
            override val descriptor: ModelDescriptor = this@SafeInferenceRunnerTest.descriptor

            override fun infer(session: ObservationSession): com.mushroom.detector.MushroomApiResponse {
                invoked = true
                throw IllegalStateException("synthetic failure")
            }
        }

        val result = SafeInferenceRunner(
            failingEngine,
            ArtifactCompatibilityGate(matrix),
            manifest
        ).run(ObservationSession())

        assertEquals(ResultStatus.RECOGNITION_UNAVAILABLE, result.status)
        assertEquals(false, invoked)
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

        assertEquals(ResultStatus.RECOGNITION_UNAVAILABLE, result.status)
        assertEquals(false, invoked)
        assertTrue(EmergencyAvailabilityPolicy.isAvailable(result.status))
    }

    @Test
    fun registeredEngineWithoutActivePackIsNotInvoked() {
        var invoked = false
        val engine = object : InferenceEngine {
            override val descriptor: ModelDescriptor = this@SafeInferenceRunnerTest.descriptor

            override fun infer(session: ObservationSession): com.mushroom.detector.MushroomApiResponse {
                invoked = true
                return NoModelInferenceEngine().infer(session)
            }
        }

        val result = SafeInferenceRunner(engine).run(ObservationSession())

        assertEquals(ResultStatus.RECOGNITION_UNAVAILABLE, result.status)
        assertEquals(false, invoked)
    }
}
