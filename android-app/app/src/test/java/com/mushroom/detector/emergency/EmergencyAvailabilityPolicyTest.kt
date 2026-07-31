package com.mushroom.detector.emergency

import com.mushroom.detector.ResultStatus
import org.junit.Assert.assertTrue
import org.junit.Test

class EmergencyAvailabilityPolicyTest {
    @Test
    fun availableWithoutModel() {
        assertTrue(
            EmergencyAvailabilityPolicy.isAvailable(
                ResultStatus.RECOGNITION_UNAVAILABLE
            )
        )
    }

    @Test
    fun availableAfterTechnicalFailure() {
        assertTrue(
            EmergencyAvailabilityPolicy.isAvailable(ResultStatus.TECHNICAL_FAILURE)
        )
    }
}
