from __future__ import annotations

import argparse
from pathlib import Path

FORBIDDEN_UI_PHRASES = (
    "можно есть",
    "безопасно есть",
    "безопасно употреблять",
    "гриб безопасен",
    "съедобный гриб",
    "ядовитых двойников нет",
    "гриб точно определён",
    "можно собирать",
    "можно готовить",
)
MODEL_SUFFIXES = {
    ".bin",
    ".gribpack",
    ".lite",
    ".onnx",
    ".pt",
    ".pth",
    ".tflite",
}
IGNORED_PARTS = {
    ".git",
    ".gradle",
    ".runtime_tmp",
    ".tmp",
    ".venv",
    "__pycache__",
    "build",
    "dist",
}
UI_ROOTS = (
    Path("android_preview.html"),
    Path("app"),
    Path("templates"),
    Path("android-app/app/src/main/java"),
    Path("android-app/app/src/main/res"),
)
TEXT_SUFFIXES = {".html", ".kt", ".py", ".xml"}
FORBIDDEN_ANDROID_PERMISSIONS = {
    "android.permission.ACCESS_COARSE_LOCATION",
    "android.permission.ACCESS_FINE_LOCATION",
    "android.permission.INTERNET",
}


def find_forbidden_phrases(root: Path) -> list[str]:
    findings: list[str] = []
    for relative_root in UI_ROOTS:
        source_root = root / relative_root
        if not source_root.exists():
            continue
        paths = (source_root,) if source_root.is_file() else source_root.rglob("*")
        for path in paths:
            if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
                continue
            text = path.read_text(encoding="utf-8").lower()
            for phrase in FORBIDDEN_UI_PHRASES:
                if phrase in text:
                    findings.append(f"{path.relative_to(root)}: {phrase}")
    return findings


def find_unbound_models(root: Path) -> list[str]:
    return sorted(
        str(path.relative_to(root))
        for path in root.rglob("*")
        if path.is_file()
        and path.suffix.lower() in MODEL_SUFFIXES
        and not IGNORED_PARTS.intersection(path.relative_to(root).parts)
    )


def find_forbidden_android_permissions(root: Path) -> list[str]:
    manifest = root / "android-app/app/src/main/AndroidManifest.xml"
    if not manifest.is_file():
        return ["AndroidManifest.xml is missing"]
    text = manifest.read_text(encoding="utf-8")
    return sorted(permission for permission in FORBIDDEN_ANDROID_PERMISSIONS if permission in text)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run repository safety source gates.")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    root = args.root.resolve()

    failures = [
        *(f"forbidden UI phrase: {item}" for item in find_forbidden_phrases(root)),
        *(f"unbound model asset: {item}" for item in find_unbound_models(root)),
        *(
            f"forbidden Android permission: {item}"
            for item in find_forbidden_android_permissions(root)
        ),
    ]
    if failures:
        print("\n".join(failures))
        return 1
    print("Safety source gates passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
