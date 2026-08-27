---
name: run-my-week
description: Orchestrate Nicolas's full weekly job-search pipeline end to end — scan all job boards (find-opportunities), pick targets, then for each target run company-intel, cv-match with its refinement loop, and write-outreach, log pursued jobs to the Job Application Tracker, and assemble a ready-to-send application package per job. Use when the user says "run my week", "run the pipeline", "full run", or wants to go from scan to application packages in one go.
---

# Run My Week (orchestrator)

Chains the specialist skills into one pipeline with persistent state and two
human checkpoints. Each specialist stays single-purpose; this skill only
routes, sequences, and assembles — it contains no scraping or writing logic
of its own.

```
find-opportunities ──▶ CHECKPOINT 1 ──▶ per job: company-intel ─▶ cv-match(loop)
      (scan+radar)      (pick targets)         └▶ write-outreach(loop)
                                                        │
Log to Tracker ◀── application package  ◀── CHECKPOINT 2 (review)
   (Google Sheet)
```

**Subagent note:** the cv-match/write-outreach refinement loops need the
Agent tool and only run in a Claude Code/Cowork session; in `app/server.py`
they degrade to a single self-review pass per that skill's own fallback —
run-my-week itself has no subagent logic of its own, so it works the same
either way except for that inherited difference.

## State
Keep pipeline state in `data/pipeline-state.json` in the cv-job-match repo:
```json
{"run_date": "YYYY-MM-DD", "stage": "scan|select|build|review|done",
 "selected_jobs": [{"id": "", "company": "", "title": "", "url": "",
                    "status": "pending|intel|cv|outreach|packaged|logged",
                    "fit_score": null, "match_score": null,
                    "cv_draft_score": null, "letter_score": null}]}
```
`fit_score` is find-opportunities' 0-10 screening score; `match_score` is
cv-match's Strong/Good/Partial judgment — keep them distinct, they answer
different questions. Update state after every stage so an interrupted run
resumes instead of re-scraping.

## Stages

### 1. Scan
Invoke **find-opportunities** (multi-board scan, 0-10 Fit Score, Company
Radar). If it ran within the last 3 days and the local list is fresh, offer
to skip re-scraping and reuse it.

### 2. CHECKPOINT 1 — target selection (human)
Present the top jobs (by Fit Score) + Company Radar and ask which to build
applications for (AskUserQuestion, multi-select). **Unattended rule:** if
nobody answers or the session is clearly unattended (scheduled run),
auto-select up to 3 jobs with **Fit Score ≥ 8** (the green band) not already
`packaged` in a previous state file, state that assumption at the top of the
output, and continue.

### 3. Build (per selected job, in order)
For each job:
1. **company-intel** (light pass). Skip if an `intel-<company>.md` newer
   than 30 days exists.
2. **cv-match** — full skill including its Match Score and, in a Claude
   Code/Cowork session, its refinement loop. Record Match Score and CV Draft
   Score trajectory in the state file.
3. **write-outreach** — full skill including its loop, fed the cv-match
   output and the intel notes.
4. **Package** — create `applications/YYYY-MM-DD_<Company>_<Role-slug>/`:
   `package.md` (posting link, Match Score, CV Draft Score trajectory,
   residual gaps, the three outreach assets, next actions), tailored CV as
   `.docx`, copy of the intel notes.

### 4. CHECKPOINT 2 — review before anything leaves
Send each package (SendUserFile + commit to the repo folder) and stop.
Applying, emailing, or messaging is **always** the human's move — the
pipeline's contract is "ready-to-send", never "sent". Not optional, attended
or not.

### 5. Log and close the loop
For each job the human confirms they're pursuing (not just built — actually
moving forward): append a row to the real **Job Application Tracker —
Nicolas** Google Sheet via the Drive connector (the same "Log" action
described in `docs/USER-GUIDE.md` §2.6 Task 3), using the tracker's real
columns (`tracker/job-tracker-model.md`) — Company, Role, Priority (from
Fit Score band), Match (Strong/Good/Partial from cv-match), Status "To
apply", Source/Link, Date Found. This is the only place in the pipeline that
writes to that Sheet — find-opportunities' local list stays separate.

Then: append a run summary to `data/pipeline-state.json` and a 5-line recap
in chat: jobs scanned, funnel, packages built, jobs logged, what needs
Nicolas's decision.

## Scheduling
If the user wants this weekly, create a **scheduled task** (create_trigger,
e.g. Monday 08:00 Europe/Paris) whose prompt is: open the cv-job-match
folder, run the `run-my-week` skill unattended (checkpoint-1 auto-select
rule applies, checkpoint 2 still stops). Never use local cron tools.

## Failure policy
A stage that fails for one job marks that job `blocked` in the state file
with a one-line reason and moves on to the next job. Report all blocked jobs
in the recap.
