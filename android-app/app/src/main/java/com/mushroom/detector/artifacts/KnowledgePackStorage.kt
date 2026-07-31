package com.mushroom.detector.artifacts

import com.mushroom.detector.inference.ModelDescriptor
import java.io.File
import java.nio.file.AtomicMoveNotSupportedException
import java.nio.file.Files
import java.nio.file.StandardCopyOption

object KnowledgePackDocumentContract {
    const val ACTION_OPEN_DOCUMENT = "android.intent.action.OPEN_DOCUMENT"
    const val MIME_TYPE = "application/octet-stream"
    const val FILE_EXTENSION = ".gribpack"
}

data class KnowledgePackSelection(
    val sourceUri: String,
    val persistedReadPermission: Boolean,
    val sourceReadable: Boolean = true
)

fun interface KnowledgePackIntegrityVerifier {
    fun verify(stagingDirectory: File, manifest: KnowledgePackManifest): Boolean
}

class RejectingKnowledgePackIntegrityVerifier : KnowledgePackIntegrityVerifier {
    override fun verify(stagingDirectory: File, manifest: KnowledgePackManifest): Boolean = false
}

interface KnowledgePackStorage {
    fun activePack(): KnowledgePackDescriptor?
    fun availableBytes(): Long
    fun createStaging(packId: String): File
    fun discardStaging(stagingDirectory: File)
    fun activateAtomically(
        stagingDirectory: File,
        descriptor: KnowledgePackDescriptor
    ): Boolean
    fun cleanupInterruptedStaging()
}

