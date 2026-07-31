package com.mushroom.detector.capture

import android.content.Context
import android.net.Uri
import android.view.Surface
import androidx.camera.core.CameraSelector
import androidx.camera.core.ImageCapture
import androidx.camera.core.ImageCaptureException
import androidx.camera.core.Preview
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.camera.view.PreviewView
import androidx.core.content.ContextCompat
import androidx.lifecycle.LifecycleOwner

class CameraController(private val context: Context) {
    private val captureFileStore = CaptureFileStore(context.cacheDir)
    private var cameraProvider: ProcessCameraProvider? = null
    private var imageCapture: ImageCapture? = null

    init {
        // Privacy: remove app-private temporary captures left by an interrupted session.
        captureFileStore.clearResidualFiles()
    }

    fun bind(
        lifecycleOwner: LifecycleOwner,
        previewView: PreviewView,
        onError: (String) -> Unit
    ) {
        val providerFuture = ProcessCameraProvider.getInstance(context)
        providerFuture.addListener(
            {
                try {
                    val provider = providerFuture.get()
                    val preview = Preview.Builder().build().also {
                        it.surfaceProvider = previewView.surfaceProvider
                    }
                    val capture = ImageCapture.Builder()
                        .setCaptureMode(ImageCapture.CAPTURE_MODE_MINIMIZE_LATENCY)
                        // CameraX records this rotation in EXIF for downstream decoding.
                        .setTargetRotation(previewView.display?.rotation ?: Surface.ROTATION_0)
                        .build()
                    provider.unbindAll()
                    provider.bindToLifecycle(
                        lifecycleOwner,
                        CameraSelector.DEFAULT_BACK_CAMERA,
                        preview,
                        capture
                    )
                    cameraProvider = provider
                    imageCapture = capture
                } catch (error: Exception) {
                    onError(error.message ?: "Камера недоступна")
                }
            },
            ContextCompat.getMainExecutor(context)
        )
    }

    fun capture(
        viewType: CaptureViewType,
        onCaptured: (CaptureViewType, Uri) -> Unit,
        onError: (String) -> Unit
    ) {
        val capture = imageCapture
        if (capture == null) {
            onError("Камера ещё не готова")
            return
        }

        val outputFile = captureFileStore.createCaptureFile(viewType)
        val outputOptions = ImageCapture.OutputFileOptions.Builder(outputFile).build()

        capture.takePicture(
            outputOptions,
            ContextCompat.getMainExecutor(context),
            object : ImageCapture.OnImageSavedCallback {
                override fun onImageSaved(output: ImageCapture.OutputFileResults) {
                    onCaptured(viewType, Uri.fromFile(outputFile))
                }

                override fun onError(exception: ImageCaptureException) {
                    outputFile.delete()
                    onError(exception.message ?: "Не удалось сохранить фотографию")
                }
            }
        )
    }

    fun unbind() {
        cameraProvider?.unbindAll()
        cameraProvider = null
        imageCapture = null
    }
}
