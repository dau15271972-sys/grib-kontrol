package com.mushroom.detector.emergency

object EmergencyContent {
    const val REVIEW_STATUS = "UNAPPROVED_MEDICAL_PLACEHOLDER"

    // SAFETY: this copy is deliberately marked as unapproved and cannot ship in production.
    const val REVIEW_NOTICE =
        "Неутверждённый медицинский текст-заглушка. Production-релиз заблокирован."
    const val PLACEHOLDER_GUIDANCE =
        "Если после контакта с грибами человеку стало плохо, обратитесь в местную экстренную службу. " +
            "Не ждите результата приложения и следуйте указаниям специалистов."

    // SAFETY: regional contacts require separate human approval; none is invented here.
    val emergencyNumber: String? = null
}
