from __future__ import annotations

from app.inference import InferenceResult, ResultStatus
from app.main import create_app


class FailingEngine:
    def infer(self, image_bytes: bytes | None = None) -> InferenceResult:
        del image_bytes
        raise RuntimeError("synthetic failure")


def test_api_fails_closed_without_model() -> None:
    client = create_app().test_client()

    response = client.post("/api/predict")
    payload = response.get_json()

    assert response.status_code == 503
    assert payload["status"] == ResultStatus.RECOGNITION_UNAVAILABLE
    assert payload["emergency_url"] == "/emergency"
    assert "confidence" not in payload
    assert "species_id" not in payload


def test_api_fails_closed_after_technical_error() -> None:
    client = create_app(FailingEngine()).test_client()

    response = client.post("/api/predict")
    payload = response.get_json()

    assert response.status_code == 500
    assert payload["status"] == ResultStatus.TECHNICAL_FAILURE
    assert payload["emergency_url"] == "/emergency"
    assert "confidence" not in payload


def test_emergency_screen_is_available_without_model() -> None:
    client = create_app().test_client()

    response = client.get("/emergency")

    assert response.status_code == 200
    assert "Экстренная помощь".encode() in response.data


def test_emergency_screen_is_available_after_technical_error() -> None:
    client = create_app(FailingEngine()).test_client()
    client.post("/api/predict")

    response = client.get("/emergency")

    assert response.status_code == 200
    assert "Экстренная помощь".encode() in response.data


def test_main_screen_fails_closed_after_technical_error() -> None:
    client = create_app(FailingEngine()).test_client()

    response = client.get("/")

    assert response.status_code == 200
    assert ResultStatus.TECHNICAL_FAILURE.value.encode() in response.data
