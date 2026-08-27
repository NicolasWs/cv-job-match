---
name: find-opportunities
description: Scan LinkedIn, Welcome to the Jungle, HelloWork, and Glassdoor for new Product Manager / Product Owner roles matching Nicolas's search profile, score each against his CV, update the job_search_matches.xlsx tracker, and produce a Company Radar — the 10–15 companies most actively hiring for his target profile, with a positioning angle for each. Use whenever the user asks to "find opportunities", "scan the boards", "run my week", "look for jobs", "update the job matches", "scout roles", or "which companies should I target".
---

# Find Opportunities (multi-board)

Scrape → merge → filter → score → **Company Radar** → tracker update.
Runs entirely in-session via the Apify connector. Never applies to a job or
contacts anyone — it only finds, scores, and logs.

## Inputs (from the cv-job-match repo)

- **`config/search-profile.yaml`** — single source of truth: titles, location,
  work modes, filters, target sectors, scoring weights, and (if present) a
  `boards:` section saying which boards to scan. Missing file → ask, don't guess.
- **`context/cv-master.md`** / **`context/cv-master-fr.md`** — the CV to score
  against. Never assume skills/experience not present in it.
- **`job_search_matches.xlsx`** — the tracker at the repo root; updated in
  place, never replaced.

## Procedure

### 1. Load config and CV
Read the yaml and the CV. Note `scoring.weights` (must sum to 1.0) and all
`filters.*`. If the yaml has a `boards:` section, scan exactly those boards;
otherwise default to all four below.

### 2. Fan out the scrapes (parallel, one actor per board)
Use the Apify connector (`mcp__remote-devices__Apify__*` tools). **Start all
runs first, then poll them together** (`get-actor-run`) until each reaches
`SUCCEEDED`, then pull results with `get-dataset-items`. Scrapes take minutes;
keep polling rather than giving up.

| Board | Actor | Input mapping (from config) |
|---|---|---|
| LinkedIn | `valig/linkedin-jobs-scraper` | `{"titles": search.titles, "location": search.location, "workModes": search.work_modes, "maxAgeDays": filters.max_age_days}` |
| Welcome to the Jungle | `clearpath/welcome-to-the-jungle-jobs-api` | one run per title (or comma-join): `{"query": <title>, "location": "Paris", "countryCode": "FR", "datePosted": <from max_age_days>, "includeDetails": true, "maxItems": 100}` |
| HelloWork | `solidcode/hellowork-scraper` | `{"searchQueries": search.titles, "location": "Paris", "datePosted": <from max_age_days>, "includeJobDetails": true, "maxResults": 150}` |
| Glassdoor | `valig/glassdoor-jobs-scraper` | one run per title: `{"keywords": <title>, "location": "Paris (France)", "daysOld": filters.max_age_days, "limit": 100}` |

If an actor id fails, `search-actors` for the board name and use the closest
match (prefer highest `totalUsers`). If a board's run fails after one retry,
**continue with the boards that succeeded** and report which board was skipped
and why — a partial scan beats no scan. Never fabricate listings.

### 3. Normalise and merge across boards
Map every raw item to
`{id, title, company, location, salary, contract_type, posted_at, age_days,
url, description, source}` where `source` ∈ {linkedin, wttj, hellowork,
glassdoor}.

Cross-board dedup (the same posting appears on several boards):
- exact same URL → duplicate;
- else normalise `company` (lowercase, strip legal suffixes like SAS/SA/SARL)
  + normalise `title` (lowercase, strip H/F, F/H, CDI, seniority fluff) —
  same pair → duplicate.
- Keep the copy with the richest `description`; record the other boards in a
  `also_on` list (it's a useful signal — a role posted on 3 boards is being
  pushed hard).

### 4. Filter
Same rules as `pipeline/filter_jobs.py`, applied in-session:
`exclude_company_patterns` (regex, case-insensitive), `exclude_title_patterns`,
`max_age_days`, `include_freelance`, `prefer_only_target_sectors`. Report the
funnel: scraped per board → merged → after dedup → after each filter.

### 5. Score against the CV
Score each survivor **out of 100** with the config weights (role_fit,
domain_fit, skills_match, location_logistics, company_appeal). Two one-line
notes per job: **Why it fits** (tied to a real CV fact) and **Gaps / Risks**
(honest; never invent a strength). ≤200 chars each.

### 6. Company Radar — the 10–15 companies to target
Aggregate the scored list **by company**:
- `openings` = matching roles this scan, `best_score`, `avg_score`,
  `sector_hit` = matches a `target_sectors` name, `multi_board` = any posting
  seen on 2+ boards.
- Rank by: best_score first, then openings, then sector_hit. Take the top
  10–15 (exclude anything matching `exclude_company_patterns`).
- For each company write two lines: **Angle** — which of Nicolas's proof
  points to lead with for THIS company (from the CV, e.g. Natixis/LBPAM for
  banks, Woon/TradeValue for AI product) and **CV variant** — which master CV
  / library CV to start from and the one headline change to make.

Write this to `applications/target-companies-YYYY-MM-DD.md` (dated, so past
radars remain comparable) and show the table in chat. This is the strategic
output: it turns "a list of ads" into "a target list Nicolas works proactively",
including spontaneous applications to companies with several near-miss postings.

### 7. Update the tracker
Update `job_search_matches.xlsx` keyed by Job URL (fallback company+title):
- never overwrite a score/notes a previous run or the user already filled;
- new jobs append; vanished jobs stay;
- add a **`Source`** column if the sheet doesn't have one yet (values:
  linkedin / wttj / hellowork / glassdoor, plus `+N boards` when multi-posted);
- header: `Rank | Job Title | Company | Industry | Location | Seniority |
  Date Posted | Salary Range | Match Score (/100) | Why it fits | Gaps /
  Risks | Job URL | Source`; re-sort by score, Rank from 1.
- Read the `xlsx` skill before writing.

### 8. Deliver and hand off
Send the updated xlsx and the Company Radar md (SendUserFile), then commit
both back to their repo paths. In chat: top 5–8 jobs + the radar table. Then
stop and offer the next stage: run `cv-match` (with its refinement loop) on
the picks, or `run-my-week` to chain the whole pipeline. Never build packages
or contact anyone from this skill.

## Config extension (optional, in search-profile.yaml)
```yaml
boards:
  linkedin: true
  wttj: true
  hellowork: true
  glassdoor: true
```
Absent section = all four. This keeps the yaml the single source of truth.
