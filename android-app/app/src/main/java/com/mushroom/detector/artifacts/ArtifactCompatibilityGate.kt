package com.mushroom.detector.artifacts

import com.mushroom.detector.inference.ModelDescriptor

enum class CompatibilityStatus {
    COMPATIBLE,
    NO_MODEL,
    INCOMPATIBLE
}

data class CompatibilityResult(
    val status: CompatibilityStatus,
    val reasons: List<String> = emptyList()
)

class ArtifactCompatibilityGate(
    private val matrix: CompatibilityMatrix
) {
    // SAFETY: future engines may run only after this exact contract check succeeds.
    fun validate(
        descriptor: ModelDescriptor?,
        manifest: ArtifactBundleManifest?
    ): CompatibilityResult {
        if (descriptor == null || manifest == null) {
            return CompatibilityResult(
                CompatibilityStatus.NO_MODEL,
                listOf("A complete approved model bundle is not installed.")
            )
        }

        val reasons = buildList {
            if (descriptor.modelId != manifest.modelId) add("modelId mismatch")
            if (descriptor.modelVersion != manifest.modelVersion) add("modelVersion mismatch")
            if (descriptor.inputContractVersion != manifest.inputContractVersion) {
                add("descriptor input contract mismatch")
            }
            if (manifest.inputContractVersion != matrix.inputContractVersion) {
                add("unsupported input contract")
            }
            if (manifest.taxonomyVersion != matrix.taxonomyVersion) {
                add("unsupported taxonomy")
            }
            if (manifest.calibrationVersion != matrix.calibrationVersion) {
                add("unsupported calibration")
            }
            if (manifest.riskRulesVersion != matrix.riskRulesVersion) {
                add("unsupported risk rules")
            }
        }
        return if (reasons.isEmpty()) {
            CompatibilityResult(CompatibilityStatus.COMPATIBLE)
        } else {
            CompatibilityResult(CompatibilityStatus.INCOMPATIBLE, reasons)
        }
    }
}
