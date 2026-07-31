from __future__ import annotations

import argparse
from pathlib import Path

PLACEHOLDER_MARKER = "UNAPPROVED_MEDICAL_PLACEHOLDER"
CONTENT_FILES = (
    Path("templates/emergency.html"),
    Path(
        "android-app/app/src/main/java/com/mushroom/detector/"
        "emergency/EmergencyContent.kt"
    ),
)


def validate_markers(root: Path) -> list[str]:
    failures: list[str] = []
    for relative_path in CONTENT_FILES:
        path = root / relative_path
        if not path.is_file():
            failures.append(f"missing medical content file: {relative_path}")
            continue
        if PLACEHOLDER_MARKER not in path.read_text(encoding="utf-8"):
            failures.append(f"missing unapproved marker: {relative_path}")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(
        description="SAFETY: validate or block unapproved emergency copy."
    )
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--production", action="store_true")
    args = parser.parse_args()

    failures = validate_markers(args.root.resolve())
    if failures:
        print("\n".join(failures))
        return 1
    if args.production:
        print(
            "SAFETY: production release blocked: emergency medical copy "
            "is UNAPPROVED_MEDICAL_PLACEHOLDER."
        )
        return 1
    print("Medical placeholder markers are explicit; development build is allowed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
