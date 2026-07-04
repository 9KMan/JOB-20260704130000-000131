#!/usr/bin/env python3
"""Quick stack-verification script.

Confirms:
  - Python version >= 3.11
  - the `lovable-audit` CLI is importable
  - pytest collects tests successfully
  - the fixture exists and is valid

Exits non-zero on any failure.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
FIXTURE = ROOT / "fixtures" / "sample_lovable_repo"


def banner(msg: str) -> None:
    print(f"[verify-stack] {msg}")


def main() -> int:
    failures: list[str] = []

    if sys.version_info < (3, 11):
        failures.append(f"need Python 3.11+, got {sys.version_info[:2]}")

    try:
        import lovable_audit  # noqa: F401
    except Exception as exc:  # pragma: no cover
        failures.append(f"lovable_audit import failed: {exc!r}")

    if not FIXTURE.is_dir():
        failures.append(f"fixture missing: {FIXTURE}")
    else:
        for required in ("package.json", "app/page.tsx", "app/api/things/route.ts", ".env"):
            if not (FIXTURE / required).exists():
                failures.append(f"fixture missing file: {required}")

    # pytest collect-only
    if shutil.which("pytest") is not None:
        try:
            res = subprocess.run(
                [sys.executable, "-m", "pytest", "--collect-only", "-q"],
                cwd=str(ROOT), capture_output=True, text=True, timeout=60,
            )
            if res.returncode != 0:
                failures.append(f"pytest collect-only failed: {res.stderr.strip()[:400]}")
            else:
                banner(f"pytest collects tests OK ({res.stdout.strip().splitlines()[-1]})")
        except Exception as exc:
            failures.append(f"could not run pytest: {exc!r}")
    else:
        banner("pytest not installed; skipping collect-only check")

    if failures:
        banner("FAILED")
        for f in failures:
            print(f"  - {f}")
        return 1
    banner("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
