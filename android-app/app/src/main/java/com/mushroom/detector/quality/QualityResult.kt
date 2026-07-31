package com.mushroom.detector.quality

import com.mushroom.detector.capture.CaptureViewType

sealed interface QualityResult {
    data object Accepted : QualityResult

    data class MissingViews(
        val views: Set<CaptureViewType>
    ) : QualityResult
}
