"""Tests for the rule-based risk patterns detector."""

from __future__ import annotations

from pathlib import Path

import pytest

from lovable_audit.risk_patterns import (
    Finding,
    detect_error_swallowing,
    detect_heavy_ui_components,
    detect_missing_tests,
    detect_typescript_smells,
    scan_file,
)


SAMPLE_TSX = """
import { useState } from "react";
import { createClient } from "@supabase/supabase-js";
import axios from "axios";

export const supabase = createClient("x", "y");

export function Page() {
    const [x, setX] = useState(0);

    // comments and lots of filler to push us past the 250-line heuristic
    // so the data-in-UI detector is irrelevant here; this file stays short
    // by design.
    return <div>{x}</div>;
}
"""


# ---------- typescript smells ------------------------------------------------

def test_detects_ts_any_in_type_position():
    text = "function f(x: any) { return x; }"
    findings = detect_typescript_smells(text, "f.ts")
    ids = [f.id for f in findings]
    assert "TS-ANY" in ids
    assert any(f.severity == "medium" for f in findings)


def test_ignores_ts_any_in_identifier_like_contexts():
    # identifier containing "any" shouldn't trip the detector (no type punctuation)
    text = "const any_thing = 1; function many() { return 1; }"
    findings = detect_typescript_smells(text, "f.ts")
    assert not [f for f in findings if f.id == "TS-ANY"]


def test_detects_ts_ignore():
    text = "// @ts-ignore\nconst x: number = 's';\n"
    findings = detect_typescript_smells(text, "f.ts")
    assert any(f.id == "TS-IGNORE" for f in findings)


def test_detects_console_log():
    text = "console.log('hi'); console.info('x');"
    findings = detect_typescript_smells(text, "f.ts")
    assert any(f.id == "CONSOLE-LOG" for f in findings)


def test_detects_todo_marker():
    text = "// TODO: refactor this"
    findings = detect_typescript_smells(text, "f.ts")
    assert any(f.id == "TODO" for f in findings)


# ---------- error swallowing ------------------------------------------------

def test_detects_empty_catch():
    text = "try { foo(); } catch (e) {}"
    findings = detect_error_swallowing(text, "f.ts")
    assert any(f.id == "ERR-SWALLOW" for f in findings)


def test_detects_catch_console_only():
    text = "try { foo(); } catch (e) { console.error(e); }"
    findings = detect_error_swallowing(text, "f.ts")
    assert any(f.id == "ERR-CONSOLE" for f in findings)


def test_ignores_catch_with_logical_body():
    text = "try { foo(); } catch (e) { reportToSentry(e); throw e; }"
    findings = detect_error_swallowing(text, "f.ts")
    assert not findings


# ---------- data-in-UI heuristic --------------------------------------------

def test_detects_db_plus_state_in_long_tsx():
    # build a 260-line TSX with state + supabase import
    lines = ["// filler"] * 260
    text = SAMPLE_TSX + "\n" + "\n".join(lines) + "\n"
    findings = detect_heavy_ui_components(text, "page.tsx")
    assert any(f.id == "ARCH-UI-DATA" for f in findings)


def test_ignores_short_tsx():
    findings = detect_heavy_ui_components(SAMPLE_TSX, "page.tsx")
    assert not findings


def test_ignores_non_jsx_files():
    text = SAMPLE_TSX + "\n" + ("// filler\n" * 300)
    findings = detect_heavy_ui_components(text, "page.ts")  # not tsx
    assert not findings


# ---------- missing tests heuristic -----------------------------------------

def test_reports_missing_test_for_uncoupled_source(tmp_repo: Path):
    (tmp_repo / "a.ts").write_text("export const a = 1;", encoding="utf-8")
    (tmp_repo / "__tests__").mkdir()
    findings = detect_missing_tests([tmp_repo / "a.ts"], tmp_repo, tmp_repo / "__tests__")
    assert any(f.id == "TEST-MISSING" for f in findings)


def test_does_not_report_when_test_exists(tmp_repo: Path):
    (tmp_repo / "a.ts").write_text("export const a = 1;", encoding="utf-8")
    tests = tmp_repo / "__tests__"
    tests.mkdir()
    (tests / "a.test.ts").write_text("test('a', () => {});", encoding="utf-8")
    findings = detect_missing_tests([tmp_repo / "a.ts"], tmp_repo, tests)
    assert not findings


def test_skips_index_utils_config(tmp_repo: Path):
    # detector should not bombard us with findings for trivial stubs
    for name in ("index.ts", "utils.ts", "config.ts", "types.ts"):
        (tmp_repo / name).write_text("export const x = 1;\n", encoding="utf-8")
    (tmp_repo / "__tests__").mkdir()
    findings = detect_missing_tests([tmp_repo / n for n in ("index.ts",)], tmp_repo, tmp_repo / "__tests__")
    assert not findings


# ---------- top-level dispatch -----------------------------------------------

def test_scan_file_returns_finding_list(tmp_repo: Path):
    f = tmp_repo / "page.ts"
    f.write_text("// @ts-ignore\nconsole.log('x')\n", encoding="utf-8")
    findings = scan_file(f, tmp_repo)
    assert isinstance(findings, list)
    assert isinstance(findings[0], Finding)
