from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PIL import Image
from PIL import ImageOps
from io import BytesIO


@dataclass
class MatchResult:
    species_id: str
    score: float


class MushroomRecognizer:
    def __init__(self, knowledge_path: Path, recognition_path: Path) -> None:
        self.knowledge_path = knowledge_path
        self.recognition_path = recognition_path
        self.knowledge = self._load_json(knowledge_path)
        self.index = self._load_json(recognition_path)
        self._validate_files()

    @staticmethod
    def _load_json(path: Path) -> dict[str, Any]:
        if not path.exists():
            raise FileNotFoundError(f"Файл не найден: {path}")
        with path.open("r", encoding="utf-8-sig") as f:
            return json.load(f)

    def _validate_files(self) -> None:
        species_map = self.knowledge.get("species", {})
        if not species_map:
            raise ValueError("knowledge_base.json пуст или не содержит species.")
        entries = self.index.get("entries", [])
        if not entries:
            raise ValueError("recognition_index.json пуст или не содержит entries.")
        for entry in entries:
            if entry["species_id"] not in species_map:
                raise ValueError(
                    f"species_id '{entry['species_id']}' из recognition_index.json не найден в knowledge_base.json."
                )

    def predict(self, image_bytes: bytes) -> dict[str, Any]:
        features_primary = self._extract_features(image_bytes)
        primary_matches = self._score_all(features_primary)
        top = primary_matches[0]
        threshold = float(self.index.get("threshold", 0.82))
        consistency_gap = float(self.index.get("consistency_gap", 0.03))

        species = self.knowledge["species"][top.species_id]
        confidence = max(0.0, min(1.0, top.score))

        # Mandatory second pass: mirrored variant must support the same class.
        features_secondary = self._extract_features(self._make_secondary_view(image_bytes))
        secondary_matches = self._score_all(features_secondary)
        second_top = secondary_matches[0]
        second_confidence = max(0.0, min(1.0, second_top.score))
        consistent_label = second_top.species_id == top.species_id
        consistent_confidence = abs(confidence - second_confidence) <= consistency_gap
        second_test_passed = consistent_label and consistent_confidence and second_confidence >= threshold

        # Mandatory third pass: slight rotation must also support the same class.
        features_third = self._extract_features(self._make_third_view(image_bytes))
        third_matches = self._score_all(features_third)
        third_top = third_matches[0]
        third_confidence = max(0.0, min(1.0, third_top.score))
        third_consistent_label = third_top.species_id == top.species_id
        third_consistent_confidence = abs(confidence - third_confidence) <= consistency_gap
        third_test_passed = third_consistent_label and third_consistent_confidence and third_confidence >= threshold

        if confidence < threshold:
            return {
                "status": "unknown",
                "title": "Низкая уверенность распознавания",
                "confidence": round(confidence * 100, 2),
                "second_test_passed": False,
                "second_confidence": round(second_confidence * 100, 2),
                "third_test_passed": False,
                "third_confidence": round(third_confidence * 100, 2),
                "recommendation": (
                    "Модель не уверена в результате. Сделайте фото сверху и снизу шляпки "
                    "при дневном свете и проверьте у специалиста."
                ),
                "safety_banner": self.knowledge["global_safety_disclaimer"],
            }

        if not (second_test_passed and third_test_passed):
            return {
                "status": "unknown",
                "title": "Контрольные тесты не пройдены",
                "confidence": round(confidence * 100, 2),
                "second_test_passed": second_test_passed,
                "second_confidence": round(second_confidence * 100, 2),
                "third_test_passed": third_test_passed,
                "third_confidence": round(third_confidence * 100, 2),
                "recommendation": (
                    "Финальная проверка (2-й и 3-й тест) не подтвердила результат. Загрузите еще 2-3 фото "
                    "с разных ракурсов и не принимайте решение об употреблении по этому ответу."
                ),
                "safety_banner": self.knowledge["global_safety_disclaimer"],
            }

        return {
            "status": "ok",
            "species_id": top.species_id,
            "name_ru": species["name_ru"],
            "name_latin": species["name_latin"],
            "edibility": species["edibility"],
            "danger_level": species["danger_level"],
            "confidence": round(confidence * 100, 2),
            "second_test_passed": True,
            "second_confidence": round(second_confidence * 100, 2),
            "third_test_passed": True,
            "third_confidence": round(third_confidence * 100, 2),
            "lookalikes": species.get("lookalikes", []),
            "notes": species.get("notes", ""),
            "recommendation": species.get("recommendation", ""),
            "safety_banner": self.knowledge["global_safety_disclaimer"],
        }

    def _score_all(self, features: list[float]) -> list[MatchResult]:
        matches = [
            MatchResult(species_id=e["species_id"], score=self._cosine(features, e["feature"]))
            for e in self.index["entries"]
        ]
        matches.sort(key=lambda x: x.score, reverse=True)
        return matches

    @staticmethod
    def _make_secondary_view(image_bytes: bytes) -> bytes:
        image = Image.open(BytesIO(image_bytes)).convert("RGB")
        # Secondary test checks prediction stability under horizontal flip.
        mirrored = ImageOps.mirror(image)
        buf = BytesIO()
        mirrored.save(buf, format="PNG")
        return buf.getvalue()

    @staticmethod
    def _make_third_view(image_bytes: bytes) -> bytes:
        image = Image.open(BytesIO(image_bytes)).convert("RGB")
        # Third test checks prediction stability on slight geometric change.
        rotated = image.rotate(15, resample=Image.Resampling.BICUBIC, expand=False)
        buf = BytesIO()
        rotated.save(buf, format="PNG")
        return buf.getvalue()

    @staticmethod
    def _extract_features(image_bytes: bytes) -> list[float]:
        image = Image.open(BytesIO(image_bytes)).convert("RGB").resize((64, 64))
        pixels = list(image.getdata())

        channels = [[], [], []]
        for r, g, b in pixels:
            channels[0].append(r / 255.0)
            channels[1].append(g / 255.0)
            channels[2].append(b / 255.0)

        feats: list[float] = []
        bins = 8
        for channel in channels:
            mean = sum(channel) / len(channel)
            var = sum((v - mean) ** 2 for v in channel) / len(channel)
            std = math.sqrt(var)
            feats.extend([mean, std])

            hist = [0.0 for _ in range(bins)]
            for v in channel:
                idx = min(int(v * bins), bins - 1)
                hist[idx] += 1.0
            total = len(channel)
            feats.extend([h / total for h in hist])
        return feats

    @staticmethod
    def _cosine(v1: list[float], v2: list[float]) -> float:
        if len(v1) != len(v2):
            return 0.0
        dot = sum(a * b for a, b in zip(v1, v2))
        n1 = math.sqrt(sum(a * a for a in v1))
        n2 = math.sqrt(sum(b * b for b in v2))
        if n1 == 0 or n2 == 0:
            return 0.0
        return dot / (n1 * n2)
