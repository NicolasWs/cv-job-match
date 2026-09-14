# CV & Cover Letter Tool — Architecture v2

Status: **v2 — in development (feature branch)**

> See also: [architecture-v1.md](architecture-v1.md) for the v1 design this replaces.

---

## 1. Overview

v2 refactors the pipeline from 5 monolithic Claude Code skills (chained by a single orchestrator prompt) into **7 specialized agents** with explicit **human checkpoints** between stages. Each agent has a single responsibility, reads from shared context files, and writes structured outputs tracked by a per-job state file (`application_state.json`).

### Design principles

1. **Single responsibility** — each agent does one thing well. No agent reads another agent's internal reasoning.
2. **Stateful** — `application_state.json` tracks every job through a state machine. The orchestrator knows exactly where each job is.
3. **Human checkpoints** — three review gates where the human approves, rejects, or revises before the pipeline continues.
4. **Shared context** — career narrative, project stories, CV variants, and letter templates live in `context/` and are read by agents instead of regenerated each run.
5. **Additive, not destructive** — v1 skills remain functional. A `v2_mode` flag in `config/search-profile.yaml` controls which path runs.

---

## 2. Agent Architecture

```
                    ┌─────────────────────────────────┐
                    │       ORCHESTRATOR (main)        │
                    │  routes + state mgmt + checkpoints│
                    └──────────┬──────────────────────┘
                               │ routes to
          ┌────────┬───────────┼───────────┬────────┐
          ▼        ▼           ▼           ▼        ▼
       SCOUT  MATCH_ANALYZER  CV_TAILOR  NEWS_RESEARCH  LETTER_WRITER
                                                    │
                                               ┌────┴────┐
                                               ▼         ▼
                                          INTERVIEW    TRACKER
                                            _PREP
```

### Agent table

| # | Agent | Skill path | Role | Human checkpoint |
|---|-------|-----------|------|-----------------|
| 0 | ORCHESTRATOR | `.claude/skills/orchestrator/` | Routes work, manages state, presents checkpoints | Yes (presents all 3) |
| 1 | SCOUT | `.claude/skills/scout/` | Scan LinkedIn + job boards, score postings, build Company Radar | No |
| 2 | MATCH ANALYZER | `.claude/skills/match-analyzer/` | Parse CV, score fit vs JD, produce edit plan | Yes (match review) |
| 3 | CV TAILOR | `.claude/skills/cv-tailor/` | Apply edit plan, run blind-evaluator loop, output tailored CV | Yes (CV review) |
| 4 | NEWS RESEARCH | `.claude/skills/news-research/` | Search for 3-5 recent company news items, extract hooks | No |
| 5 | LETTER WRITER | `.claude/skills/letter-writer/` | Draft cover letter using narrative + templates + news | Yes (package review) |
| 6 | INTERVIEW PREP | `.claude/skills/interview-prep-v2/` | Generate Q&A + STAR stories from project library | No |
| 7 | TRACKER | `.claude/skills/tracker/` | Log to Google Sheet, maintain state, generate dashboard | No |

---

## 3. Data Flow

```
SCOUT
  → applications/{job_id}/job-posting.md
  → application_state.json (stage: scouted)

MATCH ANALYZER
  reads: context/cv-master.md, context/cv-master-fr.md, job-posting.md
  → applications/{job_id}/analysis.md
  → applications/{job_id}/edit-plan.json
  → application_state.json (stage: matched, match_score set)

  ── CHECKPOINT 1: Human reviews match score + edit plan ──

CV TAILOR
  reads: edit-plan.json, context/cv-master.md, context/cv-library/*
  → applications/{job_id}/cv-v{version}.md
  → applications/{job_id}/cv-changelog.md
  → application_state.json (stage: cv_tailored, cv_version set)

  ── CHECKPOINT 2: Human reviews tailored CV ──

NEWS RESEARCH
  reads: job-posting.md, company name
  → applications/{job_id}/news-research.md
  → application_state.json (stage: news_researched)

LETTER WRITER
  reads: context/narrative.md, context/letter-templates/*, news-research.md, analysis.md
  → applications/{job_id}/outreach-v{version}.md
  → application_state.json (stage: letter_drafted, letter_version set)

  ── CHECKPOINT 3: Human reviews full package ──

INTERVIEW PREP (on demand)
  reads: context/project-stories.md, analysis.md
  → applications/{job_id}/interview-prep.md

TRACKER
  reads: application_state.json
  → Google Sheet log entry
  → DASHBOARD.md
  → application_state.json (stage: sent / closed)
```

---

## 4. Human Checkpoints

Three review gates where the pipeline pauses for human input:

| Checkpoint | After agent | What the human sees | Decision |
|-----------|-------------|---------------------|----------|
| 1. Match review | MATCH ANALYZER | Match score, gap analysis, edit plan | Approve / Reject / Revise |
| 2. CV review | CV TAILOR | Tailored CV + changelog | Approve / Reject / Revise |
| 3. Package review | LETTER WRITER | Full package (CV + letter + news) | Approve / Reject / Revise |

On **approve**: orchestrator advances to the next stage.
On **reject**: orchestrator marks the job as rejected in state, offers to re-scout or close.
On **revise**: orchestrator loops the agent with the human's feedback notes.

---

## 5. application_state.json State Machine

```
scouted → matched → cv_tailored → news_researched → letter_drafted → package_ready → sent → interview → closed
```

Each transition is gated by either an agent completion or a human checkpoint.

See [state-schema.md](state-schema.md) for the full schema definition.

---

## 6. Shared Context Files

| File | Read by |
|------|---------|
| `context/cv-master.md` | Match Analyzer, CV Tailor |
| `context/cv-master-fr.md` | Match Analyzer, CV Tailor |
| `context/narrative.md` | Letter Writer, Interview Prep |
| `context/project-stories.md` | Interview Prep, Letter Writer |
| `context/cv-library/summary-variants.md` | CV Tailor |
| `context/cv-library/experience-emphasis.md` | CV Tailor |
| `context/letter-templates/hooks.md` | Letter Writer |
| `context/letter-templates/story-framings.md` | Letter Writer |
| `context/letter-templates/closings.md` | Letter Writer |

These are **living documents**. The orchestrator can prompt the human to update them after each application cycle.

---

## 7. v1 → v2 Migration

| v1 Skill | v2 Agent(s) |
|----------|-------------|
| `find-opportunities` | SCOUT |
| `cv-match` | MATCH ANALYZER + CV TAILOR |
| `write-outreach` | NEWS RESEARCH + LETTER WRITER |
| `interview-prep` | INTERVIEW PREP |
| `run-my-week` | ORCHESTRATOR + TRACKER |

v1 skills remain in `.claude/skills/` during the transition. They are marked deprecated in `CLAUDE.md` but not deleted. Deletion is a follow-up PR after v2 is validated in production.

---

## 8. Backward Compatibility

| Concern | Strategy |
|---------|----------|
| v1 skills | Remain untouched, marked deprecated |
| v1 orchestrator | `orchestrator-v1.md` gets a deprecation header |
| v1 Flask app | `app/server.py` unchanged in this PR |
| Mode flag | `config/search-profile.yaml` gets `v2_mode: false` (default) |
| Existing applications/ | v2 agents can read existing files and backfill state |

Rollback: set `v2_mode: false` or revert the PR. v1 is never modified.