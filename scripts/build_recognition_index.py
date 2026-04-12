from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.recognizer import MushroomRecognizer


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build recognition_index.json from reference photos."
    )
    parser.add_argument(
        "--dataset",
        required=True,
        help="Path to folder with species subfolders: dataset/species_id/*.jpg",
    )
    parser.add_argument(
        "--out",
        default="data/recognition_index.json",
        help="Output JSON path",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.82,
        help="Recognition confidence threshold",
    )
    args = parser.parse_args()

    dataset = Path(args.dataset)
    out_path = Path(args.out)
    if not dataset.exists():
        raise FileNotFoundError(f"Dataset path not found: {dataset}")

    entries = []
    for species_dir in sorted([p for p in dataset.iterdir() if p.is_dir()]):
        vectors = []
        for img_path in species_dir.rglob("*"):
            if img_path.suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp"}:
                continue
            image_bytes = img_path.read_bytes()
            vectors.append(MushroomRecognizer._extract_features(image_bytes))
        if not vectors:
            continue

        # Mean vector over all reference images for species.
        dims = len(vectors[0])
        mean_vector = [sum(v[i] for v in vectors) / len(vectors) for i in range(dims)]
        entries.append({"species_id": species_dir.name, "feature": mean_vector})

    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "version": "1.0",
        "threshold": args.threshold,
        "feature_description": "RGB mean/std + 8-bin normalized histogram for each channel. Total length = 30.",
        "entries": entries,
    }
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved {out_path} with {len(entries)} species.")


if __name__ == "__main__":
    main()
