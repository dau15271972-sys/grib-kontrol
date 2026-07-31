package com.mushroom.detector

import android.graphics.BitmapFactory
import android.net.Uri
import androidx.camera.view.PreviewView
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.BoxScope
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ColumnScope
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.asPaddingValues
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.safeDrawing
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.ImageBitmap
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.lifecycle.compose.LocalLifecycleOwner
import com.mushroom.detector.capture.CameraController
import com.mushroom.detector.capture.CaptureViewType
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

internal object ApprovedDesign {
    const val FOREST_BACKGROUND = "karelia-bg-2.jpg"
    const val HERO_MUSHROOM = "karelia-bg.webp"
    const val TITLE = "ГРИБ КОНТРОЛЬ"

    val Forest = Color(0xFF356E4C)
    val DeepForest = Color(0xFF183A28)
    val Cream = Color(0xFFF4F5EE)
    val Ink = Color(0xFF183024)
    val Muted = Color(0xFF536259)
    val Danger = Color(0xFFB52D2D)
    val Amber = Color(0xFF9A6A20)
}

private val NaturalColorScheme = lightColorScheme(
    primary = ApprovedDesign.Forest,
    onPrimary = Color.White,
    secondary = ApprovedDesign.DeepForest,
    background = ApprovedDesign.Cream,
    surface = ApprovedDesign.Cream,
    onSurface = ApprovedDesign.Ink,
    error = ApprovedDesign.Danger
)

@Composable
internal fun MushroomAppTheme(content: @Composable () -> Unit) {
    MaterialTheme(colorScheme = NaturalColorScheme, content = content)
}

@Composable
internal fun ApprovedForestPage(
    content: @Composable ColumnScope.() -> Unit
) {
    Box(modifier = Modifier.fillMaxSize()) {
        AssetImage(
            assetName = ApprovedDesign.FOREST_BACKGROUND,
            contentDescription = null,
            modifier = Modifier.fillMaxSize()
        )
        Box(
            modifier = Modifier
                .fillMaxSize()
                .background(Color(0x260B1D11))
        )
        Column(
            modifier = Modifier
                .fillMaxSize()
                .verticalScroll(rememberScrollState())
                .padding(WindowInsets.safeDrawing.asPaddingValues())
                .padding(horizontal = 14.dp, vertical = 12.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp),
            content = content
        )
    }
}

@Composable
internal fun MushroomScreen(
    state: UiState,
    cameraController: CameraController,
    onSelectView: (CaptureViewType) -> Unit,
    onCapture: () -> Unit,
    onAssess: () -> Unit,
    onEmergency: () -> Unit,
    onCameraError: (String) -> Unit
) {
    ApprovedForestPage {
        HeroCard()
        HintCard()
        CaptureControls(state, onSelectView, onCapture, onAssess)
        CaptureGrid(state, cameraController, onSelectView, onCameraError)
        SafetyNotice()

        if (state.loading) {
            CircularProgressIndicator(
                modifier = Modifier.align(Alignment.CenterHorizontally),
                color = Color.White
            )
        }
        state.error?.let {
            ResultPanel(
                status = ResultStatus.TECHNICAL_FAILURE.name,
                title = "Техническая проблема",
                message = it,
                banner = "Опасный вариант исключить невозможно.",
                accent = ApprovedDesign.Danger
            )
        }
        state.result?.let { result ->
            ResultPanel(
                status = result.status.name,
                title = result.title,
                message = result.message,
                banner = result.safetyBanner,
                accent = when (result.status) {
                    ResultStatus.TECHNICAL_FAILURE,
                    ResultStatus.HIGH_RISK -> ApprovedDesign.Danger
                    ResultStatus.NEED_MORE_PHOTOS -> ApprovedDesign.Amber
                    else -> ApprovedDesign.Forest
                }
            )
        } ?: ResultPanel(
            status = ResultStatus.RECOGNITION_UNAVAILABLE.name,
            title = "Результат появится здесь",
            message = "Сделайте четыре независимых снимка одного гриба.",
            banner = "Без проверенной модели приложение не определяет вид и не даёт разрешений.",
            accent = ApprovedDesign.Amber
        )

        NaturalButton(
            label = "Экстренная помощь",
            onClick = onEmergency,
            containerColor = ApprovedDesign.Danger,
            modifier = Modifier.fillMaxWidth()
        )
        HistorySection(state.history)
    }
}

@Composable
private fun HeroCard() {
    Box(
        modifier = Modifier
            .fillMaxWidth()
            .height(220.dp)
            .clip(RoundedCornerShape(28.dp))
            .border(1.dp, Color(0x66FFFFFF), RoundedCornerShape(28.dp))
    ) {
        AssetImage(
            assetName = ApprovedDesign.HERO_MUSHROOM,
            contentDescription = "Утверждённая фотография гриба",
            modifier = Modifier.fillMaxSize()
        )
        Box(
            modifier = Modifier
                .fillMaxSize()
                .background(
                    Brush.verticalGradient(
                        listOf(Color.Transparent, Color(0xB3000000))
                    )
                )
        )
        Text(
            text = ApprovedDesign.TITLE,
            color = Color.White,
            fontSize = 42.sp,
            lineHeight = 40.sp,
            fontWeight = FontWeight.Black,
            letterSpacing = 1.sp,
            modifier = Modifier
                .align(Alignment.BottomStart)
                .padding(18.dp)
        )
    }
}

