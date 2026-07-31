package com.mushroom.detector.emergency

import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.sp
import com.mushroom.detector.ApprovedDesign
import com.mushroom.detector.ApprovedForestPage
import com.mushroom.detector.NaturalButton
import com.mushroom.detector.NaturalSurface

@Composable
fun EmergencyHelpScreen(onBack: () -> Unit) {
    ApprovedForestPage {
        NaturalSurface(accent = ApprovedDesign.Danger) {
            Text(
                text = "ЭКСТРЕННАЯ ПОМОЩЬ",
                color = ApprovedDesign.Ink,
                fontSize = 28.sp,
                fontWeight = FontWeight.Black
            )
            Text(
                text = EmergencyContent.REVIEW_NOTICE,
                color = ApprovedDesign.Danger,
                fontWeight = FontWeight.Bold
            )
            Text(
                text = EmergencyContent.PLACEHOLDER_GUIDANCE,
                color = ApprovedDesign.Ink,
                lineHeight = 22.sp
            )
            EmergencyContent.emergencyNumber?.let { approvedNumber ->
                Text(
                    text = "Экстренный номер: $approvedNumber",
                    color = ApprovedDesign.Ink,
                    fontWeight = FontWeight.Bold
                )
            }
        }
        NaturalButton(
            label = "Вернуться",
            onClick = onBack,
            containerColor = ApprovedDesign.DeepForest,
            modifier = Modifier
        )
        Text(
            text = "Не ждите результата приложения.",
            color = Color.White,
            fontWeight = FontWeight.SemiBold
        )
    }
}
