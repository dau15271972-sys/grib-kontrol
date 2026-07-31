package com.mushroom.detector.inference

data class ModelDescriptor(
    val modelId: String,
    val modelVersion: String,
    val inputContractVersion: String,
    val sha256: String
)
