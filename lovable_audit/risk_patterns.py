"""
risk_patterns.py — rule-based code-smell detectors.

Each detector scans a single file's text and returns a list of
:class:`Finding` records. The detectors are intentionally simple and
regex/AST-light so they can run on a repo without a compiled project,
are easy to audit themselves, and produce reproducible output across
runs.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


@dataclass
class Finding:
    """A single risk finding."""
    id: str
    title: str
    severity: str  # "high" | "medium" | "low"
    category: str  # "architecture" | "security" | "testing" | "gdpr"
    file: str
    line: int
    snippet: str = ""
    rationale: str = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "severity": self.severity,
            "category": self.category,
            "file": self.file,
            "line": self.line,
            "snippet": self.snippet,
            "rationale": self.rationale,
        }


# ---------- helpers ----------------------------------------------------------

# Files we are willing to scan for code-smells. Tokens are intentionally narrow.
_SOURCE_EXTS = {".ts", ".tsx", ".js", ".jsx", ".py", ".rb", ".go"}


def _is_source(path: Path) -> bool:
    return path.suffix in _SOURCE_EXTS


def _line_of(text: str, offset: int) -> int:
    """Return 1-based line number for byte/char offset."""
    return text.count("\n", 0, offset) + 1


def _strip_for_match(text: str, start: int, end: int) -> tuple[str, str]:
    """Return (one-line-snippet, optional-context)."""
    line_start = text.rfind("\n", 0, start) + 1
    line_end = text.find("\n", end)
    if line_end == -1:
        line_end = len(text)
    snippet = text[line_start:line_end].strip()
    if len(snippet) > 200:
        snippet = snippet[:197] + "..."
    return snippet, ""


# ---------- detector: `any`/Ts-ignore/etc ------------------------------------

_TS_ANY = re.compile(r"\bany\b")
_TS_IGNORE = re.compile(r"@(ts-ignore|ts-expect-error|ts-nocheck)")
_CONSOLE_LOG = re.compile(r"\bconsole\.(log|debug|info|warn)\s*\(")
_TODO = re.compile(r"\b(TODO|FIXME|XXX|HACK)\b")


def detect_typescript_smells(text: str, filename: str) -> list[Finding]:
    out: list[Finding] = []
    for m in _TS_ANY.finditer(text):
        # only flag `any` in a type position-ish (heuristic: looks like ": any",
        # "<any>", "as any", "(any", ", any", "= any"). Reduce noise from
        # identifiers containing "any".
        look_back = 6
        prefix = text[max(0, m.start() - look_back):m.start()]
        suffix = text[m.end():m.end() + 2]
        stripped = prefix.rstrip()
        if (
            stripped.endswith(":")
            or stripped.endswith("<")
            or stripped.endswith("(")
            or stripped.endswith(",")
            or stripped.endswith("=")
            or stripped.endswith("as")
            or suffix.startswith(">")
        ):
            snippet, _ = _strip_for_match(text, m.start(), m.end())
            out.append(Finding(
                id="TS-ANY",
                title="TypeScript `any` usage",
                severity="medium",
                category="architecture",
                file=filename,
                line=_line_of(text, m.start()),
                snippet=snippet,
                rationale="`any` defeats the type system and hides bugs; widen specific types instead.",
            ))

    for m in _TS_IGNORE.finditer(text):
        snippet, _ = _strip_for_match(text, m.start(), m.end())
        out.append(Finding(
            id="TS-IGNORE",
            title="TypeScript error suppression",
            severity="medium",
            category="architecture",
            file=filename,
            line=_line_of(text, m.start()),
            snippet=snippet,
            rationale="`@ts-ignore`/`@ts-expect-error` hide genuine type errors; prefer `// @ts-expect-error: <reason>` with a comment.",
        ))

    for m in _CONSOLE_LOG.finditer(text):
        snippet, _ = _strip_for_match(text, m.start(), m.end())
        out.append(Finding(
            id="CONSOLE-LOG",
            title="console.log in shipped code",
            severity="low",
            category="architecture",
            file=filename,
            line=_line_of(text, m.start()),
            snippet=snippet,
            rationale="Console statements leak implementation details in production; gate behind a debug flag or remove.",
        ))

    for m in _TODO.finditer(text):
        snippet, _ = _strip_for_match(text, m.start(), m.end())
        out.append(Finding(
            id="TODO",
            title="Unresolved TODO/FIXME marker",
            severity="low",
            category="architecture",
            file=filename,
            line=_line_of(text, m.start()),
            snippet=snippet,
            rationale="TODOs indicate incomplete work; ensure none are shipped to production without an associated ticket.",
        ))
    return out


# ---------- detector: error swallowing --------------------------------------

_EMPTY_CATCH = re.compile(
    r"catch\s*\([^)]*\)\s*\{\s*\}",
    re.MULTILINE,
)
_CATCH_CONSOLE = re.compile(
    r"catch\s*\([^)]*\)\s*\{[^}]*console\.(error|log|warn)[^}]*\}",
    re.MULTILINE | re.DOTALL,
)


def detect_error_swallowing(text: str, filename: str) -> list[Finding]:
    out: list[Finding] = []
    for m in _EMPTY_CATCH.finditer(text):
        snippet, _ = _strip_for_match(text, m.start(), m.end())
        out.append(Finding(
            id="ERR-SWALLOW",
            title="Empty catch block",
            severity="high",
            category="architecture",
            file=filename,
            line=_line_of(text, m.start()),
            snippet=snippet,
            rationale="Empty catch blocks hide failures; at minimum log to a structured logger and rethrow or surface a UI error.",
        ))
    for m in _CATCH_CONSOLE.finditer(text):
        snippet, _ = _strip_for_match(text, m.start(), m.end())
        out.append(Finding(
            id="ERR-CONSOLE",
            title="Catch logs to console only",
            severity="medium",
            category="architecture",
            file=filename,
            line=_line_of(text, m.start()),
            snippet=snippet,
            rationale="console.error leaves no audit trail; use a structured logger and/or error reporting (Sentry, etc.).",
        ))
    return out


# ---------- detector: business logic in UI components -----------------------

_UI_HINTS = re.compile(r"(\.tsx|\.jsx|/app/|/pages/|/components/)")

def detect_heavy_ui_components(text: str, filename: str) -> list[Finding]:
    """Heuristic: a JSX/TSX file that contains DB client or fetch + state."""
    if not filename.endswith((".tsx", ".jsx")):
        return []
    out: list[Finding] = []

    has_db_import = bool(re.search(
        r"from\s+['\"](@supabase/supabase-js|@/lib/db|prisma|@prisma/client)['\"]", text
    ))
    has_fetch = "fetch(" in text or "axios" in text
    has_state = bool(re.search(r"useState\s*\(", text))
    lines = text.count("\n")

    if has_db_import and has_state and lines > 250:
        out.append(Finding(
            id="ARCH-UI-DATA",
            title="Data access in UI component",
            severity="medium",
            category="architecture",
            file=filename,
            line=1,
            snippet=f"~{lines} lines, DB client + useState",
            rationale="Long components that also touch DB/biz logic are hard to test. Extract data layer + pure view layer.",
        ))
    return out


# ---------- detector: missing tests -----------------------------------------

def detect_missing_tests(file_iter: Iterable[Path], src_root: Path, test_root: Path) -> list[Finding]:
    """For each source file under src, check whether a corresponding test exists."""
    out: list[Finding] = []
    test_files = set()
    if test_root.exists():
        for p in test_root.rglob("*"):
            if p.is_file():
                test_files.add(p.name)

    for p in file_iter:
        if not _is_source(p):
            continue
        rel = p.relative_to(src_root) if src_root in p.parents else p.name
        stem = p.stem

        candidates = [
            f"{stem}.test.ts",
            f"{stem}.test.tsx",
            f"{stem}.test.js",
            f"{stem}.spec.ts",
            f"{stem}.spec.tsx",
            f"{stem}.spec.js",
            f"test_{stem}.py",
            f"{stem}_test.py",
        ]
        if not any(c in test_files for c in candidates):
            # report only on a subset of files (not every utility)
            if stem in {"index", "utils", "config", "types"}:
                continue
            out.append(Finding(
                id="TEST-MISSING",
                title="No matching test file",
                severity="medium",
                category="testing",
                file=str(rel),
                line=0,
                snippet=stem,
                rationale="No companion test file. Add at least one happy-path test.",
            ))
    return out


# ---------- public API -------------------------------------------------------

def scan_file(path: Path, repo_root: Path) -> list[Finding]:
    """Run all applicable detectors on a single file."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except (OSError, UnicodeDecodeError):
        return []
    rel = str(path.relative_to(repo_root))
    out: list[Finding] = []
    out.extend(detect_typescript_smells(text, rel))
    out.extend(detect_error_swallowing(text, rel))
    out.extend(detect_heavy_ui_components(text, rel))
    return out
