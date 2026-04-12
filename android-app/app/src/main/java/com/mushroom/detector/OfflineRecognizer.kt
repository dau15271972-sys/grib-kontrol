package com.mushroom.detector

import android.content.Context
import android.graphics.Bitmap
import android.graphics.Color
import android.graphics.Matrix
import com.google.gson.Gson
import kotlin.math.abs
import kotlin.math.round
import kotlin.math.sqrt

data class KnowledgeBase(
    val version: String,
    val global_safety_disclaimer: String,
    val species: Map<String, SpeciesInfo>
)

data class SpeciesInfo(
    val name_ru: String,
    val name_latin: String,
    val edibility: String,
    val danger_level: String,
    val is_toxic: Boolean = false,
    val is_false_mushroom: Boolean = false,
    val danger_tags: List<String> = emptyList(),
    val lookalikes: List<String> = emptyList(),
    val notes: String = "",
    val recommendation: String = ""
)

data class RecognitionIndex(
    val version: String,
    val threshold: Double,
    val consistency_gap: Double = 0.03,
    val high_risk_delta: Double = 0.04,
    val entries: List<RecognitionEntry>
)

data class RecognitionEntry(
    val species_id: String,
    val feature: List<Double>
)

private data class MatchResult(val speciesId: String, val score: Double)

private data class RiskInfo(
    val level: String,
    val reason: String,
    val warningText: String?
)

class OfflineRecognizer(context: Context) {
    private val gson = Gson()
    private val knowledge: KnowledgeBase
    private val index: RecognitionIndex

    init {
        val kbText = context.assets.open("knowledge_base.json")
            .bufferedReader(Charsets.UTF_8)
            .use { it.readText() }
        val idxText = context.assets.open("recognition_index.json")
            .bufferedReader(Charsets.UTF_8)
            .use { it.readText() }

        knowledge = gson.fromJson(kbText, KnowledgeBase::class.java)
        index = gson.fromJson(idxText, RecognitionIndex::class.java)
    }

