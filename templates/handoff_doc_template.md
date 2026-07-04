# Engineering-Direction Handoff — `<your-repo>`

This template implements the "engineering-direction handoff" promised in
PROPOSAL §1. It is a working agreement between your team and ours for the
first two weeks of engagement. Fill it in **before** sprint 1 so we have a
shared baseline and a clear handover at the end of each sprint.

## 1. Current state (filled by us)

- **Stack:** Next.js 14 (App Router), Supabase, Tailwind, Lovable-generated UI.
- **Estimated completion (Lovable):** ~60 % of MVP.
- **Repo URL:** <repo>
- **Staging URL:** <url>
- **Production URL:** <url>
- **Coverage:** <% lines> / <% branches>
- **Open findings:** <count high>, <count med>, <count low>

## 2. Goals for the first two weeks

| # | Goal | Acceptance criteria | Owner | Due |
| --- | --- | --- | --- | --- |
| 1 | Resolve all `high`-severity audit findings | All `high` rows in `risk_register.md` have a `Status: Resolved` link. |  |  |
| 2 | Introduce a `lib/db` data layer | Pages/components no longer import `@supabase/supabase-js` directly. |  |  |
| 3 | CI: tests + coverage report on every PR | `.github/workflows/ci.yml` shows green. |  |  |
| 4 | Sentry / structured logs in production | Issues appear with a request-id correlation. |  |  |
| 5 | Smoke test of the top-3 user journeys | `npm run test:e2e` exits 0. |  |  |

## 3. Out of scope (explicit)

- OAuth provider beyond what Supabase already does.
- Anything that does not appear in §2 unless both sides agree in writing.
- Domain-specific customisations for aesthetics/wellness clinics — captured
  here only as a placeholder; deeper work starts after the audit handover.

## 4. Working agreement

- **Communication:** daily async standup in a shared channel; weekly live
  30-minute check-in.
- **Cadence:** weekly PR review with at least one of us on call.
- **Branching:** trunk-based on `main`; PRs < 400 lines where possible.
- **Definition of done:** tests pass, CI green, reviewer approved, deployed to
  staging.
- **Escalation:** if a finding can't be triaged in 24 h, escalate to the
  product owner.

## 5. Hand-back checklist (end of sprint 2)

- [ ] All goals in §2 met or explicitly deferred with rationale.
- [ ] `risk_register.md` updated; remaining items have owners.
- [ ] `production_readiness_checklist.md` reviewed item-by-item.
- [ ] One-page architecture diagram refreshed to reflect new layout.
- [ ] Runbook for the top-3 incidents committed under `docs/runbook.md`.

## 6. Sign-off

| Role | Name | Date |
| --- | --- | --- |
| Client product owner |  |  |
| Client technical lead |  |  |
| Engineering partner |  |  |
