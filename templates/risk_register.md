# Risk Register — `<your-repo>`

Use this register to triage the issues raised by `lovable-audit` (and any
follow-up human review). Duplicate rows for additional findings; assign an
owner, a target date, and a risk class. Keep the register in version control so
it survives staff changes.

## How to use

1. Run `lovable-audit <repo> --out report.md` and paste the findings into the
   *Observation* column.
2. Triage each item into one of: `fix-now`, `fix-next-sprint`, `accept-risk`,
   `out-of-scope`.
3. Tag severity (high / medium / low) and add links to PRs, tickets, or notes.

## Triage header

| Field | Value |
| --- | --- |
| Repository | |
| Audit date | |
| Auditor | |
| Coverage % | |
| Decision gate (launch / next-sprint / backlog) | |

## Findings

| # | Severity | Category | ID | Location | Observation | Owner | Action | Target date | Status | Notes / link |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 |  |  |  |  |  |  |  |  |  |  |
| 2 |  |  |  |  |  |  |  |  |  |  |
| 3 |  |  |  |  |  |  |  |  |  |  |

## Out-of-scope (intentional)

If you decide a finding is **not** worth fixing, add it here with a one-line
justification. Risk tolerance should be explicit, not implicit.

| # | ID | Why we're accepting | Review date |
| --- | --- | --- | --- |
|  |  |  |  |

## Sign-off

| Role | Name | Date | Signature |
| --- | --- | --- | --- |
| Tech lead |  |  |  |
| Product owner |  |  |  |
| Security reviewer |  |  |  |
