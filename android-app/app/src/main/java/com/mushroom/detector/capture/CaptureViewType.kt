package com.mushroom.detector.capture

enum class CaptureViewType {
    CAP_TOP,
    UNDERSIDE,
    STEM_BASE,
    SIDE
}

val requiredCaptureViews: Set<CaptureViewType> = CaptureViewType.entries.toSet()
