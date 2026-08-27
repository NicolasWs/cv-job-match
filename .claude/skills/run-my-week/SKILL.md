---
name: run-my-week
description: Orchestrate Nicolas's full weekly job-search pipeline end to end — scan all job boards (find-opportunities), pick targets, then for each target run company-intel, cv-match with its refinement loop, and write-outreach, and assemble a ready-to-send application package per job. Use when the user says "run my week", "run the pipeline", "full run", or wants to go from scan to application packages in one go.
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
tracker update ◀── application package  ◀── CHECKPOINT 2 (review)
```

## State
Keep pipeline state in `data/pipeline-state.json` in the cv-job-match repo:
```json
{"run_date": "YYYY-MM-DD", "stage": "scan|select|build|review|done",
 "selected_jobs": [{"id": "", "company": "", "title": "", "url": "",
                    "status": "pending|intel|cv|outreach|packaged",
                    "cv_score": null, "letter_score": null}]}
```
Update it after every stage. If a run is interrupted, a later "run my week"
resumes from `stage` instead of re-scraping — that's what makes the pipeline
restartable rather than a long prompt.

## Stages

### 1. Scan
Invoke the **find-opportunities** skill (multi-board scan, scoring, tracker
update, Company Radar). If it ran within the last 3 days and the tracker is
fresh, offer to skip re-scraping and reuse the current tracker.

### 2. CHECKPOINT 1 — target selection (human)
Present the top jobs + Company Radar and ask which to build applications for
(AskUserQuestion, multi-select). **Unattended rule:** if nobody answers or
the session is clearly unattended (scheduled run), auto-select up to 3 jobs
with score ≥ 75 that are not already `packaged` in a previous state file,
state that assumption at the top of the output, and continue.

### 3. Build (per selected job, in order)
For each job — running the independent research in parallel where possible:
1. **company-intel** (light pass) — strengths, risks, what Nicolas brings.
   Skip if an `intel-<company>.md` newer than 30 days exists in the repo.
2. **cv-match** — full skill including its blind-evaluator refinement loop.
   Record the final score and trajectory in the state file.
3. **write-outreach** — full skill including its loop, fed the cv-match
   output and the intel notes.
4. **Package** — create `applications/YYYY-MM-DD_<Company>_<Role-slug>/`:
   - `package.md` — posting link, match score + trajectory, residual gaps,
     the three outreach assets, next actions;
   - tailored CV as `.docx` (via the docx skill, from the final cv-vN.md);
   - copy of the intel notes.

### 4. CHECKPOINT 2 — review before anything leaves
Send each package (SendUserFile + commit to the repo folder) and stop.
Applying, emailing, or messaging is **always** the human's move — the
pipeline's contract is "ready-to-send", never "sent". This checkpoint is not
optional, attended or not.

### 5. Close the loop
- Update `job_search_matches.xlsx`: status column → `Package ready`,
  cv score refreshed.
- Append a run summary to `data/pipeline-state.json` and a 5-line recap in
  chat: jobs scanned, funnel, packages built, scores, what needs Nicolas's
  decision.

## Scheduling
If the user wants this weekly, create a **scheduled task** (create_trigger,
e.g. Monday 08:00 Europe/Paris) whose prompt is: open the cv-job-match
folder, run the `run-my-week` skill unattended (checkpoint-1 auto-select
rule applies, checkpoint 2 still stops). Never use local cron tools.

## Failure policy
A stage that fails for one job marks that job `blocked` in the state file
with a one-line reason and moves on to the next job — one broken posting
must not sink the run. Report all blocked jobs in the recap.
