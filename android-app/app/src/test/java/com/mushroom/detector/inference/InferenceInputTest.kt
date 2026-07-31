package com.mushroom.detector.inference

import com.mushroom.detector.capture.CaptureViewType
import org.junit.Assert.assertNotEquals
import org.junit.Assert.assertNull
import org.junit.Test

class InferenceInputTest {
    @Test
    fun boundingBoxCropAndNullableMaskRemainDistinct() {
        val box = BoundingBox(1, 2, 30, 40)
        val crop = ImageCrop("file:///source.jpg", box)
        val input = InferenceInput(
            viewType = CaptureViewType.SIDE,
            source = crop.source,
            boundingBox = box,
            crop = crop,
            mask = null
        )

        assertNotEquals(input.boundingBox, input.crop)
        assertNull(input.mask)
    }
}
