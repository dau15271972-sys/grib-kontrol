package com.mushroom.detector.capture

import java.util.UUID

data class CapturedObservation(
    val viewType: CaptureViewType,
    val uri: String,
    val capturedAt: Long
)

data class ObservationSession(
    val id: String = UUID.randomUUID().toString(),
    val captures: Map<CaptureViewType, CapturedObservation> = emptyMap()
) {
    fun withCapture(capture: CapturedObservation): ObservationSession =
        copy(captures = captures + (capture.viewType to capture))

    fun missingViews(
        required: Set<CaptureViewType> = requiredCaptureViews
    ): Set<CaptureViewType> = required - captures.keys
}
