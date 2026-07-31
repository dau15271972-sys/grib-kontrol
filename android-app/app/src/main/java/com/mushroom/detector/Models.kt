package com.mushroom.detector

enum class ResultStatus {
    RECOGNITION_UNAVAILABLE,
    TECHNICAL_FAILURE,
    HIGH_RISK,
    NEED_MORE_PHOTOS,
    UNKNOWN,
    POSSIBLE_TAXON
}

data class MushroomApiResponse(
    val status: ResultStatus,
    val title: String,
    val message: String,
    val safetyBanner: String
)