    fun predict(topBitmap: Bitmap, bottomBitmap: Bitmap): MushroomApiResponse {
        val topFeatures = extractFeatures(topBitmap)
        val bottomFeatures = extractFeatures(bottomBitmap)
        val sideTop = scoreAll(topFeatures).first()
        val sideBottom = scoreAll(bottomFeatures).first()

        val sideConsistent = sideTop.speciesId == sideBottom.speciesId &&
            sideTop.score >= index.threshold &&
            sideBottom.score >= index.threshold

        val primaryFeatures = averageVectors(topFeatures, bottomFeatures)
        val primaryMatches = scoreAll(primaryFeatures)
        val primaryTop = primaryMatches.first()
        val confidence = primaryTop.score.coerceIn(0.0, 1.0)

        val secondaryFeatures = averageVectors(
            extractFeatures(mirror(topBitmap)),
            extractFeatures(mirror(bottomBitmap))
        )
        val secondaryTop = scoreAll(secondaryFeatures).first()
        val secondConfidence = secondaryTop.score.coerceIn(0.0, 1.0)
        val secondPassed = secondaryTop.speciesId == primaryTop.speciesId &&
            abs(confidence - secondConfidence) <= index.consistency_gap &&
            secondConfidence >= index.threshold

        val thirdFeatures = averageVectors(
            extractFeatures(rotate(topBitmap, 15f)),
            extractFeatures(rotate(bottomBitmap, 15f))
        )
        val thirdTop = scoreAll(thirdFeatures).first()
        val thirdConfidence = thirdTop.score.coerceIn(0.0, 1.0)
        val thirdPassed = thirdTop.speciesId == primaryTop.speciesId &&
            abs(confidence - thirdConfidence) <= index.consistency_gap &&
            thirdConfidence >= index.threshold

        val species = knowledge.species[primaryTop.speciesId]
        val toxicCompetitor = primaryMatches
            .drop(1)
            .firstOrNull { match ->
                val s = knowledge.species[match.speciesId] ?: return@firstOrNull false
                isDangerousSpecies(s)
            }
        val toxicClose = toxicCompetitor != null &&
            (primaryTop.score - toxicCompetitor.score) <= index.high_risk_delta

        val riskInfo = buildRiskInfo(
            species = species,
            sideConsistent = sideConsistent,
            confidence = confidence,
            secondPassed = secondPassed,
            thirdPassed = thirdPassed,
            toxicClose = toxicClose
        )

        if (!sideConsistent) {
            return MushroomApiResponse(
                status = "unknown",
                title = "Фото с двух сторон не совпали",
                confidence = percent(confidence),
                second_test_passed = false,
                second_confidence = percent(secondConfidence),
                third_test_passed = false,
                third_confidence = percent(thirdConfidence),
                recommendation = "Сделайте новые фото: верх шляпки, низ шляпки и ножка. Без подтверждения не употребляйте гриб.",
                safety_banner = knowledge.global_safety_disclaimer,
                risk_level = riskInfo.level,
                risk_reason = riskInfo.reason,
                warning_text = riskInfo.warningText
            )
        }

        if (confidence < index.threshold) {
            return MushroomApiResponse(
                status = "unknown",
                title = "Низкая уверенность распознавания",
                confidence = percent(confidence),
                second_test_passed = secondPassed,
                second_confidence = percent(secondConfidence),
                third_test_passed = thirdPassed,
                third_confidence = percent(thirdConfidence),
                recommendation = "Модель не уверена. Переснимите гриб при дневном свете и проверьте у специалиста.",
                safety_banner = knowledge.global_safety_disclaimer,
                risk_level = riskInfo.level,
                risk_reason = riskInfo.reason,
                warning_text = riskInfo.warningText
            )
        }

        if (!(secondPassed && thirdPassed)) {
            return MushroomApiResponse(
                status = "unknown",
                title = "Контрольные тесты не пройдены",
                confidence = percent(confidence),
                second_test_passed = secondPassed,
                second_confidence = percent(secondConfidence),
                third_test_passed = thirdPassed,
                third_confidence = percent(thirdConfidence),
                recommendation = "Финальная проверка не подтвердила результат. Сделайте еще 2-3 фото и не принимайте решение об употреблении.",
                safety_banner = knowledge.global_safety_disclaimer,
                risk_level = riskInfo.level,
                risk_reason = riskInfo.reason,
                warning_text = riskInfo.warningText
            )
        }

        if (species == null) {
            return MushroomApiResponse(
                status = "unknown",
                title = "Вид не найден в базе",
                confidence = percent(confidence),
                second_test_passed = secondPassed,
                second_confidence = percent(secondConfidence),
                third_test_passed = thirdPassed,
                third_confidence = percent(thirdConfidence),
                recommendation = "Обновите локальную базу знаний перед использованием.",
                safety_banner = knowledge.global_safety_disclaimer,
                risk_level = "high",
                risk_reason = "Вид отсутствует в локальной базе",
                warning_text = "ВНИМАНИЕ: вид не подтвержден. Возможна поганка или ложный гриб."
            )
        }

        val dangerousTop = isDangerousSpecies(species)
        if (dangerousTop || toxicClose) {
            return MushroomApiResponse(
                status = "danger",
                title = "Высокий риск: возможна поганка или ложный гриб",
                species_id = primaryTop.speciesId,
                name_ru = species.name_ru,
                name_latin = species.name_latin,
                edibility = species.edibility,
                danger_level = species.danger_level,
                confidence = percent(confidence),
                second_test_passed = secondPassed,
                second_confidence = percent(secondConfidence),
                third_test_passed = thirdPassed,
                third_confidence = percent(thirdConfidence),
                lookalikes = species.lookalikes,
                notes = species.notes,
                recommendation = "Не употреблять. Нужна очная проверка микологом.",
                safety_banner = knowledge.global_safety_disclaimer,
                risk_level = "high",
                risk_reason = riskInfo.reason,
                warning_text = riskInfo.warningText
            )
        }

        return MushroomApiResponse(
            status = "ok",
            species_id = primaryTop.speciesId,
            name_ru = species.name_ru,
            name_latin = species.name_latin,
            edibility = species.edibility,
            danger_level = species.danger_level,
            confidence = percent(confidence),
            second_test_passed = secondPassed,
            second_confidence = percent(secondConfidence),
            third_test_passed = thirdPassed,
            third_confidence = percent(thirdConfidence),
            lookalikes = species.lookalikes,
            notes = species.notes,
            recommendation = species.recommendation,
            safety_banner = knowledge.global_safety_disclaimer,
            risk_level = riskInfo.level,
            risk_reason = riskInfo.reason,
            warning_text = riskInfo.warningText
        )
    }

