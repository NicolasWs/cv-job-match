---
name: find-opportunities
description: Scan LinkedIn, Indeed, Welcome to the Jungle, HelloWork, and Glassdoor for new Product Manager / Product Owner roles matching Nicolas's search profile, score each against his CV on the standard 0-10 Fit Score, maintain a local scored-candidates spreadsheet, and produce a Company Radar — the 10–15 companies most actively hiring for his target profile, with a positioning angle for each. Use whenever the user asks to "find opportunities", "scan the boards", "run my week", "look for jobs", "update the job matches", "scout roles", or "which companies should I target".
---

# Find Opportunities (multi-board)

Scrape → merge → filter → score (**0-10 Fit Score**, same scale as the
"score the week" flow in README) → **Company Radar** → local candidates
list. Primary method runs in-session via the Apify connector; when Apify is
unavailable (quota exhausted, outage, no connector in the current runtime —
see §2b), fall back to driving a logged-in browser directly. Never applies
to a job or contacts anyone — it only finds, scores, and logs.

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
- **jobhub's `settings.dream_job`** — free-text dream-job description,
  fetched once per scan via `tools.jobhub_sync.get_settings()["dream_job"]`
  (see `ai-job-search-nico/tools/jobhub_sync.py`; if jobhub is unreachable it
  returns `None` — treat that the same as an empty dream_job, i.e. skip the
  adjustment in step 5, never block the scan on it).

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
| Indeed | `misceres/indeed-scraper` | one run per title: `{"position": <title>, "country": "FR", "location": "Paris", "maxItems": 100}` (actor has no native age filter — apply `filters.max_age_days` in step 4 instead) |
| Welcome to the Jungle | `clearpath/welcome-to-the-jungle-jobs-api` | one run per title: `{"query": <title>, "location": "Paris", "countryCode": "FR", "datePosted": <from max_age_days>, "includeDetails": true, "maxItems": 100}` |
| HelloWork | `solidcode/hellowork-scraper` | `{"searchQueries": search.titles, "location": "Paris", "datePosted": <from max_age_days>, "includeJobDetails": true, "maxResults": 150}` |
| Glassdoor | `valig/glassdoor-jobs-scraper` | one run per title: `{"keywords": <title>, "location": "Paris (France)", "daysOld": filters.max_age_days, "limit": 100}` |

If an actor id fails, `search-actors` for the board name and use the closest
match (prefer highest `totalUsers`). If a board's run fails after one retry,
**continue with the boards that succeeded** and report which board was
skipped and why. Never fabricate listings.

### 2b. Fallback: direct browser scan (no Apify)
Use when Apify is unreachable — quota/billing error (`platform-feature-disabled`
/ "Monthly usage hard limit exceeded"), an outright API outage, or (in Hermes,
which has no Apify MCP connector) when the REST workaround itself fails. This
is a real scrape, just manual and per-board instead of fan-out — expect it to
take longer and skip the Fit Score/xlsx update unless you loop back through
steps 4–7 by hand. Say plainly that this is the slow/manual path, not Apify,
when reporting results.

**Technique (learned the hard way — don't re-discover this):**
- Needs a logged-in browser session (reuse the existing authenticated session;
  don't attempt credentials yourself — see the vault note in global guidance).
- LinkedIn's current UI ships obfuscated, rotating CSS class names (its
  "AI-powered job search" redesign) — CSS selectors for job cards break
  silently and return 0 results. Use the **accessibility tree** instead:
  `cdp('Accessibility.getFullAXTree')['nodes']`, filter for `role == 'button'`
  or `'link'` whose `name` contains the job title text, then
  `cdp('DOM.getBoxModel', backendNodeId=...)` for click coordinates and
  `click_at_xy(x, y)` to open that job's detail pane. Read `js('location.href')`
  afterwards to capture the numeric id (`currentJobId=NNNNNNN` on LinkedIn) and
  build the canonical `https://www.linkedin.com/jobs/view/<id>` URL.
- **Never trust the on-page relative-time label** ("2h ago", "Reposted X hours
  ago", "Posted today") as proof of freshness — it drifts and is sometimes
  flat wrong; the same listing re-checked a few hours later showed "4 days
  ago". The only trustworthy freshness signal is the **search filter
  parameter at scan time** (`f_TPR=r86400` = within 24h when the search ran).
  Stamp every report with the exact scan timestamp and treat "is this still
  today's list" as a new question requiring a fresh scan, never an assumption.
  Listings also vanish between checks ("This job is no longer available") —
  that's normal churn, not an error.
- If the browser backend itself is down (`BU_CDP_URL unreachable` /
  connection refused), it's usually transient — wait 10–15s and retry once or
  twice before reporting it as a blocker.
- URL patterns to drive directly (swap in `search.titles` / `search.location`):
  - LinkedIn: `https://www.linkedin.com/jobs/search/?keywords=<title>&location=<location>&f_TPR=r86400` (`r86400`=24h, `r604800`=7d, `r2592000`=30d).
  - Indeed (France): `https://fr.indeed.com/jobs?q=<title>&l=<location>&fromage=1` (`fromage` = max age in days: 1/3/7/14).
  - WTTJ / HelloWork / Glassdoor: same idea — use each site's own search UI
    and date-posted filter; apply the same AX-tree technique since markup
    varies and breaks CSS selectors just as often.
- Indeed frequently throws a CAPTCHA or a hard login wall to anonymous/bot
  traffic. If blocked after one retry, say so and continue with whatever
  boards did work — don't fight a CAPTCHA, don't fabricate Indeed results.

### 3. Normalise and merge across boards
Map every raw item to
`{id, title, company, location, salary, contract_type, posted_at, age_days,
url, description, source}` where `source` ∈ {linkedin, indeed, wttj,
hellowork, glassdoor}.

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
sum to a **Fit Score out of 10** — never inflated, a 5 is a real 5.

**Dream-job adjustment (only when `settings.dream_job` from jobhub is
non-empty):** after the base 0-10 score above, judge honestly how well this
specific posting matches that free-text description (role, sector, location,
work mode, anything else the user wrote) and apply a signed adjustment in
`[-scoring.dream_job_max_adjustment, +scoring.dream_job_max_adjustment]`
(default range ±1.5), then clip the result back to `[0, 10]`. A posting that
matches the dream job closely gets close to +1.5; a posting that actively
contradicts it (wrong seniority, wrong sector, wrong location/mode) gets
close to -1.5; anything in between is graded on the same honest-judgment
basis as the five base dimensions — never just +1.5/0/-1.5 as a triple
switch. Name the adjustment explicitly in the rationale, e.g. "+1.2
dream-job: AI Head-of-Product fintech match" or "-1.0 dream-job: on-site
only, dream job wants remote" — so the two scoring layers are never
conflated in the sheet or in jobhub's `match_rationale`. When dream_job is
empty or jobhub was unreachable, skip this paragraph entirely — base score
stands unadjusted and the rationale says nothing about it.

One line naming the biggest strength and the honest biggest gap (base score,
dream-job adjustment if any included). Flag anything below
`scoring.min_priority_score` as low priority (keep it in the list — don't
drop it, just rank it low). Low priority is judged on the FINAL
(post-adjustment) score.

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
  indeed: true
  wttj: true
  hellowork: true
  glassdoor: true
```
Absent section = all five.
