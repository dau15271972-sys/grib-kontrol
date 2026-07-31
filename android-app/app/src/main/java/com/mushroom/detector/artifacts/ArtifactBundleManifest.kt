package com.mushroom.detector.artifacts

data class ArtifactBundleManifest(
    val modelId: String,
    val modelVersion: String,
    val inputContractVersion: String,
    val taxonomyVersion: String,
    val calibrationVersion: String,
    val riskRulesVersion: String
)