    private fun buildRiskInfo(
        species: SpeciesInfo?,
        sideConsistent: Boolean,
        confidence: Double,
        secondPassed: Boolean,
        thirdPassed: Boolean,
        toxicClose: Boolean
    ): RiskInfo {
        if (species == null) {
            return RiskInfo(
                level = "high",
                reason = "Вид не найден в базе",
                warningText = "ВНИМАНИЕ: возможна поганка или ложный гриб. Не употреблять."
            )
        }
        if (isFalseSpecies(species)) {
            return RiskInfo(
                level = "high",
                reason = "Распознан ложный гриб",
                warningText = "ВНИМАНИЕ: распознан ложный гриб. Не употреблять."
            )
        }
        if (toxicClose) {
            return RiskInfo(
                level = "high",
                reason = "Рядом по вероятности есть опасный двойник",
                warningText = null
            )
        }
        if (!sideConsistent || !secondPassed || !thirdPassed || confidence < index.threshold) {
            return RiskInfo(
                level = "medium",
                reason = "Распознавание нестабильно, требуется пересъемка",
                warningText = null
            )
        }
        return RiskInfo(level = "low", reason = "Высоких рисков не обнаружено", warningText = null)
    }

    private fun isDangerousSpecies(species: SpeciesInfo): Boolean {
        return species.is_toxic ||
            species.is_false_mushroom ||
            species.danger_tags.any { it.contains("поганк", ignoreCase = true) || it.contains("ложн", ignoreCase = true) }
    }

    private fun isFalseSpecies(species: SpeciesInfo): Boolean {
        return species.is_false_mushroom ||
            species.danger_tags.any { it.contains("ложн", ignoreCase = true) }
    }

    private fun scoreAll(features: List<Double>): List<MatchResult> {
        return index.entries
            .map { entry -> MatchResult(entry.species_id, cosine(features, entry.feature)) }
            .sortedByDescending { it.score }
    }

    private fun extractFeatures(bitmap: Bitmap): List<Double> {
        val resized = Bitmap.createScaledBitmap(bitmap, 64, 64, true)
        val pixels = IntArray(64 * 64)
        resized.getPixels(pixels, 0, 64, 0, 0, 64, 64)

        val r = ArrayList<Double>(pixels.size)
        val g = ArrayList<Double>(pixels.size)
        val b = ArrayList<Double>(pixels.size)

        for (pixel in pixels) {
            r.add(Color.red(pixel) / 255.0)
            g.add(Color.green(pixel) / 255.0)
            b.add(Color.blue(pixel) / 255.0)
        }

        val features = mutableListOf<Double>()
        listOf(r, g, b).forEach { channel ->
            val mean = channel.average()
            val variance = channel.sumOf { (it - mean) * (it - mean) } / channel.size
            val std = sqrt(variance)
            features.add(mean)
            features.add(std)

            val bins = DoubleArray(8)
            channel.forEach { value ->
                val idx = minOf((value * 8).toInt(), 7)
                bins[idx] += 1.0
            }
            bins.forEach { features.add(it / channel.size) }
        }
        return features
    }

    private fun cosine(v1: List<Double>, v2: List<Double>): Double {
        if (v1.size != v2.size) return 0.0
        var dot = 0.0
        var n1 = 0.0
        var n2 = 0.0
        for (i in v1.indices) {
            dot += v1[i] * v2[i]
            n1 += v1[i] * v1[i]
            n2 += v2[i] * v2[i]
        }
        if (n1 == 0.0 || n2 == 0.0) return 0.0
        return dot / (sqrt(n1) * sqrt(n2))
    }

    private fun averageVectors(v1: List<Double>, v2: List<Double>): List<Double> {
        val size = minOf(v1.size, v2.size)
        return List(size) { i -> (v1[i] + v2[i]) / 2.0 }
    }

    private fun mirror(bitmap: Bitmap): Bitmap {
        val matrix = Matrix().apply { preScale(-1f, 1f) }
        return Bitmap.createBitmap(bitmap, 0, 0, bitmap.width, bitmap.height, matrix, true)
    }

    private fun rotate(bitmap: Bitmap, degrees: Float): Bitmap {
        val matrix = Matrix().apply { postRotate(degrees) }
        return Bitmap.createBitmap(bitmap, 0, 0, bitmap.width, bitmap.height, matrix, true)
    }

    private fun percent(value: Double): Double = round(value * 10000.0) / 100.0
}
