---
name: find-opportunities
description: Scan LinkedIn, Welcome to the Jungle, HelloWork, and Glassdoor for new Product Manager / Product Owner roles matching Nicolas's search profile, score each against his CV on the standard 0-10 Fit Score, maintain a local scored-candidates spreadsheet, and produce a Company Radar — the 10–15 companies most actively hiring for his target profile, with a positioning angle for each. Use whenever the user asks to "find opportunities", "scan the boards", "run my week", "look for jobs", "update the job matches", "scout roles", or "which companies should I target".
---

# Find Opportunities (multi-board)

Scrape → merge → filter → score (**0-10 Fit Score**, same scale as the
"score the week" flow in README) → **Company Radar** → local candidates
list. Runs entirely in-session via the Apify connector. Never applies to a
job or contacts anyone — it only finds, scores, and logs.

**This is not the Job Application Tracker.** The canonical **Job
Application Tracker — Nicolas** Google Sheet (`tracker/job-tracker-model.md`)
holds one row per job you're actually pursuing, written only by the explicit
"Log" task or by `run-my-week`'s packaging step. This skill's output is a
wider screening list — every live posting worth a look — kept locally so
scanning doesn't require Drive access and doesn't clutter the curated
tracker with postings nobody decided to pursue yet.

## Inputs (from the cv-job-match repo)

- **`config/search-profile.yaml`** — single source of truth: titles,
  location, work modes, filters, target sectors, `scoring.weights`
  (integer points per dimension, summing to 10), `scoring.min_priority_score`,
  and (if present) a `boards:` section saying which boards to scan. Missing
  file → ask, don't guess.
- **`context/cv-master.md`** / **`context/cv-master-fr.md`** — the CV to
  score against (FR is the richer fact source even for English output).
- **`job_search_matches.xlsx`** — the local scored-candidates list at the
  repo root; updated in place, never replaced.

## Procedure

### 1. Load config and CV
Read the yaml and the CV. Note `scoring.weights` — currently `domain_match`,
`seniority_match`, `ai_relevance`, `target_sector_bonus`,
`recruiter_available`, each an integer point value summing to 10 — and
`scoring.min_priority_score` (currently 6). If the yaml has a `boards:`
section, scan exactly those boards; otherwise default to all four below.

### 2. Fan out the scrapes (parallel, one actor per board)
Use the Apify connector (`mcp__remote-devices__Apify__*` tools). **Start all
runs first, then poll them together** (`get-actor-run`) until each reaches
`SUCCEEDED`, then pull results with `get-dataset-items`. Scrapes take
minutes; keep polling rather than giving up.

| Board | Actor | Input mapping (from config) |
|---|---|---|
| LinkedIn | `valig/linkedin-jobs-scraper` | `{"titles": search.titles, "location": search.location, "workModes": search.work_modes, "maxAgeDays": filters.max_age_days}` |
| Welcome to the Jungle | `clearpath/welcome-to-the-jungle-jobs-api` | one run per title: `{"query": <title>, "location": "Paris", "countryCode": "FR", "datePosted": <from max_age_days>, "includeDetails": true, "maxItems": 100}` |
| HelloWork | `solidcode/hellowork-scraper` | `{"searchQueries": search.titles, "location": "Paris", "datePosted": <from max_age_days>, "includeJobDetails": true, "maxResults": 150}` |
| Glassdoor | `valig/glassdoor-jobs-scraper` | one run per title: `{"keywords": <title>, "location": "Paris (France)", "daysOld": filters.max_age_days, "limit": 100}` |

If an actor id fails, `search-actors` for the board name and use the closest
match (prefer highest `totalUsers`). If a board's run fails after one retry,
**continue with the boards that succeeded** and report which board was
skipped and why. Never fabricate listings.

### 3. Normalise and merge across boards
Map every raw item to
`{id, title, company, location, salary, contract_type, posted_at, age_days,
url, description, source}` where `source` ∈ {linkedin, wttj, hellowork,
glassdoor}.

Cross-board dedup: exact same URL → duplicate; else normalise `company`
(lowercase, strip legal suffixes like SAS/SA/SARL) + normalise `title`
(lowercase, strip H/F, F/H, CDI, seniority fluff) — same pair → duplicate.
Keep the richest `description`; record other boards seen in `also_on` (a
role posted on 3 boards is being pushed hard — a real signal).

### 4. Filter
Same rules as `pipeline/filter_jobs.py`: word-boundary regex on
`exclude_company_patterns` and `exclude_title_patterns` (case-insensitive),
`filters.max_age_days` (missing age → keep, don't silently drop),
`include_freelance`, `prefer_only`. Report the funnel: scraped per board →
merged → after dedup → after each filter.

### 5. Score against the CV — the standard 0-10 Fit Score
Score each survivor the same way the "score the week" flow does: for each
dimension in `scoring.weights`, judge honestly whether the posting earns
that dimension's points (domain/finance-AI overlap, seniority match,
explicit AI/ML relevance, target-sector bonus, a named recruiter present),
sum to a **Fit Score out of 10** — never inflated, a 5 is a real 5. One
line naming the biggest strength and the honest biggest gap. Flag anything
below `scoring.min_priority_score` as low priority (keep it in the list —
don't drop it, just rank it low).

### 6. Company Radar — the 10–15 companies to target
Aggregate the scored list **by company**:
- `openings` = matching roles this scan, `best_fit_score` (/10), `sector_hit`
  = matches a `target_sectors` name, `multi_board` = posting seen on 2+
  boards.
- Rank by: best_fit_score first, then openings, then sector_hit. Take the
  top 10–15 (exclude anything matching `exclude_company_patterns`).
- For each company write two lines: **Angle** — which of Nicolas's proof
  points to lead with for THIS company (from the CV) and **CV variant** —
  which CV language/emphasis to start from.

Write this to `applications/target-companies-YYYY-MM-DD.md` and show the
table in chat.

### 7. Update the local scored-candidates list
Update `job_search_matches.xlsx` at the repo root, keyed by Job URL
(fallback company+title):
- never overwrite a score/notes a previous run or the user already filled;
- new jobs append; vanished jobs stay;
- header: `Rank | Job Title | Company | Industry | Location | Seniority |
  Date Posted | Salary Range | Fit Score (/10) | Priority | Why it fits |
  Gaps / Risks | Job URL | Source`, where `Priority` is
  High/Med/Low derived from the score band (green ≥8 → High, amber 6-7 →
  Med, red <6 → Low) — the same bands README uses; re-sort by score.
- Read the `xlsx` skill before writing.
- If the Google Drive connector is available and `output.drive_folder_id`
  is set, also offer to mirror this list into the `JobApplications` Drive
  folder as README's "re-upload to Drive" step describes — ask first,
  don't write to Drive silently.

### 8. Deliver and hand off
Send the updated xlsx and the Company Radar md (SendUserFile), then commit
both back to their repo paths. In chat: top 5–8 jobs + the radar table. Then
stop and offer the next stage: run `cv-match` on the picks (its own
Strong/Good/Partial match score is a separate, deeper judgment than this
screening Fit Score), or `run-my-week` to chain the whole pipeline. A job
only reaches the **Job Application Tracker** Google Sheet once it's
actually being pursued — never from this skill directly.

## Config extension (optional, in search-profile.yaml)
```yaml
boards:
  linkedin: true
  wttj: true
  hellowork: true
  glassdoor: true
```
Absent section = all four.
