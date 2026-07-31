package com.mushroom.detector.capture

import java.io.File
import java.nio.file.Files
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class CaptureFileStoreTest {
    @Test
    fun capturesStayInAppPrivateCacheAndAreDeletedOnRecapture() {
        val cacheDir = Files.createTempDirectory("capture-store").toFile()
        try {
            val store = CaptureFileStore(cacheDir)
            val first = store.createCaptureFile(CaptureViewType.CAP_TOP)

            assertTrue(first.canonicalPath.startsWith(cacheDir.canonicalPath))
            assertTrue(first.exists())
            assertTrue(store.deleteUri(first.toURI().toString()))
            assertFalse(first.exists())
        } finally {
            cacheDir.deleteRecursively()
        }
    }

    @Test
    fun completedSessionAndNextLaunchRemoveTemporaryPhotos() {
        val cacheDir = Files.createTempDirectory("capture-store").toFile()
        try {
            val store = CaptureFileStore(cacheDir)
            val completed = store.createCaptureFile(CaptureViewType.SIDE)
            val session = ObservationSession().withCapture(
                CapturedObservation(CaptureViewType.SIDE, completed.toURI().toString(), 1)
            )

            store.deleteSession(session)
            assertFalse(completed.exists())

            val interrupted = store.createCaptureFile(CaptureViewType.UNDERSIDE)
            CaptureFileStore(cacheDir).clearResidualFiles()
            assertFalse(interrupted.exists())
        } finally {
            cacheDir.deleteRecursively()
        }
    }

    @Test
    fun refusesToDeleteOutsideCaptureDirectory() {
        val cacheDir = Files.createTempDirectory("capture-store").toFile()
        val outside = File.createTempFile("outside-capture", ".jpg")
        try {
            val store = CaptureFileStore(cacheDir)

            assertFalse(store.deleteUri(outside.toURI().toString()))
            assertTrue(outside.exists())
        } finally {
            cacheDir.deleteRecursively()
            outside.delete()
        }
    }
}
