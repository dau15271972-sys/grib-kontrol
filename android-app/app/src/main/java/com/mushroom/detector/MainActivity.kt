package com.mushroom.detector

import android.graphics.Bitmap
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.activity.result.contract.ActivityResultContracts
import androidx.activity.viewModels
import androidx.compose.foundation.Image
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.weight
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

class MainActivity : ComponentActivity() {
    private val vm: MushroomViewModel by viewModels()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()

        val topCameraLauncher = registerForActivityResult(ActivityResultContracts.TakePicturePreview()) { bitmap ->
            vm.onTopCaptured(bitmap)
        }
        val bottomCameraLauncher = registerForActivityResult(ActivityResultContracts.TakePicturePreview()) { bitmap ->
            vm.onBottomCaptured(bitmap)
        }

        setContent {
            MaterialTheme {
                val state by vm.uiState.collectAsStateWithLifecycle()
                MushroomScreen(
                    state = state,
                    onCaptureTop = { topCameraLauncher.launch(null) },
                    onCaptureBottom = { bottomCameraLauncher.launch(null) },
                    onDetect = { vm.detectOffline() }
                )
            }
        }
    }
}

@Composable
private fun MushroomScreen(
    state: UiState,
    onCaptureTop: () -> Unit,
    onCaptureBottom: () -> Unit,
    onDetect: () -> Unit
) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        Text(text = "Гриб Контроль", style = MaterialTheme.typography.headlineSmall)
        Text(
            text = "Сделайте 2 фото: верх шляпки и нижняя сторона.",
            style = MaterialTheme.typography.bodyMedium
        )

        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            Button(onClick = onCaptureTop) { Text("Фото сверху") }
            Button(onClick = onCaptureBottom) { Text("Фото снизу") }
            Button(onClick = onDetect) { Text("Проверить") }
        }

        Row(horizontalArrangement = Arrangement.spacedBy(12.dp), modifier = Modifier.fillMaxWidth()) {
            PhotoPreview(title = "Верхняя сторона", bitmap = state.topPhoto, modifier = Modifier.weight(1f))
            PhotoPreview(title = "Нижняя сторона", bitmap = state.bottomPhoto, modifier = Modifier.weight(1f))
        }

        if (state.loading) {
            CircularProgressIndicator()
        }

        if (!state.error.isNullOrBlank()) {
            ResultCard(title = "Ошибка", body = state.error)
        }

        state.result?.let { result ->
            if (!result.warning_text.isNullOrBlank() && result.risk_level in setOf("high", "medium")) {
                RiskAlertCard(
                    text = result.warning_text,
                    reason = result.risk_reason
                )
            }
            ResultCard(title = "Безопасность", body = result.safety_banner ?: "-")
            if (result.status == "ok") {
                ResultCard(
                    title = "${result.name_ru ?: "-"} (${result.name_latin ?: "-"})",
                    body = buildString {
                        appendLine("Съедобность: ${result.edibility ?: "-"}")
                        appendLine("Опасность: ${result.danger_level ?: "-"}")
                        appendLine("Уверенность: ${result.confidence ?: 0.0}%")
                        appendLine("2-й тест: пройден (${result.second_confidence ?: 0.0}%)")
                        appendLine("3-й тест: пройден (${result.third_confidence ?: 0.0}%)")
                        appendLine()
                        appendLine("Описание: ${result.notes ?: "-"}")
                        appendLine("Рекомендация: ${result.recommendation ?: "-"}")
                        if (!result.lookalikes.isNullOrEmpty()) {
                            appendLine("Похожие виды:")
                            result.lookalikes.forEach { appendLine("- $it") }
                        }
                    }
                )
            } else if (result.status == "danger") {
                ResultCard(
                    title = result.title ?: "ВНИМАНИЕ: высокий риск",
                    body = buildString {
                        appendLine("Съедобность: ${result.edibility ?: "-"}")
                        appendLine("Опасность: ${result.danger_level ?: "-"}")
                        appendLine("Уверенность: ${result.confidence ?: 0.0}%")
                        appendLine("2-й тест: ${if (result.second_test_passed == true) "пройден" else "не пройден"} (${result.second_confidence ?: 0.0}%)")
                        appendLine("3-й тест: ${if (result.third_test_passed == true) "пройден" else "не пройден"} (${result.third_confidence ?: 0.0}%)")
                        appendLine()
                        append(result.recommendation ?: "Не употреблять.")
                    }
                )
            } else {
                ResultCard(
                    title = result.title ?: "Нужна дополнительная проверка",
                    body = buildString {
                        appendLine("Уверенность: ${result.confidence ?: 0.0}%")
                        appendLine("2-й тест: ${if (result.second_test_passed == true) "пройден" else "не пройден"} (${result.second_confidence ?: 0.0}%)")
                        appendLine("3-й тест: ${if (result.third_test_passed == true) "пройден" else "не пройден"} (${result.third_confidence ?: 0.0}%)")
                        appendLine()
                        append(result.recommendation ?: "-")
                    }
                )
            }
        }

        if (state.history.isNotEmpty()) {
            Text(text = "Последние распознавания", style = MaterialTheme.typography.titleMedium)
            state.history.forEach { item ->
                ResultCard(
                    title = "${formatTimestamp(item.createdAt)} | ${item.nameRu ?: item.status}",
                    body = buildString {
                        appendLine("Статус: ${item.status}")
                        appendLine("Риск: ${item.riskLevel ?: "-"}")
                        appendLine("Уверенность: ${item.confidence ?: 0.0}%")
                        appendLine("2-й тест: ${item.secondConfidence ?: 0.0}%")
                        appendLine("3-й тест: ${item.thirdConfidence ?: 0.0}%")
                        if (!item.riskReason.isNullOrBlank()) {
                            appendLine("Причина риска: ${item.riskReason}")
                        }
                        append(item.recommendation ?: "-")
                    }
                )
            }
        }

        Spacer(modifier = Modifier.height(24.dp))
    }
}

