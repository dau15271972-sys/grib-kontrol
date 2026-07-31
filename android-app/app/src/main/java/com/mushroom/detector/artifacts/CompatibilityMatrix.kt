package com.mushroom.detector.artifacts

data class CompatibilityMatrix(
    val inputContractVersion: String,
    val taxonomyVersion: String,
    val calibrationVersion: String,
    val riskRulesVersion: String
)
