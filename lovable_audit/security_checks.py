"""
security_checks.py — lightweight static security & privacy posture checks.

These are *not* a substitute for a proper SAST/DAST scan. They are guard-rails
that catch the most common mistakes in a Lovable/Next.js + Supabase MVP:

- Secret material hard-coded in source
- `.env` files committed to the repo
- `dangerouslySetInnerHTML` usage without a justification
- Insecure CORS / wildcard origins
- Missing authentication on API routes
- Bare `user_id` columns in RLS-less contexts (GDPR / tenant-isolation red flag)
"""

from __future__ import annotations

import re
from pathlib import Path

from .risk_patterns import Finding


# Patterns tuned for false-positive *reduction*, not zero recall.

_SECRET_LIKELY = re.compile(
    r"(?i)(api[_-]?key|secret|token|password|passwd|client[_-]?secret|private[_-]?key)"
    r"\s*[:=]\s*['\"][A-Za-z0-9_\-/.+=]{12,}['\"]"
)

_OPENAI_LIVE = re.compile(r"sk-[A-Za-z0-9]{20,}")
_AWS_ACCESS_KEY = re.compile(r"AKIA[0-9A-Z]{16}")
_GH_TOKEN = re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}")
_SLACK_TOKEN = re.compile(r"xox[abprs]-[A-Za-z0-9-]{10,}")

_DSIHTML = re.compile(r"dangerouslySetInnerHTML")
_CORS_WILDCARD = re.compile(r"Access-Control-Allow-Origin.*\*|cors\(\{\s*origin\s*:\s*['\"]?\*['\"]?")
_LOCALSTORAGE_TOKEN = re.compile(r"localStorage\.(setItem|getItem)\s*\(\s*['\"](token|access_token|jwt|refresh)")
_NO_AUTH_GUARD = re.compile(
    r"export\s+(?:async\s+)?function\s+(?:GET|POST|PUT|DELETE|PATCH)\s*\("
)
_RAW_USER_ID = re.compile(r"\.eq\(\s*['\"]user_id['\"]\s*,")


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def detect_secrets_in_source(text: str, rel: str) -> list[Finding]:
    findings: list[Finding] = []
    seen: set[tuple[int, str]] = set()

    patterns = [
        ("SECRET-INLINE", _SECRET_LIKELY, "Hardcoded secret-like value", "high"),
        ("SECRET-OPENAI", _OPENAI_LIVE, "OpenAI-style API key", "high"),
        ("SECRET-AWS", _AWS_ACCESS_KEY, "AWS access key id", "high"),
        ("SECRET-GH", _GH_TOKEN, "GitHub personal access token", "high"),
        ("SECRET-SLACK", _SLACK_TOKEN, "Slack token", "high"),
    ]
    for fid, pat, title, sev in patterns:
        for m in pat.finditer(text):
            key = (m.start(), fid)
            if key in seen:
                continue
            seen.add(key)
            line = text.count("\n", 0, m.start()) + 1
            snippet = text[max(0, m.start() - 10):m.end() + 10].replace("\n", " ").strip()
            if len(snippet) > 200:
                snippet = snippet[:197] + "..."
            findings.append(Finding(
                id=fid, title=title, severity=sev, category="security",
                file=rel, line=line, snippet=snippet,
                rationale="Move secrets to env vars / a secret manager. Rotate any leaked credential immediately.",
            ))
    return findings


def detect_env_committed(repo_root: Path, ignored: set[Path] | None = None) -> list[Finding]:
    """Flag any tracked .env / .env.* file."""
    findings: list[Finding] = []
    for p in repo_root.rglob("*"):
        if not p.is_file():
            continue
        if ignored and any(p == ig or ig in p.parents for ig in ignored):
            continue
        name = p.name
        if name == ".env" or (name.startswith(".env.") and not name.endswith(".example")):
            rel = str(p.relative_to(repo_root))
            findings.append(Finding(
                id="ENV-COMMITTED",
                title="Environment file present in repository",
                severity="high",
                category="security",
                file=rel,
                line=0,
                snippet=name,
                rationale="`.env*` files should not be committed. Add them to `.gitignore` and rotate any exposed values.",
            ))
    return findings


