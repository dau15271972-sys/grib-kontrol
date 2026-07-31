package com.mushroom.detector.inference

import com.mushroom.detector.MushroomApiResponse
import com.mushroom.detector.capture.ObservationSession

interface InferenceEngine {
    val descriptor: ModelDescriptor?

    fun infer(session: ObservationSession): MushroomApiResponse
}
