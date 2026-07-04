# Out of scope

This PoC scaffold is **deliberately narrow**. The following are *not* part of
this repo and will only become in-scope once a real engagement begins.

## What this repo is

- A generic static-analysis pass over a Next.js + Supabase + Lovable-style repo.
- Three Markdown templates (`templates/`) the client team can fill in.
- A demo Next.js page showcasing a WhatsApp-style conversation component driven
  by a **mocked** LLM provider (no API keys, no network calls).
- A small sample fixture (`fixtures/sample_lovable_repo`) intentionally built
  to trigger several rules.

## What this repo is NOT

- **Not** a complete vertical SaaS for aesthetic/wellness clinics. We have not
  seen the client's codebase, and the proposal explicitly declines the
  cofounder framing. Domain knowledge for that vertical — bookings,
  treatments, regulatory specifics, integrations — is acquired **after**
  kickoff.
- **Not** a substitute for a security audit by a human. Static rules catch
  common mistakes; they do not replace threat modelling or penetration
  testing.
- **Not** a real AI assistant. The `/api/chat` route is intentionally mocked.
  Wiring it to OpenAI / Anthropic / a local model is **post-kickoff work**
  and must be:
  - rate-limited
  - authenticated
  - audited (request IDs + structured logs)
  - tested for prompt-injection
- **Not** an automatic fixer. Findings are emitted as a Markdown report;
  triage and code edits are the team's responsibility, with our help.
- **Not** an SLA, retainer, or hosting service.

## Honest about engagement scope

The work proceeds in two-week sprints with explicit goals. The first sprint
typically:

1. Confirms the audit report against the real codebase.
2. Triages findings with the client team.
3. Ships the highest-priority fixes (committed & deployed to staging).

Everything else sits in the backlog until both sides agree in writing.

See [`templates/handoff_doc_template.md`](templates/handoff_doc_template.md)
for the working agreement we use during the first two sprints.
