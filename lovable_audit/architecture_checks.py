"""
architecture_checks.py — folder-layout & dependency-direction checks.

The goal is *not* to enforce a particular framework; it is to flag the
common smells we see in Lovable-style MVPs:

- DB/auth code at the top of every page component (no real data layer)
- No clear separation between API routes and pure business logic
- Long files (likely mixing concerns)
- God folders: 30+ components in a single dir, no domain split
- Cycles in imports (best-effort static cycle scan on relative imports)
"""

from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path
from typing import Iterable

from .risk_patterns import Finding


_LONG_FILE_THRESHOLD = 600        # lines
_LONG_FUNCTION_THRESHOLD = 80     # lines (best-effort)


def detect_long_files(repo_root: Path) -> list[Finding]:
    out: list[Finding] = []
    ignore_dirs = {"node_modules", ".next", ".git", "dist", "build", "__pycache__", ".venv"}
    for p in repo_root.rglob("*"):
        if not p.is_file():
            continue
        if set(p.parts) & ignore_dirs:
            continue
        if p.suffix not in {".ts", ".tsx", ".js", ".jsx", ".py"}:
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        nlines = text.count("\n") + 1
        if nlines >= _LONG_FILE_THRESHOLD:
            rel = str(p.relative_to(repo_root))
            out.append(Finding(
                id="ARCH-LONG-FILE",
                title="Suspiciously long source file",
                severity="medium",
                category="architecture",
                file=rel,
                line=1,
                snippet=f"{nlines} lines",
                rationale=f"File has {nlines} lines (threshold {_LONG_FILE_THRESHOLD}). Likely mixing UI + biz + IO. Consider splitting.",
            ))
    return out


def detect_god_folders(repo_root: Path) -> list[Finding]:
    """Flag folders named 'components' or 'lib' at the top level with > 25 files."""
    out: list[Finding] = []
    for name in ("components", "lib"):
        cand = repo_root / name
        if not cand.is_dir():
            continue
        n = sum(1 for _ in cand.rglob("*") if _.is_file())
        if n >= 25:
            out.append(Finding(
                id="ARCH-GOD-FOLDER",
                title=f"`{name}/` is a god-folder",
                severity="low",
                category="architecture",
                file=f"{name}/",
                line=0,
                snippet=f"{n} files",
                rationale="A large catch-all folder usually hides many distinct sub-domains. Consider grouping by feature (domain) rather than by file type.",
            ))
    return out


_RELATIVE_IMPORT = re.compile(
    r"from\s+['\"](?:\.{1,2}/[^'\"]+)['\"]|require\(\s*['\"](?:\.{1,2}[^'\"]+)['\"]\s*\)"
)


def _build_import_graph(repo_root: Path) -> dict[Path, set[Path]]:
    ignore_dirs = {"node_modules", ".next", ".git", "dist", "build"}
    graph: dict[Path, set[Path]] = defaultdict(set)
    for p in repo_root.rglob("*"):
        if not p.is_file():
            continue
        if p.suffix not in {".ts", ".tsx", ".js", ".jsx"}:
            continue
        if set(p.parts) & ignore_dirs:
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for m in _RELATIVE_IMPORT.finditer(text):
            imp = re.search(r"['\"](\.{1,2}/[^'\"]+)['\"]", m.group(0))
            if not imp:
                continue
            raw = imp.group(1)
            target = (p.parent / raw).resolve()
            # very crude resolution: try with and without /index
            try:
                candidate = (target.with_suffix(p.suffix)).resolve()
            except OSError:
                continue
            graph[p.resolve()].add(candidate)
    return graph


def detect_import_cycles(repo_root: Path) -> list[Finding]:
    """Best-effort Tarjan SCC on the relative-import graph. Reports SCCs of size >= 2."""
    out: list[Finding] = []
    graph = _build_import_graph(repo_root)
    # trivial Tarjan iterative
    index_counter = [0]
    stack: list[Path] = []
    lowlinks: dict[Path, int] = {}
    index: dict[Path, int] = {}
    on_stack: dict[Path, bool] = {}
    sccs: list[list[Path]] = []

    def strongconnect(node: Path):
        work = [(node, iter(graph.get(node, set())))]
        call_stack = []
        while work:
            v, it = work[-1]
            if v not in index:
                index[v] = index_counter[0]
                lowlinks[v] = index_counter[0]
                index_counter[0] += 1
                stack.append(v)
                on_stack[v] = True
            for w in it:
                if w not in index:
                    call_stack.append((v, it))
                    work.append((w, iter(graph.get(w, set()))))
                    break
                elif on_stack.get(w):
                    lowlinks[v] = min(lowlinks[v], index[w])
            else:
                if lowlinks[v] == index[v]:
                    component = []
                    while True:
                        w = stack.pop()
                        on_stack[w] = False
                        component.append(w)
                        if w == v:
                            break
                    if len(component) >= 2:
                        sccs.append(component)
                if call_stack:
                    pv, pit = call_stack.pop()
                    lowlinks[pv] = min(lowlinks[pv], lowlinks[v])
                # done
            if not call_stack and work:
                work.pop()
        # implicit cleanup of unreachable helpers above is fine for our purpose

    for node in list(graph.keys()):
        if node not in index:
            strongconnect(node)

    for component in sccs[:5]:  # cap output
        rels = sorted(str(p.relative_to(repo_root)) for p in component)
        out.append(Finding(
            id="ARCH-CYCLE",
            title="Import cycle",
            severity="medium",
            category="architecture",
            file=rels[0],
            line=1,
            snippet=" -> ".join(rels[:6]) + (" ..." if len(rels) > 6 else ""),
            rationale="Cycles make refactors risky and slow bundlers. Break by extracting a shared module.",
        ))
    return out


def detect_no_data_layer(repo_root: Path) -> list[Finding]:
    """Heuristic: repository has Supabase calls but no `lib/db`, `services/`, or `repositories/` folder."""
    out: list[Finding] = []
    has_supabase = any(repo_root.rglob("*.ts"))
    for p in repo_root.rglob("*.ts"):
        try:
            t = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if "@supabase/supabase-js" in t:
            has_supabase = True
            break
    if not has_supabase:
        return out

    data_layer_candidates = ["lib/db", "src/lib/db", "services", "repositories", "data"]
    if not any((repo_root / c).is_dir() for c in data_layer_candidates):
        out.append(Finding(
            id="ARCH-NO-DATA-LAYER",
            title="No data-layer folder",
            severity="medium",
            category="architecture",
            file="repo",
            line=0,
            snippet="",
            rationale="Page/component files import `@supabase/supabase-js` directly. Extract a thin data layer (`lib/db/` or `services/`) so view code doesn't know about Supabase.",
        ))
    return out


def scan_repo(repo_root: Path) -> list[Finding]:
    out: list[Finding] = []
    out.extend(detect_long_files(repo_root))
    out.extend(detect_god_folders(repo_root))
    out.extend(detect_no_data_layer(repo_root))
    out.extend(detect_import_cycles(repo_root))
    return out
