package com.mushroom.detector

import android.app.Application
import android.graphics.Bitmap
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

data class UiState(
    val topPhoto: Bitmap? = null,
    val bottomPhoto: Bitmap? = null,
    val loading: Boolean = false,
    val error: String? = null,
    val result: MushroomApiResponse? = null,
    val history: List<HistoryEntity> = emptyList()
)

class MushroomViewModel(application: Application) : AndroidViewModel(application) {
    private val recognizer = OfflineRecognizer(application)
    private val historyDao = AppDatabase.get(application).historyDao()

    private val _uiState = MutableStateFlow(UiState())
    val uiState: StateFlow<UiState> = _uiState.asStateFlow()

    init {
        refreshHistory()
    }

    fun onTopCaptured(bitmap: Bitmap?) {
        if (bitmap == null) {
            _uiState.value = _uiState.value.copy(error = "Не удалось получить фото верхней стороны.")
            return
        }
        _uiState.value = _uiState.value.copy(topPhoto = bitmap, error = null, result = null)
    }

    fun onBottomCaptured(bitmap: Bitmap?) {
        if (bitmap == null) {
            _uiState.value = _uiState.value.copy(error = "Не удалось получить фото нижней стороны.")
            return
        }
        _uiState.value = _uiState.value.copy(bottomPhoto = bitmap, error = null, result = null)
    }

    fun detectOffline() {
        val top = _uiState.value.topPhoto
        val bottom = _uiState.value.bottomPhoto
        if (top == null || bottom == null) {
            _uiState.value = _uiState.value.copy(
                error = "Нужно 2 фото: верхняя и нижняя стороны гриба."
            )
            return
        }

        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(loading = true, error = null, result = null)
            try {
                val result = withContext(Dispatchers.Default) {
                    recognizer.predict(top, bottom)
                }
                withContext(Dispatchers.IO) {
                    historyDao.insert(
                        HistoryEntity(
                            createdAt = System.currentTimeMillis(),
                            status = result.status ?: "unknown",
                            nameRu = result.name_ru,
                            nameLatin = result.name_latin,
                            edibility = result.edibility,
                            dangerLevel = result.danger_level,
                            confidence = result.confidence,
                            secondConfidence = result.second_confidence,
                            thirdConfidence = result.third_confidence,
                            recommendation = result.recommendation,
                            riskLevel = result.risk_level,
                            riskReason = result.risk_reason
                        )
                    )
                }
                _uiState.value = _uiState.value.copy(loading = false, result = result)
                refreshHistory()
            } catch (e: Exception) {
                _uiState.value = _uiState.value.copy(
                    loading = false,
                    error = "Ошибка локального распознавания: ${e.message ?: "неизвестно"}"
                )
            }
        }
    }

    private fun refreshHistory() {
        viewModelScope.launch {
            val items = withContext(Dispatchers.IO) { historyDao.latest(20) }
            _uiState.value = _uiState.value.copy(history = items)
        }
    }
}