def detect_dangerously_set_inner_html(text: str, rel: str) -> list[Finding]:
    findings: list[Finding] = []
    for m in _DSIHTML.finditer(text):
        line = text.count("\n", 0, m.start()) + 1
        findings.append(Finding(
            id="REACT-DSIHTML",
            title="dangerouslySetInnerHTML usage",
            severity="medium",
            category="security",
            file=rel,
            line=line,
            snippet="dangerouslySetInnerHTML",
            rationale="Sanitise the input (e.g. DOMPurify) before rendering raw HTML, or render Markdown via a vetted pipeline.",
        ))
    return findings


def detect_localstorage_token(text: str, rel: str) -> list[Finding]:
    findings: list[Finding] = []
    for m in _LOCALSTORAGE_TOKEN.finditer(text):
        line = text.count("\n", 0, m.start()) + 1
        findings.append(Finding(
            id="AUTH-LS-TOKEN",
            title="Auth token in localStorage",
            severity="high",
            category="security",
            file=rel,
            line=line,
            snippet=m.group(0)[:200],
            rationale="localStorage is XSS-readable. Prefer httpOnly cookies for session tokens.",
        ))
    return findings


def detect_cors_wildcard(text: str, rel: str) -> list[Finding]:
    findings: list[Finding] = []
    for m in _CORS_WILDCARD.finditer(text):
        line = text.count("\n", 0, m.start()) + 1
        findings.append(Finding(
            id="CORS-WILDCARD",
            title="Wildcard CORS origin",
            severity="high",
            category="security",
            file=rel,
            line=line,
            snippet=m.group(0)[:120],
            rationale="`Access-Control-Allow-Origin: *` exposes authenticated endpoints to any origin. Whitelist explicit origins.",
        ))
    return findings


def detect_unauth_api_route(text: str, rel: str) -> list[Finding]:
    """Heuristic: API route file that defines GET/POST handler with no auth check."""
    findings: list[Finding] = []
    if not (rel.endswith("route.ts") or rel.endswith("route.js")):
        return findings

    has_handler = bool(_NO_AUTH_GUARD.search(text))
    if not has_handler:
        return findings

    has_auth_check = bool(re.search(
        r"(getServerSession|auth\(\)|currentUser|supabase\.auth\.getUser|requireAuth|verifyToken|checkAuth)",
        text,
    ))

    if has_handler and not has_auth_check:
        findings.append(Finding(
            id="API-NO-AUTH",
            title="API route without visible auth guard",
            severity="medium",
            category="security",
            file=rel,
            line=1,
            snippet="export async function GET/POST(...)",
            rationale="API routes must verify the caller. Add an auth guard at the top of each handler.",
        ))
    return findings


def detect_raw_user_id_filter(text: str, rel: str) -> list[Finding]:
    """Heuristic: `.eq('user_id', ...)` without a tenant or RLS check.

    Supabase RLS mitigates this when enabled, but flag client-side filters
    that assume RLS is the only line of defence.
    """
    findings: list[Finding] = []
    if "supabase" not in rel and ".ts" not in rel and ".tsx" not in rel and ".js" not in rel:
        return findings
    for m in _RAW_USER_ID.finditer(text):
        line = text.count("\n", 0, m.start()) + 1
        findings.append(Finding(
            id="AUTH-RAW-USERID",
            title="user_id filter without explicit auth context",
            severity="low",
            category="gdpr",
            file=rel,
            line=line,
            snippet=".eq('user_id', ...)",
            rationale="RLS should be the source of truth. Confirm policy in Supabase dashboard, and log the actor.",
        ))
    return findings


# ---------- public API -------------------------------------------------------

def scan_file(path: Path, repo_root: Path) -> list[Finding]:
    text = _read(path)
    rel = str(path.relative_to(repo_root))
    out: list[Finding] = []
    out.extend(detect_secrets_in_source(text, rel))
    out.extend(detect_dangerously_set_inner_html(text, rel))
    out.extend(detect_localstorage_token(text, rel))
    out.extend(detect_cors_wildcard(text, rel))
    out.extend(detect_unauth_api_route(text, rel))
    out.extend(detect_raw_user_id_filter(text, rel))
    return out


def scan_repo(repo_root: Path) -> list[Finding]:
    out: list[Finding] = []
    out.extend(detect_env_committed(repo_root))
    for p in repo_root.rglob("*"):
        if not p.is_file():
            continue
        # skip heavy/binary dirs
        parts = set(p.parts)
        if parts & {"node_modules", ".next", ".git", "dist", "build", "__pycache__", ".venv", "fixtures"}:
            continue
        out.extend(scan_file(p, repo_root))
    return out
