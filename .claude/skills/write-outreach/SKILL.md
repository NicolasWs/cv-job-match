---
name: write-outreach
description: Draft tailored outreach for a specific job — a cover letter, a recruiter/hiring-manager email, and a LinkedIn connection message — using Nicolas's profile and the target posting. Use whenever the user wants a cover letter, an email to a company, or a LinkedIn message for a role, or says "draft outreach", "write to them", "cover letter".
---

# Write Outreach

Draft cover letter, recruiter email, and LinkedIn message for ONE posting.

## Inputs
- **structured_profile + positioning** — reuse the output of `cv-match` if it
  ran this session. Otherwise read the CV matching the job description's
  language (`context/cv-master-fr.md` for French, `context/cv-master.md` for
  English — the FR file has richer facts/metrics and is a good source even
  when writing in English), or ask for the CV.
- **Job description** — the target posting.
- **Company notes** — anything known about the company/team (optional).
- **Narrative rules** — `context/narrative-rules.md` if present, else defaults.

## Narrative principles (always apply)
- Emphasize skills and learning, not duration.
- Stay positive; each mission is an opportunity.
- Show continuity; freelance since April 2025 is a deliberate strategic choice.
- Lead with impact and value delivered.

Style: professional, positive, impact-focused. No clichés, no generic filler,
no invented facts. Match the posting's language (FR/EN).

## Produce three assets

### 1. Cover letter (~250–300 words)
Structure: hook (why this company, specific) → why me (2–3 impact proofs with
metrics from the experience bank) → fit with the role → close with a clear CTA.

### 2. Recruiter / hiring-manager email (~120 words)
Subject line + short body. Lead with the single strongest relevance point,
attach-CV mention, one-line CTA. Skimmable.

### 3. LinkedIn connection message (≤300 characters)
Warm, specific to the person/role, one reason to connect, soft ask. No pitch dump.

## Output format
```
## Cover Letter
## Recruiter Email  (Subject: … / Body: …)
## LinkedIn Message
```
Then offer: "Want a variant (shorter / warmer / more technical), a follow-up
message, or contact-finding help (`find-contacts`)?"

## Guardrails
- Every quantified claim must trace to the CV / experience bank. If a metric
  isn't in the source, write qualitatively rather than inventing a number.
- Keep the freelance framing deliberate and positive, never apologetic.