@Composable
private fun HintCard() {
    NaturalSurface {
        Text(
            text = "Сделайте 4 фото одного гриба: шляпка сверху, нижняя сторона, " +
                "основание ножки и боковой ракурс.",
            color = ApprovedDesign.Ink,
            fontSize = 17.sp,
            lineHeight = 23.sp,
            fontWeight = FontWeight.Bold
        )
    }
}

@Composable
private fun CaptureControls(
    state: UiState,
    onSelectView: (CaptureViewType) -> Unit,
    onCapture: () -> Unit,
    onAssess: () -> Unit
) {
    CaptureViewType.entries.chunked(2).forEach { rowViews ->
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(10.dp)
        ) {
            rowViews.forEach { viewType ->
                val captured = state.session.captures.containsKey(viewType)
                NaturalButton(
                    label = "${viewLabel(viewType)}${if (captured) " ✓" else ""}",
                    onClick = { onSelectView(viewType) },
                    containerColor = if (state.activeView == viewType) {
                        ApprovedDesign.DeepForest
                    } else {
                        ApprovedDesign.Forest
                    },
                    modifier = Modifier.weight(1f)
                )
            }
        }
    }
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.spacedBy(10.dp)
    ) {
        NaturalButton(
            label = "Снять выбранный",
            onClick = onCapture,
            containerColor = ApprovedDesign.Forest,
            modifier = Modifier.weight(1f)
        )
        NaturalButton(
            label = "Проверить",
            onClick = onAssess,
            containerColor = ApprovedDesign.Forest,
            modifier = Modifier.weight(1f)
        )
    }
}

@Composable
private fun CaptureGrid(
    state: UiState,
    cameraController: CameraController,
    onSelectView: (CaptureViewType) -> Unit,
    onCameraError: (String) -> Unit
) {
    CaptureViewType.entries.chunked(2).forEach { rowViews ->
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(10.dp)
        ) {
            rowViews.forEach { viewType ->
                CaptureCard(
                    viewType = viewType,
                    active = state.activeView == viewType,
                    captureUri = state.session.captures[viewType]?.uri,
                    cameraController = cameraController,
                    onSelect = { onSelectView(viewType) },
                    onCameraError = onCameraError,
                    modifier = Modifier.weight(1f)
                )
            }
        }
    }
}

@Composable
private fun CaptureCard(
    viewType: CaptureViewType,
    active: Boolean,
    captureUri: String?,
    cameraController: CameraController,
    onSelect: () -> Unit,
    onCameraError: (String) -> Unit,
    modifier: Modifier = Modifier
) {
    Surface(
        modifier = modifier
            .clickable(onClick = onSelect),
        color = Color(0xF2F4F5EE),
        shape = RoundedCornerShape(20.dp),
        shadowElevation = 8.dp
    ) {
        Column(
            modifier = Modifier.padding(10.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            Text(
                text = viewLabel(viewType),
                color = ApprovedDesign.Ink,
                fontWeight = FontWeight.SemiBold,
                fontSize = 14.sp
            )
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .height(135.dp)
                    .clip(RoundedCornerShape(14.dp))
                    .background(
                        Brush.radialGradient(
                            listOf(Color(0xFFD9C39B), Color(0xFF73543D))
                        )
                    )
            ) {
                when {
                    active -> CameraPreview(
                        cameraController = cameraController,
                        onError = onCameraError,
                        modifier = Modifier.fillMaxSize()
                    )
                    captureUri != null -> CapturedPhoto(
                        uri = captureUri,
                        modifier = Modifier.fillMaxSize()
                    )
                    else -> Text(
                        text = "Выберите ракурс",
                        color = Color.White,
                        fontSize = 12.sp,
                        modifier = Modifier.align(Alignment.Center)
                    )
                }
                if (captureUri != null) {
                    Surface(
                        modifier = Modifier
                            .align(Alignment.TopEnd)
                            .padding(7.dp),
                        color = ApprovedDesign.Forest,
                        shape = RoundedCornerShape(50)
                    ) {
                        Text(
                            text = "Снято",
                            color = Color.White,
                            fontSize = 11.sp,
                            modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp)
                        )
                    }
                }
            }
        }
    }
}

@Composable
private fun SafetyNotice() {
    NaturalSurface(accent = ApprovedDesign.Danger) {
        Text(
            text = "Важно: распознавание по фото не является экспертизой. " +
                "Не принимайте решение об употреблении гриба по результату приложения.",
            color = ApprovedDesign.Ink,
            fontSize = 15.sp,
            lineHeight = 21.sp
        )
    }
}

