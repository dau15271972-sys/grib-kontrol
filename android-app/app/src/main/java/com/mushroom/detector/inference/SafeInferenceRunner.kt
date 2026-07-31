package com.mushroom.detector.inference

import com.mushroom.detector.MushroomApiResponse
import com.mushroom.detector.ResultStatus
import com.mushroom.detector.artifacts.ArtifactBundleManifest
import com.mushroom.detector.artifacts.ArtifactCompatibilityGate
import com.mushroom.detector.artifacts.CompatibilityStatus
import com.mushroom.detector.capture.ObservationSession

class SafeInferenceRunner(
    private val engine: InferenceEngine,
    private val compatibilityGate: ArtifactCompatibilityGate? = null,
    private val manifest: ArtifactBundleManifest? = null
) {
    // SAFETY: every registered model must pass the exact artifact contract.
    fun run(session: ObservationSession): MushroomApiResponse {
        val descriptor = engine.descriptor ?: return NoModelInferenceEngine().infer(session)
        val gate = compatibilityGate ?: return technicalFailure()
        val bundleManifest = manifest ?: return technicalFailure()
        when (gate.validate(descriptor, bundleManifest).status) {
            CompatibilityStatus.NO_MODEL -> return NoModelInferenceEngine().infer(session)
            CompatibilityStatus.INCOMPATIBLE -> return technicalFailure()
            CompatibilityStatus.COMPATIBLE -> Unit
        }

        return try {
            engine.infer(session)
        } catch (_: Exception) {
            technicalFailure()
        }
    }

    private fun technicalFailure() = MushroomApiResponse(
        status = ResultStatus.TECHNICAL_FAILURE,
        title = "Обработка завершилась не полностью",
        message = "Безопасно исключить опасный вариант невозможно.",
        safetyBanner = (
            "Не принимайте решение об употреблении гриба по результату приложения."
            )
    )
}
