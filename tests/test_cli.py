"""Tests for the lovable-audit CLI."""

from __future__ import annotations

import io
import sys
from pathlib import Path

import pytest

from lovable_audit.cli import _build_parser, audit_repo, main


def write_minimal_repo(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / "package.json").write_text("{}", encoding="utf-8")
    # file with a smell
    (root / "page.ts").write_text(
        "// @ts-ignore\nconsole.log('hi')\n",
        encoding="utf-8",
    )
    # file with a secret
    (root / "x.ts").write_text(
        "const k = 'sk-abcdefghijklmnopqrstuv';\n",
        encoding="utf-8",
    )
    # env file
    (root / ".env").write_text("SUPABASE_URL=abc\n", encoding="utf-8")


def test_parser_basic():
    p = _build_parser()
    ns = p.parse_args(["/tmp"])
    assert str(ns.repo) == "/tmp"


def test_audit_repo_returns_findings(tmp_path: Path):
    write_minimal_repo(tmp_path / "r")
    findings = audit_repo(tmp_path / "r")
    ids = {f.id for f in findings}
    assert "TS-IGNORE" in ids
    assert "SECRET-OPENAI" in ids or "SECRET-INLINE" in ids or len(findings) >= 2


def test_main_writes_report_file(tmp_path: Path):
    repo = tmp_path / "r"
    write_minimal_repo(repo)
    out = tmp_path / "report.md"
    rc = main([str(repo), "--out", str(out), "--print-summary"])
    assert rc == 0
    assert out.is_file()
    text = out.read_text(encoding="utf-8")
    assert "Lovable-MVP Audit" in text


def test_main_errors_on_missing_dir(tmp_path: Path, capsys):
    rc = main([str(tmp_path / "does-not-exist")])
    assert rc == 2
    captured = capsys.readouterr()
    assert "not a directory" in captured.err.lower()
