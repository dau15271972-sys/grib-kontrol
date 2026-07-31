package com.mushroom.detector.artifacts

import com.mushroom.detector.inference.ModelDescriptor
import java.time.Instant

enum class CompatibilityStatus {
    COMPATIBLE,
    NO_MODEL,
    INCOMPATIBLE
}

data class CompatibilityResult(
    val status: CompatibilityStatus,
    val reasons: List<String> = emptyList()
)

class ArtifactCompatibilityGate(
    private val matrix: CompatibilityMatrix
) {
    // SAFETY: future engines may run only after this exact contract check succeeds.
    fun validate(
        descriptor: ModelDescriptor?,
        manifest: ArtifactBundleManifest?
    ): CompatibilityResult {
        if (descriptor == null || manifest == null) {
            return CompatibilityResult(
                CompatibilityStatus.NO_MODEL,
                listOf("A complete approved model bundle is not installed.")
            )
        }

        val reasons = buildList {
            if (descriptor.modelId != manifest.modelId) add("modelId mismatch")
            if (descriptor.modelVersion != manifest.modelVersion) add("modelVersion mismatch")
            if (descriptor.inputContractVersion != manifest.inputContractVersion) {
                add("descriptor input contract mismatch")
            }
            if (manifest.inputContractVersion != matrix.inputContractVersion) {
                add("unsupported input contract")
            }
            if (manifest.taxonomyVersion != matrix.taxonomyVersion) {
                add("unsupported taxonomy")
            }
            if (manifest.calibrationVersion != matrix.calibrationVersion) {
                add("unsupported calibration")
            }
            if (manifest.riskRulesVersion != matrix.riskRulesVersion) {
                add("unsupported risk rules")
            }
            if (manifest.packFormatVersion != matrix.packFormatVersion) {
                add("unsupported pack format")
            }
            if (manifest.modelContractVersion != matrix.modelContractVersion) {
                add("unsupported model contract")
            }
            if (descriptor.sha256 != manifest.modelSha256) add("model SHA-256 mismatch")
            if (manifest.embeddingModelId != matrix.embeddingModelId) {
                add("unsupported embedding model")
            }
            if (manifest.embeddingDimension != matrix.embeddingDimension) {
                add("unsupported embedding dimension")
            }
            if (manifest.confusionGroupsVersion != matrix.confusionGroupsVersion) {
                add("unsupported confusion groups")
            }
            if (manifest.openSetVersion != matrix.openSetVersion) {
                add("unsupported open-set contract")
            }
            if (manifest.vectorSearchEngine != matrix.vectorSearchEngine) {
                add("unsupported vector search engine")
            }
            if (manifest.vectorSearchEngine == SearchIndexFormat.EXACT_BASELINE) {
                add("synthetic exact search is forbidden in production")
            }
            if (manifest.vectorSearchEngineVersion != matrix.vectorSearchEngineVersion) {
                add("unsupported vector search engine version")
            }
            if (manifest.searchIndexFormatVersion != matrix.searchIndexFormatVersion) {
                add("unsupported search index format")
            }
            if (!manifest.productionApproved) add("pack is not production approved")
            if (!manifest.signatureTrusted) add("pack signature is untrusted")
            if (!manifest.active) add("pack is not active")
        }
        return if (reasons.isEmpty()) {
            CompatibilityResult(CompatibilityStatus.COMPATIBLE)
        } else {
            CompatibilityResult(CompatibilityStatus.INCOMPATIBLE, reasons)
        }
    }

    // SAFETY: Mandatory pack validation extends this single compatibility boundary.
    fun validateKnowledgePack(
        descriptor: ModelDescriptor?,
        manifest: KnowledgePackManifest?,
        packDescriptor: KnowledgePackDescriptor?,
        indexDescriptor: SearchIndexDescriptor?
    ): KnowledgePackCompatibilityResult {
        if (
            descriptor == null ||
            manifest == null ||
            packDescriptor == null ||
            indexDescriptor == null
        ) {
            return KnowledgePackCompatibilityResult(
                false,
                listOf("A complete active knowledge pack is not installed.")
            )
        }
        val reasons = buildList {
            if (packDescriptor.packId != manifest.packId) add("pack id mismatch")
            if (packDescriptor.packVersion != manifest.packVersion) add("pack version mismatch")
            if (!isSemver(manifest.packVersion)) add("invalid pack version")
            if (runCatching { Instant.parse(manifest.createdAt) }.isFailure) {
                add("invalid creation timestamp")
            }
            if (manifest.regionIds.isEmpty() || manifest.regionIds.any { it.isBlank() }) {
                add("invalid region set")
            }
            if (manifest.packFormatVersion != matrix.packFormatVersion) {
                add("unsupported pack format")
            }
            if (!appVersionSupported(manifest)) add("app version mismatch")
            if (manifest.modelContractVersion != matrix.modelContractVersion) {
                add("model contract mismatch")
            }
            if (descriptor.modelId != manifest.modelId) add("model mismatch")
            if (descriptor.inputContractVersion != matrix.inputContractVersion) {
                add("model input contract mismatch")
            }
            if (descriptor.sha256 != manifest.modelSha256) add("model SHA-256 mismatch")
            validatePathAndHash(manifest.modelPath, manifest.modelSha256, "model", this)
            if (manifest.embeddingModelId != matrix.embeddingModelId) {
                add("embedding model mismatch")
            }
            validatePathAndHash(
                manifest.embeddingModelPath,
                manifest.embeddingModelSha256,
                "embedding model",
                this
            )
            if (manifest.embeddingDimension != matrix.embeddingDimension) {
                add("embedding dimension mismatch")
            }
            if (manifest.embeddingDtype != matrix.embeddingDtype) add("embedding dtype mismatch")
            if (manifest.taxonomyVersion != matrix.taxonomyVersion) {
                add("taxonomy mismatch")
            }
            validatePathAndHash(
                manifest.taxonomyPath,
                manifest.taxonomySha256,
                "taxonomy",
                this
            )
            if (manifest.confusionGroupsVersion != matrix.confusionGroupsVersion) {
                add("confusion groups mismatch")
            }
            validatePathAndHash(
                manifest.confusionGroupsPath,
                manifest.confusionGroupsSha256,
                "confusion groups",
                this
            )
            if (manifest.openSetVersion != matrix.openSetVersion) add("open-set mismatch")
            validatePathAndHash(manifest.openSetPath, manifest.openSetSha256, "open-set", this)
            if (manifest.calibrationVersion != matrix.calibrationVersion) {
                add("calibration mismatch")
            }
            validatePathAndHash(
                manifest.calibrationPath,
                manifest.calibrationSha256,
                "calibration",
                this
            )
            if (manifest.riskRulesVersion != matrix.riskRulesVersion) {
                add("risk rules mismatch")
            }
            validatePathAndHash(
                manifest.riskRulesPath,
                manifest.riskRulesSha256,
                "risk rules",
                this
            )
            if (manifest.referenceObservationCount < 0L || manifest.referenceImageCount < 0L) {
                add("negative reference count")
            }
            if (manifest.vectorSearchEngine != matrix.vectorSearchEngine) {
                add("vector search engine mismatch")
            }
            if (manifest.vectorSearchEngineVersion != matrix.vectorSearchEngineVersion) {
                add("incompatible engine version")
            }
            if (manifest.searchIndexFormatVersion != matrix.searchIndexFormatVersion) {
                add("search index format mismatch")
            }
            if (manifest.indexAlgorithm != matrix.indexAlgorithm) add("index algorithm mismatch")
            if (manifest.indexMetric != matrix.indexMetric) add("index metric mismatch")
            if (manifest.indexQuantization != matrix.indexQuantization) {
                add("index quantization mismatch")
            }
            if (manifest.indexShardCount <= 0 || manifest.indexVectorCount < 0L) {
                add("invalid index counts")
            }
            validatePathAndHash(
                manifest.indexBuildConfigPath,
                manifest.indexBuildConfigSha256,
                "index build config",
                this
            )
            validatePathAndHash(
                manifest.indexBenchmarkReportPath,
                manifest.indexBenchmarkReportSha256,
                "index benchmark report",
                this
            )
            if (!isSafeRelativePath(manifest.indexPath)) add("invalid index path")
            if (indexDescriptor.engine != manifest.vectorSearchEngine) {
                add("index engine mismatch")
            }
            if (indexDescriptor.engineVersion != manifest.vectorSearchEngineVersion) {
                add("index engine version mismatch")
            }
            if (indexDescriptor.indexFormatVersion != manifest.searchIndexFormatVersion) {
                add("index format version mismatch")
            }
            if (indexDescriptor.embeddingModelId != manifest.embeddingModelId) {
                add("index embedding model mismatch")
            }
            if (indexDescriptor.embeddingDimension != manifest.embeddingDimension) {
                add("index embedding dimension mismatch")
            }
            if (indexDescriptor.regionId !in manifest.regionIds) add("index region mismatch")
            if (indexDescriptor.metric != manifest.indexMetric) add("descriptor metric mismatch")
            if (indexDescriptor.shardCount != manifest.indexShardCount) {
                add("descriptor shard count mismatch")
            }
            if (indexDescriptor.vectorCount != manifest.indexVectorCount) {
                add("descriptor vector count mismatch")
            }
            if (
                manifest.vectorSearchEngine == SearchIndexFormat.EXACT_BASELINE ||
                indexDescriptor.loadingMode == SearchIndexLoadingMode.SYNTHETIC_IN_MEMORY_ONLY
            ) {
                add("synthetic exact search is forbidden in production")
            }
            if (
                manifest.declaredArchiveSizeBytes < 0L ||
                manifest.declaredUnpackedSizeBytes < 0L ||
                manifest.fileCount <= 0
            ) {
                add("invalid declared package size")
            }
            validatePathAndHash(
                manifest.licenseManifestPath,
                manifest.licenseManifestSha256,
                "license manifest",
                this
            )
            if (manifest.fileManifestPath != "file-manifest.json") {
                add("file manifest path mismatch")
            }
            if (!isSha256(manifest.fileManifestSha256)) add("invalid file manifest hash")
            if (manifest.checksumsPath != "checksums.sha256") add("checksums path mismatch")
            if (!isSha256(manifest.checksumsSha256)) add("invalid checksums hash")
            if (!manifest.productionApproved) add("pack is not production approved")
            if (!manifest.signatureRequired) add("production signature is not required")
            if (manifest.signatureAlgorithm != matrix.signatureAlgorithm) {
                add("signature algorithm mismatch")
            }
            if (manifest.signingKeyId.isNullOrBlank()) add("signing key id is missing")
            if (!packDescriptor.signatureTrusted) add("pack signature is untrusted")
            if (packDescriptor.state != KnowledgePackState.ACTIVE) add("pack is not active")
            if (!packDescriptor.readOnly) add("active pack must be read-only")
            if (!manifest.exactRerankEnabled) add("exact reranking is required")
            if (manifest.exactRerankEmbeddingDtype != matrix.exactRerankEmbeddingDtype) {
                add("exact rerank dtype mismatch")
            }
        }
        return KnowledgePackCompatibilityResult(reasons.isEmpty(), reasons.sorted())
    }

    private fun appVersionSupported(manifest: KnowledgePackManifest): Boolean {
        val current = parseSemver(matrix.appVersion) ?: return false
        val minimum = parseSemver(manifest.minimumAppVersion) ?: return false
        val maximum = parseSemver(manifest.maximumAppVersion) ?: return false
        return compareSemver(current, minimum) >= 0 && compareSemver(current, maximum) <= 0
    }

    private fun parseSemver(value: String): List<Int>? {
        if (!Regex("^[0-9]+\\.[0-9]+\\.[0-9]+(?:-[a-z0-9.-]+)?$").matches(value)) {
            return null
        }
        val parts = value.substringBefore('-').split('.')
        if (parts.size != 3) return null
        return parts.map { it.toIntOrNull() ?: return null }
    }

    private fun compareSemver(left: List<Int>, right: List<Int>): Int {
        for (index in 0..2) {
            val comparison = left[index].compareTo(right[index])
            if (comparison != 0) return comparison
        }
        return 0
    }

    private fun isSemver(value: String): Boolean = parseSemver(value) != null

    private fun isSha256(value: String): Boolean = Regex("^[a-f0-9]{64}$").matches(value)

    private fun isSafeRelativePath(value: String): Boolean =
        value.isNotBlank() &&
            !value.startsWith('/') &&
            !value.contains('\\') &&
            !Regex("^[A-Za-z]:").containsMatchIn(value) &&
            value.split('/').none { it.isBlank() || it == "." || it == ".." }

    private fun validatePathAndHash(
        path: String,
        sha256: String,
        label: String,
        reasons: MutableList<String>
    ) {
        if (!isSafeRelativePath(path)) reasons.add("invalid $label path")
        if (!isSha256(sha256)) reasons.add("invalid $label hash")
    }
}
