package com.mushroom.detector.quality

import com.mushroom.detector.capture.ObservationSession
import com.mushroom.detector.capture.requiredCaptureViews

class QualityAndViewValidator {
    fun validate(session: ObservationSession): QualityResult {
        val missing = session.missingViews(requiredCaptureViews)
        return if (missing.isEmpty()) {
            QualityResult.Accepted
        } else {
            QualityResult.MissingViews(missing)
        }
    }
}
