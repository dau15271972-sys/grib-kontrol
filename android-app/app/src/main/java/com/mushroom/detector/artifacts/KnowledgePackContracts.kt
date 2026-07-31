package com.mushroom.detector.artifacts

import com.mushroom.detector.inference.InferenceEngine
import com.mushroom.detector.inference.ModelDescriptor
import com.mushroom.detector.inference.NoModelInferenceEngine
import java.io.File

enum class KnowledgePackState {
    NOT_INSTALLED,
    SELECTED,
    PREFLIGHT_FAILED,
    IMPORTING,
    VERIFYING,
    INCOMPATIBLE,
    UNTRUSTED,
    READY,
    ACTIVE,
    CORRUPTED,
    MISSING,
    REMOVING
}

data class KnowledgePackManifest(
    val packFormatVersion: String,
    val packId: String,
    val packVersion: String,
    val createdAt: String,
    val regionIds: Set<String>,
    val minimumAppVersion: String,
    val maximumAppVersion: String,
    val modelContractVersion: String,
    val modelId: String,
    val modelPath: String,
    val modelSha256: String,
    val embeddingModelId: String,
    val embeddingModelPath: String,
    val embeddingModelSha256: String,
    val embeddingDimension: Int,
    val embeddingDtype: String,
    val taxonomyVersion: String,
    val taxonomyPath: String,
    val taxonomySha256: String,
    val confusionGroupsVersion: String,
    val confusionGroupsPath: String,
    val confusionGroupsSha256: String,
    val openSetVersion: String,
    val openSetPath: String,
    val openSetSha256: String,
    val calibrationVersion: String,
    val calibrationPath: String,
    val calibrationSha256: String,
    val riskRulesVersion: String,
    val riskRulesPath: String,
    val riskRulesSha256: String,
    val referenceObservationCount: Long,
    val referenceImageCount: Long,
    val vectorSearchEngine: SearchIndexFormat,
    val vectorSearchEngineVersion: String,
    val searchIndexFormatVersion: String,
    val indexAlgorithm: String,
    val indexMetric: String,
    val indexQuantization: String,
    val indexShardCount: Int,
    val indexVectorCount: Long,
    val indexPath: String,
    val indexBuildConfigPath: String,
    val indexBuildConfigSha256: String,
    val indexBenchmarkReportPath: String,
    val indexBenchmarkReportSha256: String,
    val exactRerankEnabled: Boolean,
    val exactRerankEmbeddingDtype: String,
    val declaredArchiveSizeBytes: Long,
    val declaredUnpackedSizeBytes: Long,
    val fileCount: Int,
    val licenseManifestPath: String,
    val licenseManifestSha256: String,
    val fileManifestPath: String,
    val fileManifestSha256: String,
    val checksumsPath: String,
    val checksumsSha256: String,
    val signatureAlgorithm: String,
    val signingKeyId: String?,
    val signatureRequired: Boolean,
    val productionApproved: Boolean
)

object KnowledgePackManifestContract {
    val jsonFields: Set<String> = setOf(
        "pack_format_version", "pack_id", "pack_version", "created_at", "region_ids",
        "minimum_app_version", "maximum_app_version", "model_contract_version",
        "model_id", "model_path", "model_sha256", "embedding_model_id",
        "embedding_model_path", "embedding_model_sha256", "embedding_dimension",
        "embedding_dtype", "taxonomy_version", "taxonomy_path", "taxonomy_sha256",
        "confusion_groups_version", "confusion_groups_path", "confusion_groups_sha256",
        "open_set_version", "open_set_path", "open_set_sha256", "calibration_version",
        "calibration_path", "calibration_sha256", "risk_rules_version", "risk_rules_path",
        "risk_rules_sha256", "reference_observation_count", "reference_image_count",
        "declared_archive_size_bytes", "declared_unpacked_size_bytes", "file_count",
        "vector_search_engine", "vector_search_engine_version", "search_index_format_version",
        "index_algorithm", "index_metric", "index_quantization", "index_shard_count",
        "index_vector_count", "index_path", "index_build_config_path",
        "index_build_config_sha256", "index_benchmark_report_path",
        "index_benchmark_report_sha256", "exact_rerank_enabled",
        "exact_rerank_embedding_dtype", "license_manifest_path", "license_manifest_sha256",
        "file_manifest_path", "file_manifest_sha256", "checksums_path", "checksums_sha256",
        "signature_algorithm", "signing_key_id", "signature_required", "production_approved"
    )

