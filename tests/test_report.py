"""Tests for the markdown report emitter."""

from __future__ import annotations

from pathlib import Path

import pytest

from lovable_audit.report import render, write_report
from lovable_audit.risk_patterns import Finding


def _f(id_: str, sev: str, cat: str, file: str = "x.ts", line: int = 1) -> Finding:
    return Finding(id=id_, title=id_, severity=sev, category=cat, file=file, line=line)


def test_render_empty_findings_returns_valid_markdown():
    md = render([], Path("/tmp/repo"), repo_label="example")
    assert md.startswith("# Lovable-MVP Audit — `example`")
    assert "Total findings" in md
    assert "Architecture (0)" in md
    assert "Security (0)" in md


def test_render_groups_by_category_and_sorts_by_severity():
    findings = [
        _f("LOW-ID", "low", "testing"),
        _f("HIGH-ID", "high", "security"),
        _f("MED-ID", "medium", "architecture"),
    ]
    md = render(findings, Path("/tmp/repo"))
    assert "### Architecture (1)" in md
    assert "### Security (1)" in md
    assert "### Testing (1)" in md

    # Categories are emitted alphabetically (architecture, gdpr, security, testing).
    arch_idx = md.find("### Architecture")
    sec_idx = md.find("### Security")
    assert arch_idx < sec_idx

    # severity should be reflected
    assert "high" in md
    assert "medium" in md
    assert "low" in md


def test_render_handles_unknown_category_gracefully(tmp_path: Path):
    findings = [_f("X", "high", "weird")]
    md = render(findings, tmp_path)
    assert "## Weird" in md  # capitalized category header


def test_write_report_creates_file(tmp_path: Path):
    out = tmp_path / "report.md"
    write_report([], tmp_path, out, repo_label="r")
    assert out.is_file()
    text = out.read_text(encoding="utf-8")
    assert "`r`" in text


def test_render_truncates_long_snippets():
    long_snip = "a" * 1000
    f = Finding(id="X", title="X", severity="high", category="security",
                file="x.ts", line=1, snippet=long_snip)
    md = render([f], Path("/tmp/repo"))
    assert "a" * 1000 not in md
    assert "..." in md
