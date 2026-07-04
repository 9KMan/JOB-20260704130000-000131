"""
test_coverage.py — best-effort test/coverage report from common coverage files.

Reads:
  - coverage/lcov.info (lcov)
  - coverage/coverage-final.json (Istanbul/NYC)
  - coverage.xml (Cobertura; used by many CI providers)

Reports uncovered line counts. Detector-only; does not run tests.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from .risk_patterns import Finding


@dataclass
class CoverageStats:
    source_files: int = 0
    covered_lines: int = 0
    total_lines: int = 0
    by_file: dict[str, dict[str, int]] = field(default_factory=dict)

    @property
    def pct(self) -> float:
        if self.total_lines == 0:
            return 0.0
        return 100.0 * self.covered_lines / self.total_lines


def _parse_lcov(text: str) -> CoverageStats:
    stats = CoverageStats()
    cur_file = None
    for line in text.splitlines():
        if line.startswith("SF:"):
            cur_file = line[3:].strip()
            stats.by_file[cur_file] = {"found": 0, "hit": 0}
            stats.source_files += 1
        elif line.startswith("LF:"):
            try:
                n = int(line[3:])
                stats.by_file.setdefault(cur_file or "", {"found": 0, "hit": 0})["found"] = n
                stats.total_lines += n
            except ValueError:
                pass
        elif line.startswith("LH:"):
            try:
                n = int(line[3:])
                stats.by_file.setdefault(cur_file or "", {"found": 0, "hit": 0})["hit"] = n
                stats.covered_lines += n
            except ValueError:
                pass
        elif line == "end_of_record":
            cur_file = None
    return stats


def _parse_nyc(text: str) -> CoverageStats:
    raw = json.loads(text)
    stats = CoverageStats()
    for path, data in raw.items():
        stmts = data.get("s", {}) or {}
        # NYC uses statement-map; stmt key -> execution count
        if not stmts:
            # older nyc format
            stmts = (data.get("statementMap") or {})
        hit = sum(1 for v in stmts.values() if isinstance(v, int) and v > 0)
        total = len(stmts)
        stats.by_file[path] = {"found": total, "hit": hit}
        stats.source_files += 1
        stats.covered_lines += hit
        stats.total_lines += total
    return stats


_COVERAGE_RE = re.compile(r"lines-covered=\"(?P<lc>\d+)\" lines-valid=\"(?P<lv>\d+)\"")


def _parse_cobertura(text: str) -> CoverageStats:
    stats = CoverageStats()
    for m in _COVERAGE_RE.finditer(text):
        lc = int(m.group("lc"))
        lv = int(m.group("lv"))
        stats.covered_lines += lc
        stats.total_lines += lv
        stats.source_files += 1
    return stats


def load_coverage(repo_root: Path) -> CoverageStats | None:
    candidates = [
        ("coverage/lcov.info", _parse_lcov),
        ("coverage/coverage-final.json", _parse_nyc),
        ("coverage.xml", _parse_cobertura),
        ("cobertura-coverage.xml", _parse_cobertura),
    ]
    for rel, parser in candidates:
        p = repo_root / rel
        if not p.is_file():
            continue
        try:
            return parser(p.read_text(encoding="utf-8", errors="replace"))
        except (OSError, ValueError, json.JSONDecodeError):
            continue
    return None


def evaluate(stats: CoverageStats | None, repo_root: Path) -> list[Finding]:
    out: list[Finding] = []
    if stats is None:
        out.append(Finding(
            id="TEST-NO-COV-REPORT",
            title="No coverage report found",
            severity="medium",
            category="testing",
            file="coverage/",
            line=0,
            snippet="",
            rationale="We couldn't find coverage/lcov.info, coverage/coverage-final.json, or coverage.xml. Ship a CI step that uploads one of these so risk can be tracked over time.",
        ))
        return out

    pct = stats.pct
    if pct < 50:
        sev = "high"
    elif pct < 70:
        sev = "medium"
    elif pct < 85:
        sev = "low"
    else:
        sev = "low"

    out.append(Finding(
        id="TEST-COV-PCT",
        title=f"Overall line coverage {pct:.1f}%",
        severity=sev if pct < 85 else "low",
        category="testing",
        file="coverage/",
        line=0,
        snippet=f"{stats.covered_lines}/{stats.total_lines} lines",
        rationale=("Aim for >=70% on business logic; 100% on auth/data-layer boundaries is realistic and worth it." if pct < 70 else "Coverage is healthy; keep an eye on regression of new code."),
    ))

    # flag the worst-covered files
    worst = sorted(
        ((f, d) for f, d in stats.by_file.items() if d.get("found", 0) > 0),
        key=lambda kv: (kv[1].get("hit", 0) / max(1, kv[1].get("found", 0))),
    )[:5]
    for f, d in worst:
        hit = d["hit"]
        total = d["found"]
        ratio = hit / max(1, total)
        if ratio >= 0.5:
            continue
        out.append(Finding(
            id="TEST-COV-LOW-FILE",
            title="Under-covered file",
            severity="medium",
            category="testing",
            file=f,
            line=0,
            snippet=f"{hit}/{total} lines ({ratio*100:.0f}%)",
            rationale="Worst-covered files deserve explicit test work before the next feature sprint.",
        ))
    return out


def scan_repo(repo_root: Path) -> list[Finding]:
    return evaluate(load_coverage(repo_root), repo_root)
