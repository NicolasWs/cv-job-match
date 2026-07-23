# CV & Cover Letter Tool — User Guide

A complete guide for Nicolas: what the system is made of (agents, skills,
tasks), and two ways to run it — Claude Code / Claude Cowork locally, or the
local web app.

---

## 0. Two ways to use this system

| | Claude Code / Cowork (chat) | Local web app |
|---|---|---|
| **How you interact** | Natural-language chat in Claude Code or Cowork | Browser UI at `localhost:5001` |
| **Setup** | Open this repo as your project folder | `pip install`, `.env` with API key(s), `python3 app/server.py` |
| **Model** | Whatever model your Claude Code/Cowork session runs | Pick per run: Sonnet 5, Haiku 4.5, or a fallback provider |
| **Best for** | Iterating conversationally, chaining tasks, editing skills live | A dedicated, form-based workflow you can reuse without a chat |
| **Setup guide** | Section 2, below | `app/README.md` |

Both read the **same** skills (`.claude/skills/`) and the **same** CVs
(`context/cv-master.md`, `context/cv-master-fr.md`) — nothing is duplicated.

---

## 1. System architecture — agents, skills & tasks

### 1.1 Design concept vs. what's actually built

The original design (`docs/architecture-v1.md`) specified **seven
conceptual agents** behind one orchestrator:

| Conceptual agent | Status |
|---|---|
| CV_ANALYZER | ✅ Built — as the `cv-match` skill (merged with JOB_MATCH) |
| JOB_MATCH | ✅ Built — merged into `cv-match` (they always run together) |
| WRITING | ✅ Built — as the `write-outreach` skill |
| NARRATIVE_COACH | ✅ Built — merged into `interview-prep` |
| INTERVIEW_QA | ✅ Built — merged into `interview-prep` |
| LEARNING_PLAN | ⬜ Designed, not yet built (no skill folder exists) |
| JOB_TRACKER_DESIGN | ✅ Delivered as a one-time design (`tracker/job-tracker-model.md`), not a reusable skill — the tracker itself is a Google Sheet, not something you regenerate per run |

**Why skills instead of separate agents:** Claude Code's native mechanism for
"a specialized capability loaded on demand" is a **Skill** — a folder with a
`SKILL.md` that Claude reads automatically when your request matches its
description. That's a closer fit than spinning up separate sub-agents for
each conceptual role, so CV_ANALYZER+JOB_MATCH became one skill
(`cv-match`) and NARRATIVE_COACH+INTERVIEW_QA became one skill
(`interview-prep`) — each pair always runs together in practice anyway.

### 1.2 Sub-agents — none are used

