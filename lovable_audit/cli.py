"""lovable_audit CLI — `lovable-audit <repo-path>`."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .report import render
from .risk_patterns import scan_file as scan_risk_file
from .risk_patterns import detect_missing_tests
from .security_checks import scan_repo as scan_security
from .architecture_checks import scan_repo as scan_architecture
from .test_coverage import scan_repo as scan_coverage


def _collect_source_files(repo: Path):
    ignore_dirs = {"node_modules", ".next", ".git", "dist", "build", "__pycache__", ".venv", "fixtures"}
    for p in repo.rglob("*"):
        if not p.is_file():
            continue
        if set(p.parts) & ignore_dirs:
            continue
        if p.suffix in {".ts", ".tsx", ".js", ".jsx", ".py"}:
            yield p


def audit_repo(repo: Path) -> list:
    """Run all detectors on a repo and return a merged list of findings."""
    findings: list = []
    for p in _collect_source_files(repo):
        findings.extend(scan_risk_file(p, repo))

    # missing-tests detector — uses src/test heuristics
    findings.extend(detect_missing_tests(_collect_source_files(repo), repo, repo / "__tests__"))
    findings.extend(detect_missing_tests(_collect_source_files(repo), repo, repo / "tests"))

    findings.extend(scan_security(repo))
    findings.extend(scan_architecture(repo))
    findings.extend(scan_coverage(repo))
    return findings


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="lovable-audit",
        description="Static audit for Next.js + Supabase + Lovable-style SaaS apps.",
    )
    p.add_argument("repo", type=Path, help="Path to the repository to audit.")
    p.add_argument("--out", type=Path, default=Path("report.md"),
                   help="Output Markdown file (default: report.md).")
    p.add_argument("--label", type=str, default=None,
                   help="Friendly label to show in the report header.")
    p.add_argument("--print-summary", action="store_true",
                   help="Also print a one-line summary to stdout.")
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return p


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    repo: Path = args.repo.resolve()
    if not repo.is_dir():
        print(f"error: {repo} is not a directory", file=sys.stderr)
        return 2

    findings = audit_repo(repo)
    md = render(findings, repo, repo_label=args.label)

    out: Path = args.out
    if not out.is_absolute():
        out = (Path.cwd() / out).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(md, encoding="utf-8")

    if args.print_summary:
        n_high = sum(1 for f in findings if f.severity == "high")
        print(f"wrote {out} — {len(findings)} findings ({n_high} high)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
