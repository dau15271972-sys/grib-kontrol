from pathlib import Path

from scripts.validate_gradle_wrapper import validate

ROOT = Path(__file__).resolve().parent.parent


def test_gradle_wrapper_files_and_checksums() -> None:
    assert validate(ROOT) == []
