---
name: interview-prep
description: Prepare Nicolas for an interview at a specific company/role — generate a strengths/weaknesses and behavioural Q&A set, build project storytelling (STAR) from his real missions, and assemble a one-page interview support sheet with key stories, metrics, and talking points. Use whenever the user is preparing for an interview, asks for "Q&A", "prep questions", "tell me about yourself", "storytelling", or "interview support".
---

# Interview Prep

Produce interview material for ONE company/role.

## Inputs
- **structured_profile** — reuse `cv-match` output if available, else read the
  CV matching the interview language (`context/cv-master-fr.md` for French,
  `context/cv-master.md` for English — the FR file has richer facts/metrics),
  else ask for the CV.
- **experience bank** — read `context/experience-bank.md` if present (Opensee,
  Natixis, Palo IT, Trade Value/Woon). If absent, extract stories from the CV.
- **target company + role** — ask if not given.
- **Narrative rules** — `context/narrative-rules.md` if present, else defaults.

## Narrative principles (always apply)
- Emphasize skills and learning, not duration.
- Stay positive; each mission is an opportunity.
- Show continuity; freelance since April 2025 is a deliberate strategic choice.
- Lead with impact and value delivered.

## Produce three sections

### 1. Q&A set
Cover, at minimum:
- "Tell me about yourself" (a 60–90s spoken narrative arc, not a CV readout).
- Strengths — 3, each tied to a real proof + metric.
- Weaknesses — 2, honest, each with the mitigation/learning already in motion.
- "Why this company / this role?" — specific to THIS company's product/domain.
- "Recent experience" — how to frame the freelance period as deliberate strategy.
- 2–3 role-specific behavioural questions likely for a PM/PO in AI/Data.

For each: the question, a suggested answer (bullets, not a script), and 1–2
follow-up questions the interviewer might ask so Nicolas can prepare depth.

### 2. Project storytelling (STAR)
For the 2–3 most relevant missions to this role, a tight story:
**Situation → Task → Action → Result → Learning.** Lead with the result/metric,
keep each to ~45–60 seconds spoken. Pick the missions that best match the
posting, not all of them.

### 3. Interview support sheet (one page)
A scannable cheat-sheet to glance at during/before the interview:
- **Key stories** — 3 one-line story titles + their headline metric.
- **Key metrics** — the numbers worth memorising.
- **Talking points** — 4–5 bullets tuned to this company/role.
- **Questions to ask them** — 4–5 sharp questions that signal seniority and
  surface insight about the job.

## Output format
```
## Q&A Set
## Project Storytelling (STAR)
## Interview Support Sheet
```
Offer to export the support sheet to a Google Doc or the user's Drive.

## Guardrails
Every metric traces to the CV / experience bank — never invent numbers or
outcomes. Weaknesses must be real and constructively framed, not humble-brags.
