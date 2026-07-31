package com.mushroom.detector.artifacts

import com.mushroom.detector.ResultStatus
import com.mushroom.detector.capture.CaptureViewType
import com.mushroom.detector.capture.ObservationSession
import com.mushroom.detector.inference.ModelDescriptor
import java.io.File
import java.nio.file.Files
import java.nio.file.StandardCopyOption
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class KnowledgePackArchitectureTest {
    private val matrix = CompatibilityMatrix(
        "input-v1",
        "1.0.0",
        "synthetic-calibration-v1",
        "synthetic-risk-rules-v1"
    )
    private val model = ModelDescriptor(
        "synthetic-model",
        "1",
        "input-v1",
        "0".repeat(64)
    )
    private val index = SearchIndexDescriptor(
        "region_synthetic",
        CaptureViewType.CAP_TOP,
        "synthetic-embedding-model",
        4,
        "exact-json-v1",
        SearchIndexFormat.EXACT_BASELINE,
        "1.0.0",
        "COSINE_DISTANCE_INTERNAL_ONLY",
        1,
        4,
        SearchIndexLoadingMode.SYNTHETIC_IN_MEMORY_ONLY
    )

    private fun manifest(productionApproved: Boolean = false) = KnowledgePackManifest(
        packFormatVersion = "1.0.0",
        packId = "pack_synthetic",
        packVersion = "1.0.0-synthetic",
        createdAt = "2026-07-31T00:00:00Z",
        regionIds = setOf("region_synthetic"),
        minimumAppVersion = "1.0.0",
        maximumAppVersion = "1.0.0",
        modelContractVersion = "model-contract-v1",
        modelId = "synthetic-model",
        modelPath = "model/model.bin",
        modelSha256 = "0".repeat(64),
        embeddingModelId = "synthetic-embedding-model",
        embeddingModelPath = "embeddings/model.bin",
        embeddingModelSha256 = "1".repeat(64),
        embeddingDimension = 4,
        embeddingDtype = "float32",
        taxonomyVersion = "1.0.0",
        taxonomyPath = "taxonomy/taxonomy.json",
        taxonomySha256 = "2".repeat(64),
        confusionGroupsVersion = "1.0.0",
        confusionGroupsPath = "taxonomy/confusion-groups.json",
        confusionGroupsSha256 = "3".repeat(64),
        openSetVersion = "synthetic-open-set-v1",
        openSetPath = "open-set/rejection.json",
        openSetSha256 = "4".repeat(64),
        calibrationVersion = "synthetic-calibration-v1",
        calibrationPath = "calibration/calibration.json",
        calibrationSha256 = "5".repeat(64),
        riskRulesVersion = "synthetic-risk-rules-v1",
        riskRulesPath = "risk-rules/rules.json",
        riskRulesSha256 = "6".repeat(64),
        referenceObservationCount = 3,
        referenceImageCount = 0,
        vectorSearchEngine = SearchIndexFormat.EXACT_BASELINE,
        vectorSearchEngineVersion = "1.0.0",
        searchIndexFormatVersion = "exact-json-v1",
        indexAlgorithm = "EXACT",
        indexMetric = "COSINE_DISTANCE_INTERNAL_ONLY",
        indexQuantization = "NONE",
        indexShardCount = 1,
        indexVectorCount = 4,
        indexPath = "search-index/index.bin",
        indexBuildConfigPath = "search-index/build-config.json",
        indexBuildConfigSha256 = "7".repeat(64),
        indexBenchmarkReportPath = "search-index/benchmark-report.json",
        indexBenchmarkReportSha256 = "8".repeat(64),
        exactRerankEnabled = true,
        exactRerankEmbeddingDtype = "float32",
        declaredArchiveSizeBytes = 100,
        declaredUnpackedSizeBytes = 100,
        fileCount = 1,
        licenseManifestPath = "licenses/attribution.json",
        licenseManifestSha256 = "9".repeat(64),
        fileManifestPath = "file-manifest.json",
        fileManifestSha256 = "a".repeat(64),
        checksumsPath = "checksums.sha256",
        checksumsSha256 = "b".repeat(64),
        signatureAlgorithm = "ED25519",
        signingKeyId = "test-key-contract-only",
        signatureRequired = productionApproved,
        productionApproved = productionApproved
    )

    @Test
    fun noActivePackCreatesUnavailableRuntime() {
        val gate = KnowledgePackCompatibilityGate(ArtifactCompatibilityGate(matrix))
        val runtime = MandatoryKnowledgePackRuntimeFactory(
            NoKnowledgePackRepository(),
            gate,
            { null },
            { null },
            { null }
        ).create()

        assertFalse(runtime.available)
        assertEquals(
            ResultStatus.RECOGNITION_UNAVAILABLE,
            runtime.inferenceEngine.infer(ObservationSession()).status
        )
    }

    @Test
    fun syntheticUnapprovedPackIsRejectedByCompatibilityGate() {
        val root = Files.createTempDirectory("pack-contract").toFile()
        try {
            val descriptor = KnowledgePackDescriptor(
                "pack_synthetic",
                "1.0.0-synthetic",
                root,
                KnowledgePackState.ACTIVE,
                signatureTrusted = false
            )
            val result = KnowledgePackCompatibilityGate(
                ArtifactCompatibilityGate(matrix)
            ).validate(model, manifest(), descriptor, index)

            assertFalse(result.compatible)
            assertTrue(result.reasons.contains("pack is not production approved"))
            assertTrue(result.reasons.contains("pack signature is untrusted"))
        } finally {
            root.deleteRecursively()
        }
    }

    @Test
    fun mismatchMatrixRejectsEveryVersionLockedComponent() {
        val root = Files.createTempDirectory("pack-contract").toFile()
        try {
            val descriptor = KnowledgePackDescriptor(
                "pack_synthetic", "1.0.0", root,
                KnowledgePackState.ACTIVE, signatureTrusted = true
            )
            val base = manifest(productionApproved = true)
            val gate = KnowledgePackCompatibilityGate(ArtifactCompatibilityGate(matrix))
            val mutations = listOf(
                base.copy(modelId = "other") to "model mismatch",
                base.copy(embeddingModelId = "other") to "embedding model mismatch",
                base.copy(embeddingDimension = 8) to "embedding dimension mismatch",
                base.copy(taxonomyVersion = "other") to "taxonomy mismatch",
                base.copy(confusionGroupsVersion = "other") to "confusion groups mismatch",
                base.copy(openSetVersion = "other") to "open-set mismatch",
                base.copy(calibrationVersion = "other") to "calibration mismatch",
                base.copy(riskRulesVersion = "other") to "risk rules mismatch",
                base.copy(vectorSearchEngineVersion = "other") to "incompatible engine version"
            )

            mutations.forEach { (changed, reason) ->
                assertTrue(gate.validate(model, changed, descriptor, index).reasons.contains(reason))
            }
        } finally {
            root.deleteRecursively()
        }
    }

    @Test
    fun failedImportKeepsPreviousActivePack() {
        val root = Files.createTempDirectory("pack-storage").toFile()
        try {
            val storage = FileKnowledgePackStorage(root) { Long.MAX_VALUE }
            val firstStaging = storage.createStaging("first")
            File(firstStaging, "marker").writeText("first")
            val first = KnowledgePackDescriptor(
                "pack_first", "1.0.0", firstStaging,
                KnowledgePackState.READY, signatureTrusted = true
            )
            assertTrue(storage.activateAtomically(firstStaging, first))
            val previous = storage.activePack()

            val nextStaging = storage.createStaging("next")
            val installer = KnowledgePackInstaller(
                storage,
                KnowledgePackIntegrityVerifier { _, _ -> true },
                RejectingKnowledgePackSignatureVerifier(),
                KnowledgePackCompatibilityGate(ArtifactCompatibilityGate(matrix)),
                runtimeProbe = { true }
            )
            val result = installer.installVerifiedStaging(
                KnowledgePackSelection("content://synthetic", true),
                nextStaging,
                first.copy(packId = "pack_next", rootDirectory = nextStaging),
                manifest(productionApproved = false),
                model,
                index
            )

            assertEquals(KnowledgePackState.UNTRUSTED, result.state)
            assertEquals(previous?.packId, storage.activePack()?.packId)
            assertNotNull(storage.activePack())
        } finally {
            root.deleteRecursively()
        }
    }

    @Test
    fun interruptedStagingIsCleanedWithoutDeletingActivePack() {
        val root = Files.createTempDirectory("pack-storage").toFile()
        try {
            val storage = FileKnowledgePackStorage(root) { Long.MAX_VALUE }
            val staging = storage.createStaging("interrupted")
            File(staging, "partial").writeText("partial")

            storage.cleanupInterruptedStaging()

            assertFalse(staging.exists())
            assertNull(storage.activePack())
        } finally {
            root.deleteRecursively()
        }
    }

    @Test
    fun insufficientSpaceDoesNotTouchPreviousActivePack() {
        val active = KnowledgePackDescriptor(
            "pack_previous", "1.0.0", File("active"),
            KnowledgePackState.ACTIVE, signatureTrusted = true
        )
        var stagingDiscarded = false
        val storage = object : KnowledgePackStorage {
            override fun activePack() = active
            override fun availableBytes() = 0L
            override fun createStaging(packId: String) = File(packId)
            override fun discardStaging(stagingDirectory: File) {
                stagingDiscarded = true
            }
            override fun activateAtomically(
                stagingDirectory: File,
                descriptor: KnowledgePackDescriptor
            ) = false
            override fun cleanupInterruptedStaging() = Unit
        }
        val installer = KnowledgePackInstaller(
            storage,
            KnowledgePackIntegrityVerifier { _, _ -> true },
            RejectingKnowledgePackSignatureVerifier(),
            KnowledgePackCompatibilityGate(ArtifactCompatibilityGate(matrix)),
            runtimeProbe = { true }
        )

        val result = installer.installVerifiedStaging(
            KnowledgePackSelection("content://synthetic", true),
            File("staging"),
            active.copy(packId = "pack_next"),
            manifest(productionApproved = true),
            model,
            index
        )

        assertEquals(KnowledgePackState.PREFLIGHT_FAILED, result.state)
        assertEquals("pack_previous", storage.activePack()?.packId)
        assertTrue(stagingDiscarded)
    }

    @Test
    fun storageAccessFrameworkContractUsesOpenDocumentWithoutBroadPermissions() {
        assertEquals(
            "android.intent.action.OPEN_DOCUMENT",
            KnowledgePackDocumentContract.ACTION_OPEN_DOCUMENT
        )
        assertEquals(".gribpack", KnowledgePackDocumentContract.FILE_EXTENSION)
    }

    @Test
    fun kotlinManifestFieldsMatchJsonSchemaAndRejectUnknownProperty() {
        val schema = sequenceOf(
            File("../../data/reference-pack/schema/manifest.schema.json"),
            File("../data/reference-pack/schema/manifest.schema.json"),
            File("data/reference-pack/schema/manifest.schema.json")
        ).first { it.isFile }.readLines()
        val schemaFields = schema.mapNotNull { line ->
            Regex("""^    "([a-z0-9_]+)":""").find(line)?.groupValues?.get(1)
        }.toSet()

        assertEquals(schemaFields, KnowledgePackManifestContract.jsonFields)
        assertEquals(
            listOf("unknown field: bypass"),
            KnowledgePackManifestContract.validateRawFields(
                KnowledgePackManifestContract.jsonFields + "bypass"
            )
        )
    }

    @Test
    fun revokedSafPermissionAndMissingSourceFailBeforeVerification() {
        val active = KnowledgePackDescriptor(
            "pack_previous", "1.0.0", File("active"),
            KnowledgePackState.ACTIVE, signatureTrusted = true
        )
        var integrityCalls = 0
        val storage = object : KnowledgePackStorage {
            override fun activePack() = active
            override fun availableBytes() = Long.MAX_VALUE
            override fun createStaging(packId: String) = File(packId)
            override fun discardStaging(stagingDirectory: File) = Unit
            override fun activateAtomically(
                stagingDirectory: File,
                descriptor: KnowledgePackDescriptor
            ) = false
            override fun cleanupInterruptedStaging() = Unit
        }
        val installer = KnowledgePackInstaller(
            storage,
            KnowledgePackIntegrityVerifier { _, _ -> integrityCalls++; true },
            RejectingKnowledgePackSignatureVerifier(),
            KnowledgePackCompatibilityGate(ArtifactCompatibilityGate(matrix)),
            runtimeProbe = { true }
        )

        val revoked = installer.installVerifiedStaging(
            KnowledgePackSelection("content://pack", false),
            File("staging"), active, manifest(true), model, index
        )
        val missing = installer.installVerifiedStaging(
            KnowledgePackSelection("content://pack", true, sourceReadable = false),
            File("staging"), active, manifest(true), model, index
        )

        assertEquals(KnowledgePackState.PREFLIGHT_FAILED, revoked.state)
        assertEquals(KnowledgePackState.PREFLIGHT_FAILED, missing.state)
        assertEquals(0, integrityCalls)
    }

    @Test
    fun importSizeCalculationRejectsLongOverflowAndIncludesRollbackMargin() {
        assertNull(
            FileKnowledgePackStorage.requiredImportFreeBytes(
                manifest().copy(
                    declaredArchiveSizeBytes = Long.MAX_VALUE,
                    declaredUnpackedSizeBytes = 1
                )
            )
        )
        assertTrue(
            FileKnowledgePackStorage.requiredImportFreeBytes(manifest())!! >
                manifest().declaredArchiveSizeBytes + manifest().declaredUnpackedSizeBytes
        )
    }

    @Test
    fun restartCleansOrphanStagingAndLoadsPersistedActivePointer() {
        val root = Files.createTempDirectory("pack-restart").toFile()
        try {
            var storage = FileKnowledgePackStorage(root) { Long.MAX_VALUE }
            val activeStaging = storage.createStaging("active")
            File(activeStaging, "marker").writeText("active")
            val descriptor = KnowledgePackDescriptor(
                "pack_active", "1.0.0", activeStaging,
                KnowledgePackState.READY, signatureTrusted = true
            )
            assertTrue(storage.activateAtomically(activeStaging, descriptor))
            val orphan = storage.createStaging("orphan")
            File(orphan, "partial").writeText("partial")

            storage = FileKnowledgePackStorage(root) { Long.MAX_VALUE }

            assertEquals("pack_active", storage.activePack()?.packId)
            assertTrue(storage.activePack()?.readOnly == true)
            assertFalse(orphan.exists())
        } finally {
            root.walkBottomUp().forEach { it.setWritable(true, false) }
            root.deleteRecursively()
        }
    }

    @Test
    fun pendingActivationCrashRestoresPreviousPack() {
        val root = Files.createTempDirectory("pack-crash-recovery").toFile()
        try {
            val storage = FileKnowledgePackStorage(root) { Long.MAX_VALUE }
            val staging = storage.createStaging("previous")
            File(staging, "marker").writeText("previous")
            val previous = KnowledgePackDescriptor(
                "pack_previous", "1.0.0", staging,
                KnowledgePackState.READY, signatureTrusted = true
            )
            assertTrue(storage.activateAtomically(staging, previous))
            File(root, "active").walkBottomUp().forEach { it.setWritable(true, false) }
            Files.move(
                File(root, "active").toPath(),
                File(root, "rollback").toPath(),
                StandardCopyOption.ATOMIC_MOVE
            )
            File(root, "active").also { it.mkdirs() }
            File(root, "active/new-marker").writeText("uncommitted")
            File(root, "activation.pending").writeText("pack_new\n1.0.0\n")

            val recovered = FileKnowledgePackStorage(root) { Long.MAX_VALUE }

            assertEquals("pack_previous", recovered.activePack()?.packId)
            assertEquals("previous", File(root, "active/marker").readText())
            assertFalse(File(root, "active/new-marker").exists())
        } finally {
            root.walkBottomUp().forEach { it.setWritable(true, false) }
            root.deleteRecursively()
        }
    }

    @Test
    fun stagingIntegrityIsRecheckedAfterRuntimeSmokeOpen() {
        val previous = KnowledgePackDescriptor(
            "pack_previous", "1.0.0", File("active"),
            KnowledgePackState.ACTIVE, signatureTrusted = true
        )
        var checks = 0
        var activated = false
        val storage = object : KnowledgePackStorage {
            override fun activePack() = previous
            override fun availableBytes() = Long.MAX_VALUE
            override fun createStaging(packId: String) = File(packId)
            override fun discardStaging(stagingDirectory: File) = Unit
            override fun activateAtomically(
                stagingDirectory: File,
                descriptor: KnowledgePackDescriptor
            ): Boolean { activated = true; return true }
            override fun cleanupInterruptedStaging() = Unit
        }
        val productionMatrix = matrix.copy(
            vectorSearchEngine = SearchIndexFormat.USEARCH_HNSW,
            vectorSearchEngineVersion = "contract-v1",
            searchIndexFormatVersion = "usearch-v1",
            indexAlgorithm = "HNSW",
            indexMetric = "COSINE",
            indexQuantization = "FLOAT16"
        )
        val productionManifest = manifest(true).copy(
            vectorSearchEngine = SearchIndexFormat.USEARCH_HNSW,
            vectorSearchEngineVersion = "contract-v1",
            searchIndexFormatVersion = "usearch-v1",
            indexAlgorithm = "HNSW",
            indexMetric = "COSINE",
            indexQuantization = "FLOAT16"
        )
        val productionIndex = index.copy(
            engine = SearchIndexFormat.USEARCH_HNSW,
            engineVersion = "contract-v1",
            indexFormatVersion = "usearch-v1",
            metric = "COSINE",
            loadingMode = SearchIndexLoadingMode.MEMORY_MAPPED
        )
        val installer = KnowledgePackInstaller(
            storage,
            KnowledgePackIntegrityVerifier { _, _ -> ++checks == 1 },
            KnowledgePackSignatureVerifier { _, _ -> true },
            KnowledgePackCompatibilityGate(ArtifactCompatibilityGate(productionMatrix)),
            runtimeProbe = { true }
        )

        val result = installer.installVerifiedStaging(
            KnowledgePackSelection("content://pack", true),
            File("staging"),
            previous.copy(packId = "pack_synthetic", packVersion = "1.0.0-synthetic"),
            productionManifest,
            model,
            productionIndex
        )

        assertEquals(KnowledgePackState.CORRUPTED, result.state)
        assertFalse(activated)
        assertEquals("pack_previous", storage.activePack()?.packId)
    }

    @Test
    fun androidManifestHasNoForbiddenPermissionsAndPackRuntimeHasNoNetworkCode() {
        fun projectFile(path: String): File = sequenceOf(File(path), File("../$path"))
            .first { it.isFile }
        val androidManifest = projectFile("app/src/main/AndroidManifest.xml").readText()
        val forbidden = listOf(
            "INTERNET", "MANAGE_EXTERNAL_STORAGE", "READ_EXTERNAL_STORAGE",
            "WRITE_EXTERNAL_STORAGE", "ACCESS_FINE_LOCATION", "ACCESS_COARSE_LOCATION"
        )
        val runtimeSource = listOf(
            "KnowledgePackContracts.kt", "KnowledgePackStorage.kt", "VectorSearch.kt"
        ).joinToString("\n") { name ->
            projectFile(
                "app/src/main/java/com/mushroom/detector/artifacts/$name"
            ).readText()
        }

        forbidden.forEach { assertFalse(androidManifest.contains(it)) }
        listOf("java.net.URL", "HttpURLConnection", "okhttp", "retrofit")
            .forEach { assertFalse(runtimeSource.contains(it)) }
        assertFalse(runtimeSource.contains("capture.CaptureFileStore"))
    }
}
