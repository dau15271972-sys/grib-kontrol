package com.mushroom.detector.artifacts

data class CompatibilityMatrix(
    val inputContractVersion: String,
    val taxonomyVersion: String,
    val calibrationVersion: String,
    val riskRulesVersion: String,
    val appVersion: String = "1.0.0",
    val packFormatVersion: String = "1.0.0",
    val modelContractVersion: String = "model-contract-v1",
    val embeddingModelId: String = "synthetic-embedding-model",
    val embeddingDimension: Int = 4,
    val embeddingDtype: String = "float32",
    val confusionGroupsVersion: String = "1.0.0",
    val openSetVersion: String = "synthetic-open-set-v1",
    val vectorSearchEngine: SearchIndexFormat = SearchIndexFormat.EXACT_BASELINE,
    val vectorSearchEngineVersion: String = "1.0.0",
    val searchIndexFormatVersion: String = "exact-json-v1",
    val indexAlgorithm: String = "EXACT",
    val indexMetric: String = "COSINE_DISTANCE_INTERNAL_ONLY",
    val indexQuantization: String = "NONE",
    val exactRerankEmbeddingDtype: String = "float32",
    val signatureAlgorithm: String = "ED25519"
)
