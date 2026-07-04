// Mock AI chat API route for the demo.
//
// This route intentionally does NOT call any real LLM. It returns one of a
// small set of canned replies based on keyword matching. Replace this with a
// real provider (and add rate-limiting + auth) after kickoff.

import { NextResponse } from "next/server";

type Body = { message?: string };

const REPLIES: Array<{ match: RegExp; reply: string }> = [
  {
    match: /audit|check|review/i,
    reply:
      "The audit checks architecture smells (no data layer, import cycles, long files), security (committed .env, hard-coded secrets, `dangerouslySetInnerHTML`, wildcard CORS), testing (coverage %, missing test files), and GDPR posture (RLS presence, audit logging). See templates/risk_register.md.",
  },
  {
    match: /sprint|timeline|long|how many/i,
    reply:
      "Sprint 1 (kickoff to first deploy) is typically 5–8 working days for an MVP at ~60% complete. The exact cadence is set in templates/handoff_doc_template.md once we agree on goals.",
  },
  {
    match: /supabase|rls|row.level/i,
    reply:
      "For Supabase, we (1) verify RLS is `enabled` on every table, (2) replace `true` policies with explicit ones, and (3) wrap client queries in lib/db so policies are not the only line of defence.",
  },
  {
    match: /privacy|gdpr|data/i,
    reply:
      "GDPR-relevant items here: RLS policies, audit logging for admin actions, account-deletion flow, DPA with each subprocessor, and a 30-day log retention window. See templates/production_readiness_checklist.md §5.",
  },
  {
    match: /cost|price|budget|hourly/i,
    reply:
      "We don't take cofounder equity. Engagements are weekly blocks on an hourly rate, billed only after each demo. See the proposal.",
  },
  {
    match: /hello|hi|hey/i,
    reply: "Hi! 👋 Ask me about audits, Supabase, GDPR, sprint cadence, or pricing.",
  },
];

export async function POST(req: Request) {
  const body = (await req.json().catch(() => ({}))) as Body;
  const message = (body.message ?? "").slice(0, 500).trim();
  if (!message) {
    return NextResponse.json({ error: "empty message" }, { status: 400 });
  }

  for (const r of REPLIES) {
    if (r.match.test(message)) {
      return NextResponse.json({ reply: r.reply, mock: true });
    }
  }
  return NextResponse.json({
    reply:
      "I'm a mocked provider — try one of the suggestion chips: audit, sprint, Supabase, GDPR, or pricing.",
    mock: true,
  });
}
