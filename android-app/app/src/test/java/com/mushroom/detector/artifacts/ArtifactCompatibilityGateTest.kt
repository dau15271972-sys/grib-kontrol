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
        vectorSearchEngine = SearchIndexFormat.EXACT_BASELINE,
        vectorSearchEngineVersion = "1.0.0",
        searchIndexFormatVersion = "exact-json-v1",
        productionApproved = true,
        signatureTrusted = true,
        active = true
    )

    @Test
    fun reportsNoModelForIncompleteBundle() {
        val result = ArtifactCompatibilityGate(matrix).validate(null, null)

        assertEquals(CompatibilityStatus.NO_MODEL, result.status)
    }

    @Test
    fun rejectsSyntheticExactContractInProduction() {
        val result = ArtifactCompatibilityGate(matrix).validate(descriptor, manifest)

        assertEquals(CompatibilityStatus.INCOMPATIBLE, result.status)
        assertTrue(result.reasons.contains("synthetic exact search is forbidden in production"))
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

    @Test
    fun rejectsUnapprovedPack() {
        val result = ArtifactCompatibilityGate(matrix).validate(
            descriptor,
            manifest.copy(productionApproved = false)
        )

        assertEquals(CompatibilityStatus.INCOMPATIBLE, result.status)
        assertTrue(result.reasons.contains("pack is not production approved"))
    }
}
