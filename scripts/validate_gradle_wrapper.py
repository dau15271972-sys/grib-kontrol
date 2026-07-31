from __future__ import annotations

import hashlib
from pathlib import Path

EXPECTED_JAR_SHA256 = "cb0da6751c2b753a16ac168bb354870ebb1e162e9083f116729cec9c781156b8"
EXPECTED_DISTRIBUTION_SHA256 = (
    "544c35d6bd849ae8a5ed0bcea39ba677dc40f49df7d1835561582da2009b961d"
)
EXPECTED_DISTRIBUTION_URL = (
    "distributionUrl=https\\://services.gradle.org/distributions/gradle-8.7-bin.zip"
)


def validate(root: Path) -> list[str]:
    errors: list[str] = []
    wrapper_root = root / "android-app"
    jar_path = wrapper_root / "gradle" / "wrapper" / "gradle-wrapper.jar"
    properties_path = (
        wrapper_root / "gradle" / "wrapper" / "gradle-wrapper.properties"
    )
    for path in (wrapper_root / "gradlew", wrapper_root / "gradlew.bat", jar_path):
        if not path.is_file():
            errors.append(f"missing wrapper file: {path.relative_to(root)}")

    if jar_path.is_file():
        digest = hashlib.sha256(jar_path.read_bytes()).hexdigest()
        if digest != EXPECTED_JAR_SHA256:
            errors.append(f"unexpected gradle-wrapper.jar SHA-256: {digest}")

    if not properties_path.is_file():
        errors.append("missing gradle-wrapper.properties")
    else:
        properties = properties_path.read_text(encoding="utf-8")
        if EXPECTED_DISTRIBUTION_URL not in properties:
            errors.append("unexpected Gradle distribution URL")
        checksum_line = f"distributionSha256Sum={EXPECTED_DISTRIBUTION_SHA256}"
        if checksum_line not in properties:
            errors.append("missing or unexpected Gradle distribution SHA-256")
    return errors


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    errors = validate(root)
    if errors:
        print("\n".join(errors))
        return 1
    print("Gradle Wrapper files and checksums are valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