    fun validateRawFields(fields: Set<String>): List<String> = buildList {
        (jsonFields - fields).sorted().forEach { add("missing field: $it") }
        (fields - jsonFields).sorted().forEach { add("unknown field: $it") }
    }
}

data class KnowledgePackDescriptor(
    val packId: String,
    val packVersion: String,
    val rootDirectory: File,
    val state: KnowledgePackState,
    val signatureTrusted: Boolean,
    val readOnly: Boolean = true
)

data class KnowledgePackCompatibilityResult(
    val compatible: Boolean,
    val reasons: List<String> = emptyList()
)

class KnowledgePackCompatibilityGate(
    private val artifactGate: ArtifactCompatibilityGate
) {
    // SAFETY: this adapter extends the single ArtifactCompatibilityGate boundary.
    fun validate(
        descriptor: ModelDescriptor?,
        manifest: KnowledgePackManifest?,
        packDescriptor: KnowledgePackDescriptor?,
        indexDescriptor: SearchIndexDescriptor?
    ): KnowledgePackCompatibilityResult = artifactGate.validateKnowledgePack(
        descriptor,
        manifest,
        packDescriptor,
        indexDescriptor
    )
}

fun interface KnowledgePackSignatureVerifier {
    fun verify(manifest: KnowledgePackManifest, stagingDirectory: File): Boolean
}

class RejectingKnowledgePackSignatureVerifier : KnowledgePackSignatureVerifier {
    override fun verify(manifest: KnowledgePackManifest, stagingDirectory: File): Boolean {
        @Suppress("UNUSED_VARIABLE")
        val inputs = manifest to stagingDirectory
        return false
    }
}

interface KnowledgePackRepository {
    fun activePack(): KnowledgePackDescriptor?
}

class NoKnowledgePackRepository : KnowledgePackRepository {
    override fun activePack(): KnowledgePackDescriptor? = null
}

interface KnowledgePackRuntime : AutoCloseable {
    val available: Boolean
    val inferenceEngine: InferenceEngine
    fun open(): Boolean
}

class UnavailableKnowledgePackRuntime : KnowledgePackRuntime {
    override val available: Boolean = false
    override val inferenceEngine: InferenceEngine = NoModelInferenceEngine()

    override fun open(): Boolean = false

    override fun close() = Unit
}

class MandatoryKnowledgePackRuntimeFactory(
    private val repository: KnowledgePackRepository,
    private val compatibilityGate: KnowledgePackCompatibilityGate,
    private val manifestProvider: (KnowledgePackDescriptor) -> KnowledgePackManifest?,
    private val modelDescriptorProvider: (KnowledgePackDescriptor) -> ModelDescriptor?,
    private val indexDescriptorProvider: (KnowledgePackDescriptor) -> SearchIndexDescriptor?,
    private val trustedRuntimeProvider: (KnowledgePackDescriptor) -> KnowledgePackRuntime = {
        UnavailableKnowledgePackRuntime()
    }
) {
    fun create(): KnowledgePackRuntime {
        val pack = repository.activePack() ?: return UnavailableKnowledgePackRuntime()
        if (
            pack.state != KnowledgePackState.ACTIVE ||
            !pack.signatureTrusted ||
            !pack.readOnly
        ) {
            return UnavailableKnowledgePackRuntime()
        }
        val manifest = manifestProvider(pack) ?: return UnavailableKnowledgePackRuntime()
        val compatibility = compatibilityGate.validate(
            modelDescriptorProvider(pack),
            manifest,
            pack,
            indexDescriptorProvider(pack)
        )
        if (!compatibility.compatible) return UnavailableKnowledgePackRuntime()
        val runtime = trustedRuntimeProvider(pack)
        return if (runtime.open() && runtime.available) {
            runtime
        } else {
            runtime.close()
            UnavailableKnowledgePackRuntime()
        }
    }
}
