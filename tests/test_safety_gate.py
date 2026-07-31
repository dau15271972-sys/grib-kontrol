from pathlib import Path

from scripts.safety_gate import (
    find_forbidden_android_permissions,
    find_forbidden_phrases,
    find_unbound_models,
)

ROOT = Path(__file__).resolve().parent.parent


def test_production_ui_has_no_forbidden_phrases() -> None:
    assert find_forbidden_phrases(ROOT) == []


def test_repository_has_no_unbound_model_assets() -> None:
    assert find_unbound_models(ROOT) == []


def test_android_has_no_network_or_location_permissions() -> None:
    assert find_forbidden_android_permissions(ROOT) == []