This system does **not** use Claude Code's `Agent`/subagent tool (the
mechanism that spawns an isolated Explore/general-purpose agent with its own
context window). Every task here runs as a **single Claude session reading a
skill's instructions**, not a delegated sub-agent call. This is deliberate:
the tasks are short, single-pass, and benefit from staying in your main
conversation (so you can immediately follow up — "make it shorter", "now log
this job") rather than returning a detached report. If a future task needed
heavy independent research (e.g. deep-diving a company's culture across many
sources), a subagent would be the right upgrade — not needed yet.

### 1.3 Skills reference (the built agents)

Each skill lives in `.claude/skills/<name>/SKILL.md`.

#### `cv-match`
- **Role:** Parse the CV, score fit against one job description, produce an
  actionable edit list and a tailored CV.
- **Inputs:** CV (auto-selected: `context/cv-master-fr.md` for French
  postings, `context/cv-master.md` for English — FR is the richer fact
  source even for English output), job description, optional company name.
- **Outputs:** `structured_profile` (JSON), relevance map (job requirement →
  CV evidence → strength), match score (Strong/Good/Partial), four edit lists
  (retitle / rewrite summary / drop / elevate), full tailored CV in Markdown.
- **Triggers:** "run cv-match", "match this job", "tailor the CV", "score
  this role".
- **Handoff:** its `structured_profile` and positioning feed `write-outreach`
  and `interview-prep` if they run later in the same session.

#### `write-outreach`
- **Role:** Draft a cover letter, recruiter email, and LinkedIn message for
  one posting, reusing narrative principles (skills over duration, freelance
  as deliberate choice, impact-first, stay positive).
- **Inputs:** `structured_profile` from `cv-match` if it ran this session
  (else reads the CV directly), job description, optional company notes.
- **Outputs:** cover letter (~250–300 words), recruiter email (subject +
  body), LinkedIn message (≤300 characters).
- **Triggers:** "draft outreach", "cover letter", "write to them", "email
  the recruiter".
- **Guardrail:** every quantified claim must trace to the CV — no invented
  metrics.

#### `interview-prep`
- **Role:** Build interview material for one company/role: Q&A,
  STAR-structured storytelling, and a one-page cheat sheet.
- **Inputs:** `structured_profile` if available, target company + role,
  optional `context/experience-bank.md` (not yet created — see §7).
- **Outputs:** Q&A set (strengths/weaknesses, "tell me about yourself",
  "why this company", behavioural questions — each with follow-ups), STAR
  stories for the 2–3 most relevant missions, a support sheet (key stories,
  key metrics, talking points, questions to ask them).
- **Triggers:** "interview prep", "Q&A", "tell me about yourself",
  "storytelling", "prep me for the interview".

### 1.4 Tasks reference (what you actually type)

A "task" here is a discrete thing you ask for — each maps to exactly one
skill (or, for tracking, a direct Google Sheets write with no skill/LLM
involved).

| # | Task | Example prompt | Skill / mechanism | Typical output length |
|---|---|---|---|---|
| 1 | **Match** | "Run cv-match on this job: \<paste JD\>" | `cv-match` | ~800–1500 words |
| 2 | **Outreach** | "Draft outreach for this role" | `write-outreach` | ~400 words (3 assets) |
| 3 | **Interview prep** | "Prep me for the interview at Datadog" | `interview-prep` | ~1000–1800 words |
| 4 | **Log** | "Log this job: status Applied, priority High" | Direct Google Sheets append (no skill) | 1 row |

Tasks 1–3 chain naturally in one session: match → outreach → log, then
interview-prep later once an interview is scheduled. You don't need to name
the skill — the trigger phrases above are enough for Claude to pick the
right one.

---

## 2. Using it with Claude Code / Claude Cowork — locally

This section covers running the system as a **local chat session** against
your own clone of the repo (as opposed to a hosted/remote Claude Code
session). Claude Code and Claude Cowork both discover skills the same way —
via the `.claude/skills/` folder at the root of whatever project you open —
so these steps apply to either app; menu wording may differ slightly.

### 2.1 Prerequisites
- **Claude Code** (CLI or desktop app) or **Claude Cowork** installed.
- **Git** installed (`git --version` to check).
- A **Claude subscription or API access** the app is signed into.
- **Google Drive connected** as a data source in the app, so Claude can read
  and append to your tracker sheet.

### 2.2 Get the repo onto your machine

```bash
git clone https://github.com/NicolasWs/cv-job-match.git
cd cv-job-match
git checkout main            # the merged, up-to-date branch
```

If you already have a clone (e.g. from earlier testing the web app), just:
```bash
cd /path/to/cv-job-match
git checkout main
git pull origin main
```

### 2.3 Open it as a project in Claude Code / Cowork

- **Claude Code (CLI):** `cd` into the repo folder, then run `claude` (or
  your launch command) from there — Claude Code auto-loads
  `.claude/skills/` from the current working directory.
- **Claude Code (desktop) / Cowork:** open/add the `cv-job-match` folder as
  your project or workspace root. Skills are discovered the same way — the
  app scans `.claude/skills/*/SKILL.md` in the opened project.

### 2.4 Verify the skills loaded

Ask directly: *"What skills are available in this project?"* — Claude
should list `cv-match`, `write-outreach`, and `interview-prep` with their
one-line descriptions (the same descriptions from §1.3). If it doesn't see
them, confirm you opened the **repo root** (the folder containing
`.claude/`), not a subfolder.

### 2.5 Confirm your CV is loaded

Your CV is already committed at `context/cv-master.md` (English) and
`context/cv-master-fr.md` (French) — nothing to paste. Sanity-check with:
*"Read context/cv-master.md and confirm you have my CV."*

### 2.6 Walk through each task

**Task 1 — Match** (start every new job here):
```
Run cv-match on this job:

<paste the full job description>
```
Expect: structured profile → relevance map → match score → edit
suggestions → full tailored CV, in that order.

**Task 2 — Outreach** (right after a match, same session):
```
Draft outreach for this role.
```
Ask for variants freely: *"shorter"*, *"warmer"*, *"more technical"*, *"in
French"* — no need to re-paste anything, the session already has context.

**Task 3 — Log** (any time after applying):
```
Log this job in the tracker: status Applied, priority High.
```
Claude appends a row to your **Job Application Tracker — Nicolas** Google
Sheet directly via the Drive connection.

**Task 4 — Interview prep** (once an interview is scheduled):
```
Prep me for the interview at <company> for <role>.
```
This can run standalone (new session) or right after a match — either way
it reuses whatever profile/positioning is already in context.

### 2.7 Editing the skills

Skills are just Markdown — open `.claude/skills/cv-match/SKILL.md` (or the
others) in any editor and edit the instructions directly. Claude Code /
Cowork picks up the change on the **next** message in a session; no restart
needed. This is the same file the local web app reads too, so an edit
improves both.

### 2.8 Common issues

| Symptom | Fix |
|---|---|
| Skill doesn't trigger | Name it explicitly: "use the cv-match skill on this job" |
| CV not picked up | Confirm the repo root (containing `context/`) is what's open, not a subfolder |
| Tracker append fails | Re-check Google Drive is connected as a data source in the app |
| Wrong CV language used | The posting's language drives the choice — say "use the French CV" to force it |

---

## 3. Using the local web app

Full setup, `.env` configuration, and troubleshooting: **`app/README.md`**.
Quick summary:

```bash
cd cv-job-match
pip install -r app/requirements.txt
cp .env.example .env        # fill in your real key(s)
python3 app/server.py
open http://localhost:5001
```

Four tabs (Match CV / Draft outreach / Interview prep / Log job), a model
picker (Sonnet 5 default, Haiku 4.5, plus Mistral/Google/OpenAI fallbacks if
configured), and automatic fallback if your primary provider's key fails.

---

## 4. The Google Sheet tracker

**Job Application Tracker — Nicolas** (Google Sheet). Columns: Company ·
Role · Priority · Match · Status · Source/Link · Date Found · Date Applied ·
Contact Name · Contact Email/LinkedIn · Last Action · Last Action Date ·
Next Follow-up · Assets · Notes. Full model and formulas:
`tracker/job-tracker-model.md` and `context/tracker.md`.

**One-time polish (2 min):** open the sheet → *Format ▸ Conditional
formatting* and add:
- Overdue follow-up → red
- Follow-up within 3 days → amber
- Priority = High & active → green row

---

## 5. Limitations (by design, for now)

- **Finding & contacting real people** — the tool tells you *who* to target
  and drafts the messages, but can't discover named contacts or send
  messages (no LinkedIn/email access). You run the search and send manually.
- **`LEARNING_PLAN` isn't built yet** — the original design called for a
  skill that ranks hard skills to deepen and maps them to free training
  resources. Not implemented — ask conversationally in the meantime and
  Claude will do it ad hoc, just without a dedicated, reusable skill.
- **No `context/experience-bank.md` yet** — `interview-prep` falls back to
  extracting stories straight from the CV, which works but is less rich than
  a dedicated STAR-block file per mission (Opensee, Natixis, Palo IT, Trade
  Value/Woon). Worth creating once, per §7 of the original guide.
- **Never invents facts** — every metric traces to your CV. If a number
  isn't in the source, output stays qualitative.

---

## 6. Troubleshooting (general)

| Problem | Fix |
|---|---|
| A skill isn't triggering | Name it explicitly: "use the cv-match skill" |
| CV not being picked up | Confirm `context/cv-master.md` exists in the opened project |
| Tracker edits fail | Re-check Google Drive is connected in the app |
| Local web app issues | See the Troubleshooting section in `app/README.md` |
