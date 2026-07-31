package com.mushroom.detector

import android.Manifest
import android.content.pm.PackageManager
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.activity.result.contract.ActivityResultContracts
import androidx.activity.viewModels
import androidx.core.content.ContextCompat
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.mushroom.detector.capture.CameraController
import com.mushroom.detector.emergency.EmergencyHelpScreen

class MainActivity : ComponentActivity() {
    private val vm: MushroomViewModel by viewModels()
    private lateinit var cameraController: CameraController

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        cameraController = CameraController(this)

        val permissionLauncher = registerForActivityResult(
            ActivityResultContracts.RequestPermission()
        ) { granted ->
            if (!granted) vm.onCaptureError("Для съёмки нужен доступ к камере")
        }

        setContent {
            MushroomAppTheme {
                val state = vm.uiState.collectAsStateWithLifecycle().value
                if (state.showEmergency) {
                    EmergencyHelpScreen(onBack = vm::hideEmergency)
                } else {
                    MushroomScreen(
                        state = state,
                        cameraController = cameraController,
                        onSelectView = vm::selectView,
                        onCapture = {
                            cameraController.capture(
                                state.activeView,
                                vm::onCaptured,
                                vm::onCaptureError
                            )
                        },
                        onAssess = vm::assess,
                        onEmergency = vm::showEmergency,
                        onCameraError = vm::onCaptureError
                    )
                }
            }
        }

        if (
            ContextCompat.checkSelfPermission(this, Manifest.permission.CAMERA) !=
            PackageManager.PERMISSION_GRANTED
        ) {
            permissionLauncher.launch(Manifest.permission.CAMERA)
        }
    }
}
