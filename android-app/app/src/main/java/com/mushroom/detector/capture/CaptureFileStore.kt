package com.mushroom.detector.capture

import java.io.File
import java.net.URI

class CaptureFileStore(cacheDir: File) {
    private val captureDir = File(cacheDir, "observation-captures")
    private val canonicalCaptureDir = captureDir.canonicalFile

    fun clearResidualFiles() {
        captureDir.listFiles()?.forEach { file ->
            if (isInsideCaptureDir(file)) file.delete()
        }
    }

    fun createCaptureFile(viewType: CaptureViewType): File {
        captureDir.mkdirs()
        return File.createTempFile(
            "${viewType.name.lowercase()}-",
            ".jpg",
            captureDir
        )
    }

    fun deleteUri(uri: String): Boolean {
        val file = runCatching { File(URI(uri)) }.getOrNull() ?: return false
        return deleteFile(file)
    }

    fun deleteSession(session: ObservationSession) {
        session.captures.values.forEach { deleteUri(it.uri) }
    }

    private fun deleteFile(file: File): Boolean =
        isInsideCaptureDir(file) && (!file.exists() || file.delete())

    private fun isInsideCaptureDir(file: File): Boolean {
        val candidate = file.canonicalFile
        return candidate.parentFile == canonicalCaptureDir
    }
}
