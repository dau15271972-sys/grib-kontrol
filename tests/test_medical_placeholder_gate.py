from pathlib import Path

from scripts.medical_placeholder_gate import (
    CONTENT_FILES,
    PLACEHOLDER_MARKER,
    main,
    validate_markers,
)

ROOT = Path(__file__).resolve().parent.parent


def test_medical_placeholder_is_explicit_on_every_emergency_surface() -> None:
    assert validate_markers(ROOT) == []
    for relative_path in CONTENT_FILES:
        assert PLACEHOLDER_MARKER in (ROOT / relative_path).read_text(encoding="utf-8")


def test_production_mode_is_blocked(monkeypatch) -> None:
    monkeypatch.setattr(
        "sys.argv",
        ["medical_placeholder_gate.py", "--root", str(ROOT), "--production"],
    )

    assert main() == 1