@Composable
private fun RiskAlertCard(text: String?, reason: String?) {
    Surface(
        color = MaterialTheme.colorScheme.errorContainer,
        contentColor = MaterialTheme.colorScheme.onErrorContainer,
        tonalElevation = 4.dp,
        shape = RoundedCornerShape(12.dp),
        modifier = Modifier.fillMaxWidth()
    ) {
        Column(modifier = Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
            Text("ВНИМАНИЕ", style = MaterialTheme.typography.titleMedium)
            Text(text ?: "Возможна поганка или ложный гриб.", style = MaterialTheme.typography.bodyMedium)
            if (!reason.isNullOrBlank()) {
                Text("Причина: $reason", style = MaterialTheme.typography.bodySmall)
            }
        }
    }
}

@Composable
private fun PhotoPreview(
    title: String,
    bitmap: Bitmap?,
    modifier: Modifier = Modifier
) {
    Card(
        modifier = modifier,
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceContainerHigh)
    ) {
        Column(modifier = Modifier.padding(10.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Text(text = title, style = MaterialTheme.typography.titleSmall)
            if (bitmap == null) {
                Text("Фото не сделано")
            } else {
                Image(
                    bitmap = bitmap.asImageBitmap(),
                    contentDescription = title,
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(140.dp)
                        .clip(RoundedCornerShape(8.dp)),
                    contentScale = ContentScale.Crop
                )
            }
        }
    }
}

@Composable
private fun ResultCard(title: String, body: String?) {
    Card(
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceContainerHigh),
        modifier = Modifier.fillMaxWidth()
    ) {
        Column(modifier = Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Text(text = title, style = MaterialTheme.typography.titleMedium)
            Text(text = body ?: "-", style = MaterialTheme.typography.bodyMedium)
        }
    }
}

private fun formatTimestamp(timestamp: Long): String {
    val sdf = SimpleDateFormat("dd.MM.yyyy HH:mm", Locale.getDefault())
    return sdf.format(Date(timestamp))
}
