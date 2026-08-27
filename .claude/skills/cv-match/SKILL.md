---
name: cv-match
description: Parse Nicolas's CV, match it against a specific job description, produce a tailored CV, then refine it through a generator→evaluator loop with a blind critic subagent until the match score reaches 95/100 or honestly plateaus. Use whenever the user has a job posting to tailor the CV to, or asks to "match", "tailor", "adapt the CV", "score" or "optimize" a role.
---

# CV Match (with refinement loop)

Parse → map → score → tailor → **refine until ≥95 or plateau**. The first
draft is never the deliverable; the loop is.

## Inputs
- **CV** — by posting language: `context/cv-master-fr.md` (FR) or
  `context/cv-master.md` (EN) in the cv-job-match repo. Read both if unsure —
  the FR file has richer facts/metrics and is the better fact source even for
  English output. Neither present → ask for the CV text.
- **Job description** — the target posting. Thin posting + named company →
  ask for a link before matching.
- **Narrative rules** — `context/narrative-rules.md` if present, else defaults.

## Narrative principles (always apply)
- Emphasize skills and learning, not duration.
- Stay positive; each mission is an opportunity.
- Show continuity; freelance since April 2025 is a deliberate strategic choice.
- Lead with impact and value delivered.

## Phase 1 — Analysis (once)

1. **structured_profile** — parse the CV to JSON
   `{identity, summary, skills{hard,soft,tools}, experiences[{org, role,
   period, context, actions[], results[{metric,value}], themes[]}],
   certifications[]}`. Keep it; later skills reuse it.
2. **Requirement extraction** — list the posting's requirements as discrete,
   numbered items with a weight (must-have = 2, nice-to-have = 1). This list
   is the scoring contract for the whole loop — freeze it now so the score
   can't drift to flatter the draft.
3. **Relevance map** — `| # | Requirement | Evidence in CV | Strength H/M/L |`.
4. **Edit plan** — Retitle / Rewrite summary / Downplay-drop / Elevate-add,
   each item with a one-line reason. Only claims the real CV supports.

## Phase 2 — Generate v1
Write the full tailored CV in markdown, applying the edit plan, natively in
the posting's language. Reorder, re-weight, rephrase — never fabricate.
Save it to a file (e.g. `applications/<slug>/cv-v1.md`) so each iteration is
a diffable artifact, not chat scrollback.

## Phase 3 — Refinement loop (the agentic part)

Repeat up to **4 rounds**:

### 3a. Blind evaluation (fresh-context critic)
Spawn a subagent with the **Agent tool** (general-purpose). Give it ONLY:
the job posting, the frozen requirement list, the current CV file, and the
rubric below. It must NOT see the master CV, the edit plan, previous
versions, previous scores, or this conversation — a critic that saw the
generator's reasoning rubber-stamps it, which is exactly the "output stays
close to the input" failure this loop exists to fix.

The evaluator returns JSON:
```json
{"score": {"coverage": 0-40, "ats_keywords": 0-20, "impact_evidence": 0-20,
           "company_fit": 0-10, "readability": 0-10, "total": 0-100},
 "findings": [{"severity": "major|minor", "requirement": "#N or general",
               "problem": "…", "concrete_fix": "…"}]}
```
Rubric: **coverage /40** — each weighted requirement visibly addressed near
the top of the CV; **ats_keywords /20** — the posting's exact terms (tools,
methods, domain words) appear where true; **impact_evidence /20** — claims
carry metrics/outcomes, not duties; **company_fit /10** — summary and framing
speak to this company's domain/product; **readability /10** — one page logic,
scannable, no dilution by irrelevant experience.

If the Agent tool is unavailable, re-read only the two files fresh and
evaluate in a strict critic persona — but prefer the subagent.

### 3b. Revise
For **every** finding: apply the concrete fix, or explicitly reject it with a
reason (only valid reasons: it would fabricate experience, or it contradicts
the narrative principles). Write the result to `cv-v{n+1}.md`.

### 3c. Stop conditions
- **total ≥ 95** → done;
- improvement < 3 points vs previous round → **honest plateau**: stop and
  report the residual gaps as real gaps (interview prep material, or a
  learning-plan item), not as wording problems. Never chase the score by
  inventing facts — a fabricated 95 is worse than a true 82;
- 4 rounds reached → stop, same reporting.

## Phase 4 — Report
```
## Match Score trajectory   (v1: 78 → v2: 88 → v3: 95)
## Relevance Map (final)
## What changed and why     (per round, 2-3 bullets)
## Residual gaps            (honest; feeds interview-prep)
## Tailored CV (final)
```
Deliver the final CV file (and .docx via the docx skill if the user wants the
application-ready version). Then offer: `write-outreach` for this posting
(it runs the same loop on the letter), or log it in the tracker.

## Handoff
`structured_profile`, the frozen requirement list, and the final CV feed
`write-outreach` and `interview-prep`. The score trajectory feeds the tracker.
