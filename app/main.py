from __future__ import annotations

import os
from pathlib import Path

from flask import Flask, jsonify, render_template, request

from app.recognizer import MushroomRecognizer


BASE_DIR = Path(__file__).resolve().parent.parent
KNOWLEDGE_PATH = BASE_DIR / "data" / "knowledge_base.json"
RECOGNITION_PATH = BASE_DIR / "data" / "recognition_index.json"


def create_app() -> Flask:
    app = Flask(__name__, template_folder=str(BASE_DIR / "templates"))
    app.config["MAX_CONTENT_LENGTH"] = 12 * 1024 * 1024  # 12 MB
    app.config["UPLOAD_EXTENSIONS"] = {".jpg", ".jpeg", ".png", ".webp"}

    recognizer = MushroomRecognizer(
        knowledge_path=KNOWLEDGE_PATH,
        recognition_path=RECOGNITION_PATH,
    )

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.post("/predict")
    def predict():
        uploaded = request.files.get("photo")
        if not uploaded or uploaded.filename is None or not uploaded.filename.strip():
            return render_template("index.html", error="Загрузите фотографию гриба.")

        ext = Path(uploaded.filename).suffix.lower()
        if ext not in app.config["UPLOAD_EXTENSIONS"]:
            return render_template("index.html", error="Поддерживаются JPG, PNG, WEBP.")

        image_bytes = uploaded.read()
        try:
            result = recognizer.predict(image_bytes)
        except Exception as exc:  # defensive message for UI
            return render_template(
                "index.html",
                error=f"Не удалось обработать изображение: {exc}",
            )

        return render_template("index.html", result=result)

    @app.post("/api/predict")
    def api_predict():
        uploaded = request.files.get("photo")
        if not uploaded or uploaded.filename is None or not uploaded.filename.strip():
            return jsonify({"error": "Загрузите фотографию гриба."}), 400

        ext = Path(uploaded.filename).suffix.lower()
        if ext not in app.config["UPLOAD_EXTENSIONS"]:
            return jsonify({"error": "Поддерживаются JPG, PNG, WEBP."}), 400

        image_bytes = uploaded.read()
        try:
            result = recognizer.predict(image_bytes)
        except Exception as exc:
            return jsonify({"error": f"Не удалось обработать изображение: {exc}"}), 500

        return jsonify(result)

    return app


app = create_app()


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    app.run(host="0.0.0.0", port=port, debug=True)