class FileKnowledgePackStorage(
    private val appOwnedRoot: File,
    private val availableBytesProvider: () -> Long
) : KnowledgePackStorage {
    private val activeDirectory = File(appOwnedRoot, "active")
    private val rollbackDirectory = File(appOwnedRoot, "rollback")
    private val stagingRoot = File(appOwnedRoot, "staging")
    private val activePointer = File(appOwnedRoot, "active.pointer")
    private val pendingActivation = File(appOwnedRoot, "activation.pending")
    private var activeDescriptor: KnowledgePackDescriptor? = null

    init {
        recoverInterruptedActivation()
        cleanupInterruptedStaging()
        activeDescriptor = readActivePointer()
    }

    override fun activePack(): KnowledgePackDescriptor? = activeDescriptor

    override fun availableBytes(): Long = availableBytesProvider()

    override fun createStaging(packId: String): File {
        require(packId.matches(Regex("[a-zA-Z0-9_-]+")))
        stagingRoot.mkdirs()
        return Files.createTempDirectory(stagingRoot.toPath(), "$packId-").toFile()
    }

    override fun discardStaging(stagingDirectory: File) {
        if (isOwnedStaging(stagingDirectory)) stagingDirectory.deleteRecursively()
    }

    override fun activateAtomically(
        stagingDirectory: File,
        descriptor: KnowledgePackDescriptor
    ): Boolean {
        if (!isOwnedStaging(stagingDirectory) || !stagingDirectory.isDirectory) return false
        appOwnedRoot.mkdirs()
        val previous = activeDescriptor
        return try {
            deleteOwnedTree(rollbackDirectory)
            writeAtomically(
                pendingActivation,
                descriptor.packId + "\n" + descriptor.packVersion + "\n"
            )
            if (activeDirectory.exists()) {
                setTreeWritable(activeDirectory, true)
                Files.move(
                    activeDirectory.toPath(),
                    rollbackDirectory.toPath(),
                    StandardCopyOption.ATOMIC_MOVE
                )
            }
            Files.move(
                stagingDirectory.toPath(),
                activeDirectory.toPath(),
                StandardCopyOption.ATOMIC_MOVE
            )
            val activated = descriptor.copy(
                rootDirectory = activeDirectory,
                state = KnowledgePackState.ACTIVE,
                readOnly = true
            )
            setTreeWritable(activeDirectory, false)
            writeActivePointer(activated)
            activeDescriptor = activated
            deleteOwnedTree(rollbackDirectory)
            pendingActivation.delete()
            true
        } catch (_: AtomicMoveNotSupportedException) {
            restorePrevious(previous)
            false
        } catch (_: Exception) {
            restorePrevious(previous)
            false
        }
    }

    override fun cleanupInterruptedStaging() {
        stagingRoot.listFiles()?.forEach { candidate ->
            if (isOwnedStaging(candidate)) candidate.deleteRecursively()
        }
    }

    private fun restorePrevious(previous: KnowledgePackDescriptor?) {
        if (rollbackDirectory.exists()) {
            runCatching {
                if (activeDirectory.exists()) {
                    setTreeWritable(activeDirectory, true)
                    deleteOwnedTree(activeDirectory)
                }
                Files.move(
                    rollbackDirectory.toPath(),
                    activeDirectory.toPath(),
                    StandardCopyOption.ATOMIC_MOVE
                )
                setTreeWritable(activeDirectory, false)
            }
        } else if (previous == null && activeDirectory.exists()) {
            setTreeWritable(activeDirectory, true)
            deleteOwnedTree(activeDirectory)
        }
        activeDescriptor = previous
        if (previous == null) activePointer.delete() else writeActivePointer(previous)
        pendingActivation.delete()
    }

    private fun isOwnedStaging(candidate: File): Boolean = runCatching {
        candidate.canonicalFile.parentFile == stagingRoot.canonicalFile
    }.getOrDefault(false)

    private fun recoverInterruptedActivation() {
        if (!pendingActivation.exists()) return
        if (rollbackDirectory.exists()) {
            if (activeDirectory.exists()) {
                setTreeWritable(activeDirectory, true)
                deleteOwnedTree(activeDirectory)
            }
            runCatching {
                Files.move(
                    rollbackDirectory.toPath(),
                    activeDirectory.toPath(),
                    StandardCopyOption.ATOMIC_MOVE
                )
                setTreeWritable(activeDirectory, false)
            }
        } else if (!activePointer.exists() && activeDirectory.exists()) {
            setTreeWritable(activeDirectory, true)
            deleteOwnedTree(activeDirectory)
        }
        pendingActivation.delete()
    }

    private fun readActivePointer(): KnowledgePackDescriptor? {
        if (!activeDirectory.isDirectory || !activePointer.isFile) return null
        val lines = runCatching { activePointer.readLines() }.getOrNull() ?: return null
        if (lines.size != 4 || lines[2] != "trusted" || lines[3] != "readonly") return null
        if (!lines[0].matches(Regex("[a-zA-Z0-9_-]+"))) return null
        return KnowledgePackDescriptor(
            lines[0],
            lines[1],
            activeDirectory,
            KnowledgePackState.ACTIVE,
            signatureTrusted = true,
            readOnly = true
        )
    }

    private fun writeActivePointer(descriptor: KnowledgePackDescriptor) {
        writeAtomically(
            activePointer,
            listOf(
                descriptor.packId,
                descriptor.packVersion,
                "trusted",
                "readonly"
            ).joinToString("\n", postfix = "\n")
        )
    }

    private fun writeAtomically(target: File, value: String) {
        val temporary = File(appOwnedRoot, target.name + ".tmp")
        temporary.writeText(value)
        Files.move(
            temporary.toPath(),
            target.toPath(),
            StandardCopyOption.ATOMIC_MOVE,
            StandardCopyOption.REPLACE_EXISTING
        )
    }

    private fun setTreeWritable(root: File, writable: Boolean) {
        root.walkBottomUp().forEach { file ->
            file.setReadable(true, true)
            file.setWritable(writable, true)
        }
    }

    private fun deleteOwnedTree(candidate: File) {
        val ownedRoot = runCatching { appOwnedRoot.canonicalFile }.getOrNull() ?: return
        val canonical = runCatching { candidate.canonicalFile }.getOrNull() ?: return
        if (canonical.parentFile == ownedRoot) canonical.deleteRecursively()
    }

    companion object {
        private const val MINIMUM_ROLLBACK_MARGIN_BYTES = 64L * 1024L * 1024L

        fun requiredImportFreeBytes(manifest: KnowledgePackManifest): Long? = runCatching {
            require(
                manifest.declaredArchiveSizeBytes >= 0L &&
                    manifest.declaredUnpackedSizeBytes >= 0L
            )
            val margin = maxOf(
                MINIMUM_ROLLBACK_MARGIN_BYTES,
                manifest.declaredUnpackedSizeBytes / 10L
            )
            Math.addExact(
                Math.addExact(
                    manifest.declaredArchiveSizeBytes,
                    manifest.declaredUnpackedSizeBytes
                ),
                margin
            )
        }.getOrNull()
    }
}

