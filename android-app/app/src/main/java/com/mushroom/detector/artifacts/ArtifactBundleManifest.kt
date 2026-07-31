package com.mushroom.detector.artifacts

data class ArtifactBundleManifest(
    val modelId: String,
    val modelVersion: String,
    val inputContractVersion: String,
    val taxonomyVersion: String,
    val calibrationVersion: String,
    val riskRulesVersion: String,
    val packFormatVersion: String = "",
    val packId: String = "",
    val packVersion: String = "",
    val modelContractVersion: String = "",
    val modelSha256: String = "",
    val embeddingModelId: String = "",
    val embeddingDimension: Int = 0,
    val confusionGroupsVersion: String = "",
    val openSetVersion: String = "",
    val vectorSearchEngine: SearchIndexFormat? = null,
    val vectorSearchEngineVersion: String = "",
    val searchIndexFormatVersion: String = "",
    val productionApproved: Boolean = false,
    val signatureTrusted: Boolean = false,
    val active: Boolean = false
)
