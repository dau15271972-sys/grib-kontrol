from __future__ import annotations

import inspect

from app.inference import ResultStatus, technical_failure_result
from app.main import create_app


def test_api_fails_closed_without_model() -> None:
    client = create_app().test_client()

    response = client.post("/api/predict")
    payload = response.get_json()

    assert response.status_code == 503
    assert payload["status"] == ResultStatus.RECOGNITION_UNAVAILABLE
    assert payload["emergency_url"] == "/emergency"
    assert "confidence" not in payload
    assert "species_id" not in payload


def test_production_app_factory_has_no_engine_injection_path() -> None:
    assert inspect.signature(create_app).parameters == {}


def test_emergency_screen_is_available_without_model() -> None:
    client = create_app().test_client()

    response = client.get("/emergency")

    assert response.status_code == 200
    assert "Экстренная помощь".encode() in response.data


def test_emergency_screen_is_available_after_technical_error() -> None:
    failure = technical_failure_result()
    client = create_app().test_client()

    response = client.get("/emergency")

    assert failure.status is ResultStatus.TECHNICAL_FAILURE
    assert failure.emergency_url == "/emergency"
    assert response.status_code == 200
    assert "Экстренная помощь".encode() in response.data


def test_technical_failure_payload_does_not_expose_scores() -> None:
    payload = technical_failure_result().to_dict()

    assert "confidence" not in payload
    assert "distance" not in payload


def test_production_app_always_fails_closed_without_pack() -> None:
    client = create_app().test_client()

    response = client.post("/api/predict")
    payload = response.get_json()

    assert response.status_code == 503
    assert payload["status"] == ResultStatus.RECOGNITION_UNAVAILABLE
