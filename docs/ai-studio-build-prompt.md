# Google AI Studio — one-shot build prompt

Paste the block below into Google AI Studio's "Build" (app generation) flow
to reconstruct this system on the Gemini API. It intentionally does **not**
include Nicolas's actual CV — the app collects that at runtime, same as the
Claude-based version.

---

```
Build a single-page web app called "CV & Job Application Assistant" — a
personal job-search tool for a Product Manager targeting AI/Data roles. It
uses the Gemini API for all AI generation, with no separate backend beyond
that (client-side app, calling Gemini directly, streaming responses).

CORE CONCEPT
The user pastes their CV once (stored in browser localStorage, editable
anytime) and a job description per application. Four actions operate on
that pair. Never invent facts, employers, metrics, or outcomes not present
in the user's pasted CV — every claim in generated output must trace back
to it.

NARRATIVE PRINCIPLES (apply to every generated piece of writing)
- Emphasize skills and learning, not duration in a role.
- Stay positive — frame every past mission as a deliberate opportunity.
- If there are freelance periods or gaps, frame them as a deliberate
  strategic choice, never apologetically.
- Lead with impact and quantified value delivered wherever the CV supports it.

LAYOUT
A left panel with: a CV textarea (persisted in localStorage, with an
"Edit CV" toggle so it's collapsed once saved), a job description textarea,
optional Company and Role fields, and four tab buttons for the actions
below. A right panel renders the streamed Gemini output as formatted
Markdown (headings, tables, lists, bold) with a "Copy" button.

ACTION 1 — Match CV
Given the CV and job description, have Gemini produce, in this order:
1. A structured JSON profile extracted from the CV (name, target titles,
   summary, hard/soft skills, tools, experiences with org/role/period/
   context/actions/results/themes, certifications) — render it as a
   readable summary, not raw JSON, in the UI.
2. A relevance map: a table of [job requirement | evidence in CV | strength
   High/Medium/Low].
3. A match score: Strong / Good / Partial, with a 2-line honest
   justification naming the biggest strength and the biggest gap.
4. Four labelled edit-suggestion lists: Retitle (headline change),
   Rewrite summary, Downplay/drop (less relevant experience to trim), and
   Elevate/add (relevant items to surface) — each item with a one-line
   reason.
5. A full tailored CV in Markdown applying those edits, preserving every
   factual claim from the source CV (reordering/rephrasing is fine,
   fabrication is not), written in the same language as the job posting.

ACTION 2 — Draft Outreach
Using the CV, job description, and (if the user ran it this session) the
match result as context, generate three assets: a cover letter (~250–300
words: hook → why-me impact proof → fit with the role → call to action), a
recruiter email (subject line + ~120-word body, skimmable), and a LinkedIn
connection message (under 300 characters). Match the job posting's
language. Every quantified claim must trace to the CV.

ACTION 3 — Interview Prep
Given the CV, target company, and target role, generate: a Q&A set
covering "tell me about yourself" (60-90s spoken narrative, not a CV
readout), 3 strengths each tied to a real proof point, 2 honest weaknesses
each with a mitigation already in motion, "why this company/role"
(specific to the company's actual domain/product), and 2-3 role-specific
behavioural questions — each question paired with a suggested answer
outline and 1-2 likely follow-ups. Then STAR-structured stories (Situation/
Task/Action/Result/Learning) for the 2-3 most relevant experiences from the
CV, ~45-60 seconds each when spoken. Finally a one-page cheat sheet: 3 key
story titles with their headline metric, key numbers worth memorizing, 4-5
talking points tuned to this company/role, and 4-5 sharp questions to ask
the interviewer.

ACTION 4 — Track Application
No AI call — a simple local table (persisted in localStorage) with columns:
Company, Role, Priority (High/Med/Low), Match (Strong/Good/Partial/blank),
Status (To apply/Applied/Screening/Interview 1/Interview 2/Final/Offer/
Rejected/Withdrawn), Source Link, Date Found (auto-filled today), Date
Applied, Contact Name, Contact Link, Next Follow-up (date), Notes. A form
above the table to add/edit a row, sortable columns, and a "Copy as TSV"
button per row so it can be pasted into an external spreadsheet. Highlight
rows red if Next Follow-up is in the past and status isn't
Rejected/Withdrawn/Offer, amber if within 3 days.

TECHNICAL REQUIREMENTS
- Use the Gemini API with streaming so text appears incrementally in the
  output panel, not all at once.
- No backend server beyond direct Gemini API calls from the client; API key
  entered by the user and stored locally, never hardcoded.
- CV and tracker data persist in browser localStorage across reloads.
- Clean, minimal UI — light and dark mode support, readable typography, no
  placeholder Lorem Ipsum content.
- Guard against empty submissions: require a job description before
  Actions 1-2, require company+role before Action 3.

Build this now as a working app.
```

---

## Notes for Nicolas
- This targets **Google AI Studio's Gemini models** as a from-scratch
  rebuild, not a port of the Claude Code skills — it's a good way to
  compare a Gemini-only build against the Claude-based system already in
  this repo.
- It deliberately **excludes your actual CV text** — you'll paste it into
  the generated app once it's built, same workflow as the current tool.
- If AI Studio's output needs a second pass, the fastest fix is usually to
  paste back a specific complaint ("the tracker table isn't sortable",
  "streaming isn't working") rather than re-running the whole prompt.
