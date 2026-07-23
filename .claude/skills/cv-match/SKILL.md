---
name: cv-match
description: Parse a CV, match it against a specific job description, and propose concrete improvements for that posting — which experience to drop or downplay, how to retitle and rewrite the summary, and how to adapt wording to the target company. Use whenever the user has a job posting they want to tailor Nicolas's CV to, or asks to "match", "tailor", "adapt the CV", or "score" a role.
---

# CV Match

Parse Nicolas's CV, score fit against ONE job description, and produce an
actionable edit list plus a tailored CV.

## Inputs
- **CV** — pick by the job description's language: `context/cv-master-fr.md`
  for a French posting, `context/cv-master.md` for English. Read both if
  unsure or if the posting mixes languages — `cv-master-fr.md` has richer
  technical detail (exact stack, Natixis/Opensee/Woon metrics, full AI
  certification list) and is the better fact source even when writing in
  English. If neither file exists, ask the user to paste the CV text.
- **Job description** — the target posting (paste). If a company is named but
  the posting is thin, ask for a link or more detail before matching.
- **Narrative rules** — read `context/narrative-rules.md` if present, else apply
  the defaults in the "Narrative principles" section below.

## Narrative principles (always apply)
- Emphasize skills and learning, not duration.
- Stay positive; each mission is an opportunity.
- Show continuity; freelance since April 2025 is a deliberate strategic choice.
- Lead with impact and value delivered.

## Procedure

### 1. Parse into structured_profile
Extract JSON (keep it — later skills reuse it):
```json
{ "identity": {"name":"", "target_titles":[]},
  "summary":"", "skills":{"hard":[],"soft":[],"tools":[]},
  "experiences":[{"org":"","role":"","period":"","context":"",
    "actions":[],"results":[{"metric":"","value":""}],"themes":[]}],
  "certifications":[] }
```

### 2. Relevance map
Table: `| Job requirement | Evidence in CV | Strength (H/M/L) |`
One row per meaningful requirement in the posting.

### 3. Match score
`Strong / Good / Partial` + a 2-line honest justification (name the biggest
strength and the biggest gap).

### 4. Edit suggestions (the actionable part)
Four labelled lists, each item = change + one-line reason:
- **Retitle** — the CV title/headline to mirror the target role.
- **Rewrite summary** — a 2–3 line summary tuned to this role AND company
  (reference the company's domain/product where natural).
- **Downplay / drop** — experiences or bullets that dilute relevance here.
- **Elevate / add** — experiences, skills, or keywords to surface (only claims
  supported by the real CV — never invent experience).

### 5. Tailored CV
Output a full tailored CV in markdown applying the edits above. Match the
posting's language (FR/EN) — write natively in that language, don't translate
literally. Preserve every factual claim from the source CV; you may reorder,
re-weight, and rephrase, but not fabricate.

## Output format
```
## Structured Profile (JSON)
## Relevance Map
## Match Score
## Edit Suggestions
## Tailored CV
```
Then offer: "Next: draft outreach (cover letter / email / LinkedIn) with
`write-outreach`, or log this in the tracker with `track-application`?"

## Handoff
`structured_profile` + edit suggestions feed `write-outreach`. Match score +
company/role feed `track-application`.
