package com.mushroom.detector

data class MushroomApiResponse(
    val status: String? = null,
    val error: String? = null,
    val title: String? = null,
    val species_id: String? = null,
    val name_ru: String? = null,
    val name_latin: String? = null,
    val edibility: String? = null,
    val danger_level: String? = null,
    val confidence: Double? = null,
    val second_test_passed: Boolean? = null,
    val second_confidence: Double? = null,
    val third_test_passed: Boolean? = null,
    val third_confidence: Double? = null,
    val lookalikes: List<String>? = null,
    val notes: String? = null,
    val recommendation: String? = null,
    val safety_banner: String? = null,
    val risk_level: String? = null,
    val risk_reason: String? = null,
    val warning_text: String? = null
)
