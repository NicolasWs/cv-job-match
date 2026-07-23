# CV & Cover Letter Tool — User Guide

A practical guide for Nicolas to run the job-search prototype from the command
line, with an optional paste-in UI helper.

---

## 1. What this tool does

You give it **your CV** (once) and **a job description** (per role). It then:

| You say… | The tool does… | Skill used |
|---|---|---|
| "Run cv-match on this" | Scores fit, lists edits, writes a tailored CV | `cv-match` |
| "Draft outreach" | Cover letter + recruiter email + LinkedIn message | `write-outreach` |
| "Prep me for the interview" | Q&A + STAR stories + 1-page support sheet | `interview-prep` |
| "Log this job" | Adds a row to your Google Sheet tracker | (Drive) |

Everything runs **inside Claude Code** — the skills are instructions Claude
loads automatically. There is no server to start and no API key to manage.

---

## 2. One-time setup

### 2a. Prerequisites
- **Claude Code** installed (CLI, desktop, or web) — https://claude.ai/code
- This repository open as your working folder.
- **Google Drive connected** in Claude (for the tracker). Already done if the
  tracker sheet exists on your Drive.

### 2b. Save your CV once
Open Claude Code in this repo and paste:

```
Here is my CV. Save it to context/cv-master.md so every skill reuses it:

<<< paste your full CV text here >>>
```

From then on, every skill reads your CV automatically — you never paste it again.

> Optional but recommended: also ask Claude to create
> `context/experience-bank.md` (one STAR block per mission: Opensee, Natixis,
> Palo IT, Trade Value/Woon) and `context/narrative-rules.md` (your tone +
> narrative principles). This sharpens every output.

---

## 3. Daily workflow — one job, start to finish

**Step 1 — Match.** Paste a posting and say:
```
Run cv-match on this job:

<<< paste the full job description here >>>
```
You get: match score, relevance map, four edit lists (retitle / rewrite summary
/ drop / elevate), and a tailored CV.

**Step 2 — Outreach.** If the match looks good:
```
Draft outreach for this role.
```
You get a cover letter, a recruiter email, and a LinkedIn message. Ask for
variants freely: "shorter", "warmer", "more technical", "in French".

**Step 3 — Track it.**
```
Log this job in the tracker: status Applied, priority High.
```
Claude appends a row to your Google Sheet.

**Later — Interview.** When you get an interview:
```
Prep me for the interview at <company> for <role>.
```
You get a Q&A set, STAR stories, and a one-page support sheet.

---

## 4. Skills reference

| Skill | Trigger phrases | Output |
|---|---|---|
| `cv-match` | "match", "tailor the CV", "score this role" | edits + tailored CV |
| `write-outreach` | "draft outreach", "cover letter", "write to them" | 3 drafts |
| `interview-prep` | "interview prep", "Q&A", "tell me about yourself", "storytelling" | Q&A + STAR + support sheet |

You don't have to name the skill — natural language triggers the right one.

---

## 5. The tracker

Your Google Sheet: **Job Application Tracker — Nicolas**.
Columns: Company · Role · Priority · Match · Status · Source/Link · Date Found ·
Date Applied · Contact Name · Contact Email/LinkedIn · Last Action · Last Action
Date · Next Follow-up · Assets · Notes.

**One-time polish (2 min):** open the sheet → *Format ▸ Conditional formatting*
and add (rules are in `context/tracker.md`):
- Overdue follow-up → red
- Follow-up within 3 days → amber
- Priority = High & active → green row

---

## 6. Optional UI helper (paste CV + job description)

For a friendlier paste experience, open **`tools/cv-job-composer.html`** in any
browser (double-click the file — it works fully offline, no install).

How it works:
1. Paste your CV (or leave blank if already saved to `context/cv-master.md`).
2. Paste the job description.
3. Pick an action (Match / Match + Outreach / Interview prep).
4. Click **Build prompt** → **Copy**.
5. Paste the result into Claude Code and send.

It's a **prompt composer**: it assembles a clean, correctly-delimited prompt for
you to paste into Claude. It does not call Claude itself (that keeps it
zero-setup and key-free). Think of it as a tidy on-ramp to the CLI.

---

## 7. Limitations (by design, for now)

- **Finding & contacting real people** — the tool can tell you *who* to target
  and draft the messages, but it can't discover named contacts or send messages
  (no LinkedIn/email access). You run the search and send manually.
- **Formatting the tracker** — Claude can write rows via Drive, but conditional
  formatting is a one-time manual setup (section 5).
- **Never invents facts** — every metric traces to your CV. If a number isn't in
  your source, outputs stay qualitative.

---

## 8. Troubleshooting

| Problem | Fix |
|---|---|
| A skill isn't triggering | Name it explicitly: "use the cv-match skill" |
| CV not being picked up | Confirm `context/cv-master.md` exists, or paste inline |
| Tracker edits fail | Re-check Google Drive is connected in Claude |
| Git push fails (403) | Repo write access not granted; work stays local + on Drive. Grant access at https://claude.ai/admin-settings/claude-in-slack |
