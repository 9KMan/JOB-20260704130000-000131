#!/usr/bin/env bash
# scripts/run_audit.sh — one-command demo on a sample bad-codebase fixture.
#
# Usage:
#   bash scripts/run_audit.sh           # audits fixtures/sample_lovable_repo
#
# Output:
#   report.md in the current working directory.
#
# Requirements: Python 3.11+ (no third-party deps required at runtime).

set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"

TARGET="${1:-$ROOT/fixtures/sample_lovable_repo}"
OUT="${2:-report.md}"

if [[ ! -d "$TARGET" ]]; then
  echo "Target repo not found: $TARGET" >&2
  exit 2
fi

PY="${PYTHON:-python3}"
if ! command -v "$PY" >/dev/null 2>&1; then
  echo "Python interpreter '$PY' not found on PATH" >&2
  exit 3
fi

echo "[run_audit] auditing $TARGET -> $OUT"
cd "$ROOT"
"$PY" -m lovable_audit.cli "$TARGET" --out "$OUT" --print-summary

echo
echo "[run_audit] top 10 lines of $OUT:"
head -n 20 "$OUT"
