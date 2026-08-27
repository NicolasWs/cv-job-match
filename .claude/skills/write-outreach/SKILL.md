---
name: write-outreach
description: Draft tailored outreach for a specific job — cover letter, recruiter/hiring-manager email, and LinkedIn message — then refine each through a blind evaluator loop until it scores high or honestly plateaus. Use whenever the user wants a cover letter, an email to a company, or a LinkedIn message for a role, or says "draft outreach", "write to them", "cover letter".
---

# Write Outreach (with refinement loop)

Draft cover letter, recruiter email, and LinkedIn message for ONE posting —
then iterate. The first draft is raw material, not the deliverable.

## Inputs
- **structured_profile + requirement list + final tailored CV + Match Score**
  — reuse `cv-match` output if it ran this session. Otherwise read the CV
  matching the posting's language (`context/cv-master-fr.md` FR /
  `context/cv-master.md` EN; the FR file is the richer fact source even for
  English output).
- **Job description** — the target posting.
- **Company notes** — `company-intel` output if available, else anything known.
- **Narrative rules** — `context/narrative-rules.md` if present, else defaults.

## Narrative principles (always apply)
- Emphasize skills and learning, not duration.
- Stay positive; each mission is an opportunity.
- Show continuity; freelance since April 2025 is a deliberate strategic choice.
- Lead with impact and value delivered.

Style: professional, positive, impact-focused. No clichés, no filler, no
invented facts. Match the posting's language (FR/EN).

## Phase 1 — Draft the three assets

### 1. Cover letter (~250–300 words)
Hook (why this company, specific — a product, a market move, a real detail) →
why me (2–3 impact proofs with metrics) → fit with the role → clear CTA.

### 2. Recruiter / hiring-manager email (~120 words)
Subject line + short body. Single strongest relevance point first,
attach-CV mention, one-line CTA. Skimmable.

### 3. LinkedIn connection message (≤300 characters)
Warm, specific to the person/role, one reason to connect, soft ask.

Save drafts to files (e.g. `applications/<slug>/outreach-v1.md`) so each
iteration is diffable.

## Phase 2 — Refinement loop (cover letter, then email)

**Only available in a Claude Code / Cowork session** — the blind-evaluation
step needs the `Agent`/subagent tool. `app/server.py` (the local web app)
has no subagent mechanism; when running there, do one fresh-context
self-review pass instead (re-read the draft against the rubric with no
memory of why you wrote it) and report a single round, no loop.

Up to **3 rounds** per asset (the LinkedIn message gets one review pass, not
a full loop — it's 300 characters):

**Blind evaluation.** Spawn a general-purpose subagent (Agent tool) that sees
ONLY: the posting, the company notes, the current draft, and this rubric —
not the CV, not previous versions or scores, not this conversation. It plays
a busy hiring manager at THIS company and returns JSON
`{score:{...,total 0-100}, findings:[{severity, problem, concrete_fix}]}`.

Rubric /100: **company_specificity /25** — could this letter have been sent
to any other company? every generic sentence costs points; **evidence /25** —
claims traceable to the CV, with numbers; **jd_mirroring /20** — answers the
posting's actual asks in its own vocabulary; **structure /15** — hook quality,
length discipline, one idea per paragraph, real CTA; **voice /15** — no
clichés ("passionate", "dynamic", "je me permets"), active verbs, sounds like
a person.

**Revise.** Apply every concrete_fix or reject it with a reason (fabrication
/ narrative-principle conflict only). Write `outreach-v{n+1}.md`.

**Stop:** total ≥ 95, or gain < 3 points, or 3 rounds. On plateau, report
what's structurally missing (usually: no real company insight available →
suggest running `company-intel` and re-looping once with its output).

## Output format
```
## Score trajectory (per asset)
## Cover Letter (final)
## Recruiter Email (Subject / Body, final)
## LinkedIn Message
## What the loop changed (2-3 bullets)
```
Then offer: a variant (shorter / warmer / more technical), a follow-up
message, or `interview-prep` for this company.

## Guardrails
- Every quantified claim must trace to the CV / experience bank. No metric in
  the source → write qualitatively, never invent a number. A fabricated 95
  is worse than a true 82.
- Keep the freelance framing deliberate and positive, never apologetic.
- This skill writes drafts; it never sends anything.
