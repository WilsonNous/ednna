from __future__ import annotations

import os

from .conformance import SpecialistConformanceValidator
from .manifest import load_specialist_manifests


def main() -> int:
    path = os.getenv("SPECIALIST_MANIFEST_PATH", "").strip()
    if not path:
        print("SPECIALIST_MANIFEST_PATH is not configured.")
        return 1

    manifests = load_specialist_manifests(path)
    validator = SpecialistConformanceValidator()
    failed = False

    for manifest in manifests:
        report = validator.validate(manifest)
        status = "VALID" if report.valid else "INVALID"
        print(f"{report.specialist_id}: {status}")
        for issue in report.issues:
            print(f"- {issue.code}: {issue.message}")
        failed = failed or not report.valid

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