data class KnowledgePackInstallResult(
    val state: KnowledgePackState,
    val reasons: List<String> = emptyList()
)

class KnowledgePackInstaller(
    private val storage: KnowledgePackStorage,
    private val integrityVerifier: KnowledgePackIntegrityVerifier,
    private val signatureVerifier: KnowledgePackSignatureVerifier,
    private val compatibilityGate: KnowledgePackCompatibilityGate,
    private val runtimeProbe: (KnowledgePackDescriptor) -> Boolean
) {
    fun installVerifiedStaging(
        selection: KnowledgePackSelection,
        stagingDirectory: File,
        descriptor: KnowledgePackDescriptor,
        manifest: KnowledgePackManifest,
        modelDescriptor: ModelDescriptor?,
        indexDescriptor: SearchIndexDescriptor?
    ): KnowledgePackInstallResult {
        if (
            !selection.persistedReadPermission ||
            !selection.sourceReadable ||
            !selection.sourceUri.startsWith("content://")
        ) {
            storage.discardStaging(stagingDirectory)
            return KnowledgePackInstallResult(
                KnowledgePackState.PREFLIGHT_FAILED,
                listOf("Persisted read permission is required.")
            )
        }
        val requiredBytes = FileKnowledgePackStorage.requiredImportFreeBytes(manifest)
        if (requiredBytes == null || storage.availableBytes() < requiredBytes) {
            storage.discardStaging(stagingDirectory)
            return KnowledgePackInstallResult(
                KnowledgePackState.PREFLIGHT_FAILED,
                listOf("Insufficient app-specific storage.")
            )
        }
        if (!integrityVerifier.verify(stagingDirectory, manifest)) {
            storage.discardStaging(stagingDirectory)
            return KnowledgePackInstallResult(KnowledgePackState.CORRUPTED)
        }
        if (
            !manifest.productionApproved ||
            !manifest.signatureRequired ||
            !signatureVerifier.verify(manifest, stagingDirectory)
        ) {
            storage.discardStaging(stagingDirectory)
            return KnowledgePackInstallResult(KnowledgePackState.UNTRUSTED)
        }
        val verifiedDescriptor = descriptor.copy(
            state = KnowledgePackState.ACTIVE,
            signatureTrusted = true,
            readOnly = true
        )
        val compatibility = compatibilityGate.validate(
            modelDescriptor,
            manifest,
            verifiedDescriptor,
            indexDescriptor
        )
        if (!compatibility.compatible) {
            storage.discardStaging(stagingDirectory)
            return KnowledgePackInstallResult(
                KnowledgePackState.INCOMPATIBLE,
                compatibility.reasons
            )
        }
        if (!runtimeProbe(verifiedDescriptor)) {
            storage.discardStaging(stagingDirectory)
            return KnowledgePackInstallResult(KnowledgePackState.CORRUPTED)
        }
        if (!integrityVerifier.verify(stagingDirectory, manifest)) {
            storage.discardStaging(stagingDirectory)
            return KnowledgePackInstallResult(KnowledgePackState.CORRUPTED)
        }
        return if (storage.activateAtomically(stagingDirectory, verifiedDescriptor)) {
            KnowledgePackInstallResult(KnowledgePackState.ACTIVE)
        } else {
            storage.discardStaging(stagingDirectory)
            KnowledgePackInstallResult(KnowledgePackState.CORRUPTED)
        }
    }
}
