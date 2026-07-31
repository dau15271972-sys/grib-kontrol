from pathlib import Path

from scripts.safety_gate import find_forbidden_phrases

ROOT = Path(__file__).resolve().parent.parent
PREVIEW = ROOT / "android_preview.html"
ANDROID_UI = (
    ROOT
    / "android-app/app/src/main/java/com/mushroom/detector/MushroomScreen.kt"
)


def test_approved_visual_assets_and_reference_are_preserved() -> None:
    assert PREVIEW.is_file()
    assert (ROOT / "assets/karelia-bg-2.jpg").stat().st_size > 0
    assert (ROOT / "assets/karelia-bg.webp").stat().st_size > 0

    preview = PREVIEW.read_text(encoding="utf-8")
    assert 'url("assets/karelia-bg-2.jpg")' in preview
    assert 'url("assets/karelia-bg.webp")' in preview
    assert "ГРИБ КОНТРОЛЬ" in preview


def test_android_ui_keeps_approved_design_contract() -> None:
    source = ANDROID_UI.read_text(encoding="utf-8")

    assert '"karelia-bg-2.jpg"' in source
    assert '"karelia-bg.webp"' in source
    assert '"ГРИБ КОНТРОЛЬ"' in source
    assert "verticalScroll" in source
    assert "RoundedCornerShape" in source


def test_design_reference_contains_no_forbidden_result_copy() -> None:
    assert find_forbidden_phrases(ROOT) == []
