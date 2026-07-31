package com.mushroom.detector.capture

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class ObservationSessionTest {
    @Test
    fun transformedCopiesCannotSatisfyIndependentViews() {
        val source = "file:///capture.jpg"
        var session = ObservationSession()
        session = session.withCapture(
            CapturedObservation(CaptureViewType.CAP_TOP, source, capturedAt = 1)
        )

        assertEquals(setOf(CaptureViewType.CAP_TOP), session.captures.keys)
        assertTrue(session.missingViews().contains(CaptureViewType.UNDERSIDE))
        assertTrue(session.missingViews().contains(CaptureViewType.STEM_BASE))
        assertTrue(session.missingViews().contains(CaptureViewType.SIDE))
    }
}
