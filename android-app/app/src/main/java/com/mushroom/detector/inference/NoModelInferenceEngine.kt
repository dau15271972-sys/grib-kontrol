package com.mushroom.detector.inference

import com.mushroom.detector.MushroomApiResponse
import com.mushroom.detector.ResultStatus
import com.mushroom.detector.capture.ObservationSession

class NoModelInferenceEngine : InferenceEngine {
    override val descriptor: ModelDescriptor? = null

    override fun infer(session: ObservationSession): MushroomApiResponse {
        @Suppress("UNUSED_VARIABLE")
        val observationId = session.id
        return MushroomApiResponse(
            status = ResultStatus.RECOGNITION_UNAVAILABLE,
            title = "Распознавание недоступно",
            message = (
                "Активный проверенный автономный пакет знаний не установлен. " +
                    "По фотографиям нельзя надёжно исключить опасный вариант."
                ),
            safetyBanner = (
                "Не принимайте решение об употреблении гриба по результату приложения."
                )
        )
    }
}
