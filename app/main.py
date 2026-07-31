from __future__ import annotations

import os
from pathlib import Path

from flask import Flask, jsonify, render_template, request

from app.inference import NoModelInferenceEngine, SafeInferenceRunner

BASE_DIR = Path(__file__).resolve().parent.parent


def create_app() -> Flask:
    app = Flask(__name__, template_folder=str(BASE_DIR / "templates"))
    app.config["MAX_CONTENT_LENGTH"] = 12 * 1024 * 1024  # 12 MB
    inference_runner = SafeInferenceRunner(
        NoModelInferenceEngine(),
    )

    @app.get("/")
    def index():
        return render_template(
            "index.html",
            result=inference_runner.infer().to_dict(),
        )

    @app.post("/predict")
    def predict():
        uploaded = request.files.get("photo")
        image_bytes = uploaded.read() if uploaded else None
        result = inference_runner.infer(image_bytes)
        return render_template("index.html", result=result.to_dict())

    @app.post("/api/predict")
    def api_predict():
        uploaded = request.files.get("photo")
        image_bytes = uploaded.read() if uploaded else None
        result = inference_runner.infer(image_bytes)
        if result.status.value == "TECHNICAL_FAILURE":
            return jsonify(result.to_dict()), 500

        return jsonify(result.to_dict()), 503

    @app.get("/emergency")
    def emergency():
        return render_template("emergency.html")

    return app


app = create_app()


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    app.run(host="127.0.0.1", port=port, debug=False)
