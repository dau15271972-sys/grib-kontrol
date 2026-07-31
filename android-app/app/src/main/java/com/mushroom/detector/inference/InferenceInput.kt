package com.mushroom.detector.inference

import com.mushroom.detector.capture.CaptureViewType

data class BoundingBox(
    val left: Int,
    val top: Int,
    val right: Int,
    val bottom: Int
)

data class ImageCrop(
    val source: String,
    val boundingBox: BoundingBox
)

data class PixelMask(
    val width: Int,
    val height: Int,
    val bytes: ByteArray
)

data class InferenceInput(
    val viewType: CaptureViewType,
    val source: String,
    val boundingBox: BoundingBox?,
    val crop: ImageCrop?,
    val mask: PixelMask?
)
