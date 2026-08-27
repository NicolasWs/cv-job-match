# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A personal job-search pipeline for Nicolas Wajs (Product Manager, AI/Data, Paris). Two loops that share the same config and CVs:

1. **Weekly scrape (n8n, automated)** — Apify scrapes LinkedIn → Python/JS filters → dedupes against `data/seen-jobs.json` → drops `jobs-YYYY-MM-DD.json` into Google Drive `JobApplications` folder.
2. **On-demand (Claude, conversational)** — score jobs against the CV, build tailored application packages, prep for interviews, log applications.

The split is deliberate: n8n does cheap repetitive work on a schedule; Claude does judgment work only when asked. See [README.md](README.md) for the user-facing workflow and [docs/USER-GUIDE.md](docs/USER-GUIDE.md) for the full agent/skill/task model.

## Single source of truth: `config/search-profile.yaml`

Everything downstream reads from this one file — search titles, filter patterns, target sectors, scoring weights, CV language, Drive folder. When the user asks to "add Amundi to targets" or "allow freelance roles", edit this file, then sync into the n8n workflow:

```bash
python3 pipeline/config_to_n8n.py --write   # rewrites n8n/weekly-job-scrape.json in place
```

**Critical duplication:** filter logic exists twice — Python ([pipeline/filter_jobs.py](pipeline/filter_jobs.py)) and JavaScript (inside the n8n `Code` node in [n8n/weekly-job-scrape.json](n8n/weekly-job-scrape.json)), because the n8n container has no Python. `config_to_n8n.py` keeps the *config* in sync automatically, but if you change filter *logic*, change both files.

## Skills, mostly no sub-agents

Every user-facing task runs as **a single Claude session reading a skill's instructions** — the `Agent`/subagent tool is not used, with one deliberate exception below. Skills live in `.claude/skills/<name>/SKILL.md`:

| Skill | Purpose | Handoff |
|---|---|---|
| `find-opportunities` | Scan LinkedIn + WTTJ + HelloWork + Glassdoor, score each posting (0-10 Fit Score), build a Company Radar | its scored list feeds `cv-match` / `run-my-week` |
| `cv-match` | Parse CV, score fit vs one JD (Match Score: Strong/Good/Partial), produce edit list + tailored CV, refine the draft in a loop | its `structured_profile` + Match Score feed the other two in the same session |
| `write-outreach` | Cover letter + recruiter email + LinkedIn message, refined in a loop | reuses `structured_profile` if `cv-match` ran |
| `interview-prep` | Q&A + STAR stories + one-page cheat sheet | standalone or after a match |
| `run-my-week` | Orchestrates scan → target selection → per-job build → package, across the others | writes the Job Application Tracker Sheet for jobs actually pursued |

**The exception:** `cv-match` and `write-outreach` each run a generator→evaluator refinement loop that spawns a **blind critic subagent** (Agent tool) per round — it sees only the posting, a frozen requirement list, and the current draft, never the generator's reasoning or prior scores, so it can't rubber-stamp its own output. This needs the Agent tool, so it **only runs in a Claude Code/Cowork session**. [app/server.py](app/server.py) calls the model APIs directly with no subagent mechanism, so there it degrades to one fresh-context self-review pass per that skill's documented fallback — same skill file, same result quality on the first pass, just no independent second opinion. `find-opportunities` and `run-my-week` use no subagents at all.

These files are read on every request by both Claude Code sessions and [app/server.py](app/server.py) — edits take effect on the next run, no restart needed. If you edit a skill, both entry points improve (modulo the subagent exception above).

The `prompts/build-package.md` file is a separate, older workflow for building packages directly from the weekly scrape results (bypassing the skill split); the newer path is `cv-match` → `write-outreach`.

## CV language selection

- `cv.language: en` → `context/cv-master.md`
- `cv.language: fr` → `context/cv-master-fr.md`
- `cv.language: auto` → detect the posting's language and use the matching CV

**Always read `context/cv-master-fr.md` as well**, even when writing English output — it is the richer fact source (exact stack, Natixis/Opensee/Woon metrics, full AI certification list). This is enforced in every skill and in `build_system()` in `app/server.py`.

## Filter engine

[pipeline/filter_jobs.py](pipeline/filter_jobs.py) is used from n8n and directly. Notable behavior:

- Uses **word-boundary regex** on exclusion patterns so `ESN` doesn't match `Dessein`.
- **Missing age** → keep the job (don't silently drop). Only drops when age is parseable and exceeds `max_age_days`.
- Dedupes twice: within the batch (`batch_ids`) and across runs (`seen_ids` from `data/seen-jobs.json`).
- Sorts kept jobs: target-sector hits first, then freshest.
- `data/seen-jobs.json` **is committed** (cross-run dedupe history); `data/last-raw.json` and `data/*.tmp.json` are git-ignored.

Test filters against a real Apify dump without burning credits:
```bash
python3 pipeline/filter_jobs.py \
  --config config/search-profile.yaml \
  --input data/last-raw.json \
  --seen  data/seen-jobs.json
```
Prints a breakdown to stderr — tune the config until the "KEPT" count and dropped examples look right before triggering a real run.

## Local web app

[app/server.py](app/server.py) is a small Flask app (port 5001) that runs the three streaming skills through the Claude API, with automatic fallback across configured providers (Anthropic → Mistral → Google → OpenAI). Setup and troubleshooting: [app/README.md](app/README.md).

Key implementation notes:
- Provider is "configured" only when its env var is set — never hardcode keys. `.env` is loaded via `python-dotenv` at startup and is git-ignored.
- The four providers are normalized to one wire format (`data: {"text": "..."}` SSE) so the frontend doesn't know which model ran.
- If a model fails **before** any output → transparently fall back with a `⚠️` notice in the stream. If it fails **after partial output** → surface the error rather than splicing in another model.
- `/api/log` is pure Python (no LLM) — returns a tab-separated row to paste into the Google Sheet tracker.

## Applications output

Generated packages land in `applications/{YYYY-MM-DD}_{Company}_{Role-slug}/package.md` and are uploaded to a matching Drive subfolder. `applications/Job_Matches_Paris_ProductAI.xlsx` is the local mirror of the scored spreadsheet.

## Hard rules that show up across the codebase

- **Never invent experience, metrics, employers, or dates.** Every claim must trace to one of the CV files. When a required credential is missing, name the gap honestly — don't fabricate.
- **Match the posting's language natively** — a French posting gets French written natively, not translated English.
- **Freelance since Jul 2025 is a deliberate strategic choice**, not a gap — frame it accordingly in every generated asset.
- **No auto-apply, no auto-messaging.** Everything generates drafts; the user sends them manually. LinkedIn blocks automated outreach.
- **Consulting/ESN exclusion is aggressive** by design (33+ named companies in `exclude_company_patterns`). If a user asks for a package on an excluded company, build it but say plainly it's normally filtered and why.

## Setup dependencies

```bash
pip3 install pyyaml                     # for pipeline/*.py
pip install -r app/requirements.txt     # for the local web app (Flask, anthropic, requests, python-dotenv)
```

No lint, test, or build commands are configured — this is a small script + skills repo, not a packaged application.
