package com.mushroom.detector.quality

import com.mushroom.detector.capture.CapturedObservation
import com.mushroom.detector.capture.CaptureViewType
import com.mushroom.detector.capture.ObservationSession
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class QualityAndViewValidatorTest {
    @Test
    fun requestsEveryMissingIndependentView() {
        val result = QualityAndViewValidator().validate(ObservationSession())

        assertTrue(result is QualityResult.MissingViews)
        assertEquals(
            CaptureViewType.entries.toSet(),
            (result as QualityResult.MissingViews).views
        )
    }

    @Test
    fun acceptsCompleteObservationSession() {
        val captures = CaptureViewType.entries.associateWith { view ->
            CapturedObservation(view, "file:///${view.name}.jpg", 1)
        }
        val result = QualityAndViewValidator().validate(
            ObservationSession(captures = captures)
        )

        assertEquals(QualityResult.Accepted, result)
    }
}
