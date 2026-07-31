package com.mushroom.detector.emergency

import com.mushroom.detector.ResultStatus

object EmergencyAvailabilityPolicy {
    fun isAvailable(status: ResultStatus?): Boolean = true
}
