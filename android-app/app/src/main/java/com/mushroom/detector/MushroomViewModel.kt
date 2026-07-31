package com.mushroom.detector

import android.app.Application
import android.net.Uri
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.mushroom.detector.capture.CapturedObservation
import com.mushroom.detector.capture.CaptureFileStore
import com.mushroom.detector.capture.CaptureViewType
import com.mushroom.detector.capture.ObservationSession
import com.mushroom.detector.inference.NoModelInferenceEngine
import com.mushroom.detector.inference.SafeInferenceRunner
import com.mushroom.detector.quality.QualityAndViewValidator
import com.mushroom.detector.quality.QualityResult
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

data class UiState(
    val session: ObservationSession = ObservationSession(),
    val activeView: CaptureViewType = CaptureViewType.CAP_TOP,
    val loading: Boolean = false,
    val error: String? = null,
    val result: MushroomApiResponse? = null,
    val history: List<HistoryEntity> = emptyList(),
    val showEmergency: Boolean = false
)

class MushroomViewModel(application: Application) : AndroidViewModel(application) {
    private val inferenceRunner = SafeInferenceRunner(NoModelInferenceEngine())
    private val validator = QualityAndViewValidator()
    private val historyDao = AppDatabase.get(application).historyDao()
    private val captureFileStore = CaptureFileStore(application.cacheDir)

    private val _uiState = MutableStateFlow(UiState())
    val uiState: StateFlow<UiState> = _uiState.asStateFlow()

    init {
        refreshHistory()
    }

    fun selectView(viewType: CaptureViewType) {
        _uiState.value = _uiState.value.copy(activeView = viewType, error = null)
    }

    fun onCaptured(viewType: CaptureViewType, uri: Uri) {
        val oldCapture = _uiState.value.session.captures[viewType]
        oldCapture?.uri?.let(captureFileStore::deleteUri)
        val capture = CapturedObservation(
            viewType,
            uri.toString(),
            System.currentTimeMillis()
        )
        _uiState.value = _uiState.value.copy(
            session = _uiState.value.session.withCapture(capture),
            error = null,
            result = null
        )
    }

    fun onCaptureError(message: String) {
        _uiState.value = _uiState.value.copy(error = message)
    }

    fun assess() {
        when (val quality = validator.validate(_uiState.value.session)) {
            QualityResult.Accepted -> runInference()
            is QualityResult.MissingViews -> {
                val missing = quality.views.joinToString { it.name }
                _uiState.value = _uiState.value.copy(
                    result = MushroomApiResponse(
                        status = ResultStatus.NEED_MORE_PHOTOS,
                        title = "Нужны дополнительные фотографии",
                        message = "Не сняты обязательные ракурсы: $missing.",
                        safetyBanner = (
                            "Без полного набора ракурсов опасный вариант исключить невозможно."
                            )
                    )
                )
            }
        }
    }

    fun showEmergency() {
        _uiState.value = _uiState.value.copy(showEmergency = true)
    }

    fun hideEmergency() {
        _uiState.value = _uiState.value.copy(showEmergency = false)
    }

    private fun runInference() {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(loading = true, error = null)
            val completedSession = _uiState.value.session
            val result = withContext(Dispatchers.Default) {
                inferenceRunner.run(completedSession)
            }
            try {
                withContext(Dispatchers.IO) {
                    historyDao.insert(
                        HistoryEntity(
                            createdAt = System.currentTimeMillis(),
                            status = result.status,
                            title = result.title,
                            message = result.message
                        )
                    )
                }
            } finally {
                captureFileStore.deleteSession(completedSession)
            }
            _uiState.value = _uiState.value.copy(
                session = ObservationSession(),
                loading = false,
                result = result
            )
            refreshHistory()
        }
    }

    private fun refreshHistory() {
        viewModelScope.launch {
            val items = withContext(Dispatchers.IO) { historyDao.latest(20) }
            _uiState.value = _uiState.value.copy(history = items)
        }
    }

    override fun onCleared() {
        captureFileStore.deleteSession(_uiState.value.session)
        super.onCleared()
    }
}
