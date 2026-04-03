# Dream Blue agents and operations playbook

This document is for humans and for Cursor-style agents working on profitability, tenant tracking, and prospecting.

## Data the system trusts

- **Business calendar events** drive the digest, ICS export, lease economics, and suggested rents. Lease rows should set **rent basis** (gross vs NNN vs unknown) and **rent basis note** so “suggested” (gross-oriented) is not misread as apples-to-apples with net leases.
- **Lease document URL** (or `reference_url`) is the audit link for abstracts and LOIs.
- **Books reconciliation** (`BusinessBooksReconciliation`) is the optional “per books” rent and operating totals vs the calendar roll-up, with **variance notes** explaining timing and accrual.
- **Lease rent roll changes** append when lease `amount` or sf fields change — use for history and digest “recent changes.”

## Running agents (management commands)

| Command | Role |
|--------|------|
| `grantscout_run_agent` | Funding / incentive / regulatory scan; drift vs prior run; digest section. |
| `dream_blue_run_lease_comp_agent` | Bemidji-area lease / flex comparable memo; stores **diff vs prior** memo in `report_diff_summary`. |
| `dream_blue_send_digest` | Renders HTML email from DB state; logs structured fields (`dream_blue_event`, `recipient_count`, `required_gpr_monthly`, timings). |

Cron examples live under `deploy/` (`grantscout_agent_biweekly.sh`, `lease_comp_scheduled.sh`).

## GrantScout noise control

- Set **`topic_tags`** on each opportunity (JSON list of lowercase strings, e.g. `bemidji`, `retail`, `energy`).
- Set env **`GRANTSCOUT_DIGEST_TOPIC_TAGS`** (comma-separated) so the digest only includes rows whose tags overlap. Empty = show all.

## Staff URLs (after login, staff user)

- Operations calendar: `/apps/dream-blue/operations/calendar/`
- Units / $·sf dashboard: `/apps/dream-blue/operations/units/`
- ICS: `/apps/dream-blue/operations/calendar.ics` — add `?critical=1` for leases, property tax, and insurance only (Google Calendar one-way subscribe).

## Improving agent quality (prompts and review)

- **Lease comp:** Require explicit gross vs NNN labeling in the memo when sources allow; call out when the model is inferring vs quoting.
- **GrantScout:** Prefer canonical program URLs; use `topic_tags` consistently so digest filtering stays useful.
- **Human loop:** Review the **diff block** in the digest for lease comp and **drift** for GrantScout before treating outputs as decisions.

## Engineering checks

- `python manage.py test dream_blue` — includes digest HTML substring checks and rent-roll logging tests.
- After template table changes, update expectations in `DigestHtmlTemplateSnapshotTests` if columns are renamed on purpose.

## Optional Cursor skill (local)

To turn this into a reusable **Skill** in Cursor, use the project’s create-skill flow and point the skill at this file plus `dream_blue/lease_comp_agent.py` and `dream_blue/grantscout_agent.py` for command names and invariants.
