package com.mushroom.detector.inference

import com.mushroom.detector.ResultStatus
import com.mushroom.detector.capture.ObservationSession
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Test

class NoModelInferenceEngineTest {
    @Test
    fun returnsRecognitionUnavailableWithoutGuessing() {
        val result = NoModelInferenceEngine().infer(ObservationSession())

        assertEquals(ResultStatus.RECOGNITION_UNAVAILABLE, result.status)
        assertFalse(result.message.contains("%"))
    }
}
