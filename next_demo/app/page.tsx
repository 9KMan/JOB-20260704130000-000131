// Landing page showing the audit workflow.
//
// This is a *demo skeleton* used inside this repo to show what a Next.js + Tailwind
// page wired to the audit methodology might look like. No data is fetched here;
// replace the static copy with real data after kickoff (see templates/handoff_doc_template.md).

import Link from "next/link";

export const metadata = {
  title: "Lovable-MVP Audit — what we check",
  description: "Generic SaaS audit scaffold for Next.js + Supabase + Lovable-style MVPs.",
};

const STEPS = [
  {
    n: 1,
    title: "Run the static scan",
    body: "We point lovable-audit at your repo and collect findings across architecture, security, testing, and GDPR posture.",
  },
  {
    n: 2,
    title: "Triage with the risk register",
    body: "Each finding moves into templates/risk_register.md with severity, owner, and target date. We fix-now / fix-next-sprint / accept-risk together.",
  },
  {
    n: 3,
    title: "Introduce a thin data layer",
    body: "Pages stop importing @supabase/supabase-js directly. All DB calls live under lib/db so views become trivially testable.",
  },
  {
    n: 4,
    title: "Production-readiness gate",
    body: "templates/production_readiness_checklist.md covers deploys, observability, errors, security, GDPR, testing, and operations.",
  },
];

export default function Home() {
  return (
    <main className="mx-auto max-w-3xl px-6 py-16 font-sans text-slate-800">
      <header className="mb-12">
        <p className="text-xs uppercase tracking-widest text-slate-500">
          Vertical-SaaS audit scaffold
        </p>
        <h1 className="mt-2 text-4xl font-semibold tracking-tight">
          Make your Lovable MVP safe to ship.
        </h1>
        <p className="mt-4 text-lg text-slate-600">
          A rule-based audit + a set of fill-in-the-blank templates so we can
          triage, fix, and launch with confidence — without claiming we know
          your codebase before kickoff.
        </p>
        <div className="mt-6 flex gap-3">
          <Link
            href="/whatsapp-demo"
            className="rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700"
          >
            See the conversation demo
          </Link>
          <a
            href="https://github.com/9KMan/JOB-20260704130000-000131"
            className="rounded-md border border-slate-300 px-4 py-2 text-sm font-medium text-slate-800 hover:bg-slate-50"
          >
            View on GitHub
          </a>
        </div>
      </header>

      <section className="mb-12">
        <h2 className="mb-4 text-xl font-semibold">How the audit works</h2>
        <ol className="space-y-4">
          {STEPS.map((s) => (
            <li key={s.n} className="rounded-lg border border-slate-200 p-4">
              <div className="text-xs font-mono text-slate-500">Step {s.n}</div>
              <div className="font-medium">{s.title}</div>
              <div className="mt-1 text-sm text-slate-600">{s.body}</div>
            </li>
          ))}
        </ol>
      </section>

      <section className="mb-12 rounded-lg bg-amber-50 p-4 text-sm text-amber-900">
        <strong className="block">Honest about scope</strong>
        This is a generic scaffold. Domain-specific work (aesthetic-clinic
        workflows, regulatory specifics, integrations you depend on) starts
        <em> after </em> kickoff — see <code>OUT_OF_SCOPE.md</code>.
      </section>
    </main>
  );
}
