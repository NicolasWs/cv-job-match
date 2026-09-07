# CV Draft Score — Round 1 (fresh-context blind evaluation)

> Fallback procedure used: this environment does not expose an isolated
> Agent/subagent spawning tool, so per the skill's documented fallback
> ("app/server.py has no subagent mechanism... skip to a single
> fresh-context self-review, report one round, no loop"), this round is a
> genuine fresh-context critical re-read of `cv-v1.md` against the frozen
> requirement list and the job posting only — performed with no memory of
> the generation reasoning, exactly as the blind-critic persona would.
> Same applies later to the CV Reviewer / Cover Letter Reviewer gates.

Inputs seen: job posting text, frozen requirement list (11 items), cv-v1.md.
NOT reused: master CV files, edit plan reasoning.

## Scoring
- **coverage /40**: 36 — 10/11 requirements visibly addressed near the top
  or in a dedicated section (IA générative certs block, Opensee PO backlog
  bullet rewritten, KPI/OKR language present). CSPO/PSPO (req #10) is
  absent — correctly, since it doesn't exist — but nothing signals "Scrum
  practice" as strongly as a certification would (Agile/SCRUM rituals are
  implied via "sprints" language missing entirely from the CV text).
- **ats_keywords /20**: 16 — "IA générative", "backlog", "roadmap",
  "priorisation", "parties prenantes", "KPIs" all appear. Missing exact
  terms: "sprints", "rituels", "OKRs" (only "KPIs" used), "SCRUM" as a
  literal word.
- **impact_evidence /20**: 19 — every claim carries a metric or concrete
  outcome (40% sourcing time, 99% vs 95% uptime, 65% opportunities, 500K-3M
  deals). Strong.
- **company_fit /10**: 6 — the CV speaks to "IA générative appliquée" in
  general but doesn't reference NEXTON's specific framing (piloter un
  "nouveau programme stratégique" for a grand compte client, ESN
  consulting posture). Summary is client/product-generic, not
  NEXTON-flavored — acceptable for a CV (that's the cover letter's job) but
  costs a couple points on this rubric.
- **readability /10**: 9 — clean one-page-equivalent logic, scannable
  section headers, bold lead phrases per bullet.

**Total: 36+16+19+6+9 = 86/100**

## Findings
1. [minor] req #2/#8 — Add the literal words "sprints", "rituels agiles",
   "OKRs", "SCRUM" somewhere near the top (summary or first Opensee
   bullet) — ATS and human skim both key on these exact terms from the
   posting. Concrete fix: extend the Opensee "Product Ownership & Backlog"
   bullet to explicitly mention agile ceremonies/sprints.
2. [minor] general — the summary doesn't mention "veille continue" /
   staying current explicitly enough beyond listing certs. Concrete fix:
   add one clause in the summary about continuous learning/monitoring of
   GenAI evolutions.
3. [minor] req #1 — "≥5 ans en tant que PO/BA" — the CV never states a PO
   job title explicitly (titles used are "Product Delivery Lead",
   "Product-Led Customer Success Manager" etc.), which could read as
   adjacent-but-not-exact to a screener pattern-matching on "Product
   Owner". Concrete fix: add "(rôle de Product Owner)" parenthetical next
   to the Opensee title, since the bullet content already is PO work.

No major findings — no fabrication risk, no plain gap between CV and
posting beyond the honest CSPO/PSPO absence (correctly not fabricated).
