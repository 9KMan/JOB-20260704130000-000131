# Production Readiness Checklist — `<your-repo>`

A pragmatic, MVP-targeted checklist. It is **not** SOC 2 / ISO 27001 — those
require their own audits. Use it for a small-team SaaS about to take its
first paying customers.

## 1. Deployment

- [ ] `main` branch is protected; PRs require 1 review.
- [ ] CI runs `typecheck`, `lint`, `test`, and `build` on every PR.
- [ ] Deploys are gated on green CI; releases are tagged in git.
- [ ] Hosting: Vercel / Fly / Render / Railway — auto-deploys from `main`.
- [ ] Preview deployments exist per PR and are reachable.
- [ ] Environment variables are set via the hosting UI, never committed.
- [ ] Database migrations are reversible; a backup exists for the last 7 days.
- [ ] DNS / TLS / HSTS handled by host or Cloudflare.

## 2. Observability

- [ ] Structured logs from API routes (`pino`, `winston`, `next-logger`).
- [ ] Error reporting: Sentry / Highlight / Rollbar installed and DSN set.
- [ ] Uptime monitor: Betterstack / Cronitor / Healthchecks on `/api/health`.
- [ ] Smoke test on production URL: load `/`, `/api/health`, key flows.
- [ ] Pager rotation or "who's on-call" doc for incident response.

## 3. Error handling & resilience

- [ ] Global `ErrorBoundary` in the React tree; UI never goes blank.
- [ ] All async UI surfaces show error and retry states.
- [ ] Server routes log + return sanitised errors (no stack leak).
- [ ] Background jobs are idempotent and re-queueable.
- [ ] Rate-limits in front of any LLM/3rd-party call.

## 4. Security

- [ ] All `route.ts`/`route.js` handlers verify auth before any data access.
- [ ] Cookies are `httpOnly`, `Secure`, `SameSite=Lax|Strict`.
- [ ] RLS is enabled on every Supabase table; policies are explicit, not `true`.
- [ ] CORS is whitelisted to known origins (no `*`).
- [ ] CSP header is set in `next.config.js`.
- [ ] No `dangerouslySetInnerHTML` unless the input is sanitised first.
- [ ] Dependencies scanned by `npm audit --production` in CI.

## 5. GDPR / data protection

- [ ] Public privacy policy exists and is linked from signup.
- [ ] Data Processing Agreement in place with each subprocessor (Supabase,
  OpenAI, etc.).
- [ ] Data export and account deletion flows are working.
- [ ] Log retention policy is configured (default 30 days).
- [ ] Audit log for admin actions (create / delete / role change).

## 6. Testing

- [ ] Smoke tests for the top-3 user journeys.
- [ ] Auth tests covering sign-up, sign-in, sign-out, password reset.
- [ ] At least one test per API route.
- [ ] Coverage threshold in CI (we recommend 70% lines, 60% branches).

## 7. Operations

- [ ] Runbook for the 3 most likely incidents (DB down, 3rd-party down,
  spike in errors).
- [ ] `CHANGELOG.md` kept up to date at every release.
- [ ] Onboarding doc for a new engineer joining cold.

## Sign-off

| Role | Name | Date |
| --- | --- | --- |
| Engineer who built it |  |  |
| Engineer who reviews it |  |  |
| Product owner |  |  |