@Composable
private fun ResultPanel(
    status: String,
    title: String,
    message: String,
    banner: String,
    accent: Color
) {
    NaturalSurface(accent = accent) {
        Text(
            text = status,
            color = accent,
            fontSize = 12.sp,
            fontWeight = FontWeight.Bold
        )
        Text(
            text = title,
            color = ApprovedDesign.Ink,
            fontSize = 18.sp,
            fontWeight = FontWeight.Bold
        )
        Text(text = message, color = ApprovedDesign.Ink, lineHeight = 21.sp)
        Text(
            text = banner,
            color = ApprovedDesign.DeepForest,
            fontWeight = FontWeight.SemiBold,
            lineHeight = 21.sp
        )
    }
}

@Composable
private fun HistorySection(history: List<HistoryEntity>) {
    var expanded by rememberSaveable { mutableStateOf(false) }
    NaturalButton(
        label = if (expanded) "Скрыть историю" else "История оценок",
        onClick = { expanded = !expanded },
        containerColor = ApprovedDesign.DeepForest,
        modifier = Modifier.fillMaxWidth()
    )
    if (expanded) {
        NaturalSurface {
            if (history.isEmpty()) {
                Text("История пока пуста.", color = ApprovedDesign.Muted)
            } else {
                history.forEach { item ->
                    Text(
                        text = "${formatTimestamp(item.createdAt)} | ${item.status.name}",
                        color = ApprovedDesign.Ink,
                        fontWeight = FontWeight.SemiBold
                    )
                    Text(
                        text = "${item.title}\n${item.message}",
                        color = ApprovedDesign.Muted
                    )
                }
            }
        }
    }
}

@Composable
internal fun NaturalSurface(
    accent: Color? = null,
    content: @Composable ColumnScope.() -> Unit
) {
    Surface(
        modifier = Modifier.fillMaxWidth(),
        color = Color(0xF2F4F5EE),
        shape = RoundedCornerShape(20.dp),
        shadowElevation = 8.dp
    ) {
        Row {
            if (accent != null) {
                Box(
                    modifier = Modifier
                        .width(6.dp)
                        .height(140.dp)
                        .background(accent)
                )
            }
            Column(
                modifier = Modifier.padding(16.dp),
                verticalArrangement = Arrangement.spacedBy(8.dp),
                content = content
            )
        }
    }
}

@Composable
internal fun NaturalButton(
    label: String,
    onClick: () -> Unit,
    containerColor: Color,
    modifier: Modifier = Modifier
) {
    Button(
        onClick = onClick,
        modifier = modifier.height(50.dp),
        shape = RoundedCornerShape(18.dp),
        colors = ButtonDefaults.buttonColors(containerColor = containerColor)
    ) {
        Text(
            text = label,
            color = Color.White,
            fontWeight = FontWeight.SemiBold,
            fontSize = 13.sp
        )
    }
}

@Composable
private fun AssetImage(
    assetName: String,
    contentDescription: String?,
    modifier: Modifier = Modifier
) {
    val context = LocalContext.current
    val bitmap = remember(assetName) {
        runCatching {
            context.assets.open(assetName).use { stream ->
                BitmapFactory.decodeStream(stream)?.asImageBitmap()
            }
        }.getOrNull()
    }
    if (bitmap != null) {
        Image(
            bitmap = bitmap,
            contentDescription = contentDescription,
            contentScale = ContentScale.Crop,
            modifier = modifier
        )
    } else {
        Box(
            modifier = modifier.background(ApprovedDesign.DeepForest)
        )
    }
}

@Composable
private fun CapturedPhoto(uri: String, modifier: Modifier = Modifier) {
    val bitmap: ImageBitmap? = remember(uri) {
        val path = runCatching { Uri.parse(uri).path }.getOrNull()
        path?.let { BitmapFactory.decodeFile(it)?.asImageBitmap() }
    }
    if (bitmap != null) {
        Image(
            bitmap = bitmap,
            contentDescription = "Снятый ракурс",
            contentScale = ContentScale.Crop,
            modifier = modifier
        )
    }
}

@Composable
private fun BoxScope.CameraPreview(
    cameraController: CameraController,
    onError: (String) -> Unit,
    modifier: Modifier = Modifier
) {
    val lifecycleOwner = LocalLifecycleOwner.current
    AndroidView(
        factory = { context ->
            PreviewView(context).also { preview ->
                preview.scaleType = PreviewView.ScaleType.FILL_CENTER
                cameraController.bind(lifecycleOwner, preview, onError)
            }
        },
        modifier = modifier
    )
    DisposableEffect(cameraController, lifecycleOwner) {
        onDispose { cameraController.unbind() }
    }
}

private fun viewLabel(viewType: CaptureViewType): String = when (viewType) {
    CaptureViewType.CAP_TOP -> "Шляпка сверху"
    CaptureViewType.UNDERSIDE -> "Нижняя сторона"
    CaptureViewType.STEM_BASE -> "Основание ножки"
    CaptureViewType.SIDE -> "Боковой ракурс"
}

private fun formatTimestamp(timestamp: Long): String =
    SimpleDateFormat("dd.MM.yyyy HH:mm", Locale.getDefault()).format(Date(timestamp))
