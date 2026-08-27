# cv-job-match

A reusable job-search pipeline: scrape LinkedIn weekly, filter out the noise,
score what's left against your CV, and generate tailored application packages
on demand.

```
  n8n (weekly, automated)                    Claude (on demand, you ask)
  ─────────────────────────                  ───────────────────────────
  Apify → LinkedIn scrape                    score jobs against CV
      ↓                                          ↓
  filter: consulting, age, freelance         build package for any job
      ↓                                          ↓
  dedupe vs. previous weeks                  tailored CV + cover letter
      ↓                                       + LinkedIn message
  Google Drive / JobApplications  ─────────→ Drive subfolder per job
```

The split is deliberate: n8n does the cheap repetitive work on a schedule,
Claude does the judgment work when you actually want it. You are never paying
an LLM to write 76 cover letters you'll never send.

---

## Quick start

```bash
pip3 install pyyaml
```

Everything is driven by one file: **`config/search-profile.yaml`**.
Edit it directly, or just ask Claude in plain English:

> "add Amundi to my target companies"
> "include freelance roles this week"
> "only jobs from the last 2 weeks"
> "switch my CV to French"

After editing the config, sync it into the n8n workflow:

```bash
python3 pipeline/config_to_n8n.py --write
```

---

## The three things you'll actually do

n8n only does step 0 — everything else is a conversation with Claude, not a
script you run. The three asks below are independent; you can do just #2, or
#2 then #3, whenever you feel like it.

### 0. Let the weekly scrape run (automatic, n8n)
Every Monday 07:00 the n8n workflow scrapes LinkedIn, filters, dedupes against
previous weeks, and drops a file named `jobs-YYYY-MM-DD.json` into your Drive
`JobApplications` folder. Nothing needed from you — this is the only step that
isn't a conversation.

### 1. Refresh the spreadsheet from that JSON
> "Refresh the job spreadsheet from this week's scrape"
> "Turn jobs-2026-08-03.json into a spreadsheet"

What Claude does:
- Finds the newest `jobs-YYYY-MM-DD.json` in the `JobApplications` Drive folder
  (or the specific one you name).
- Reads it, dedupes against anything already in `Job_Matches_Paris_ProductAI.xlsx`
  by job ID (so re-running this doesn't create duplicate rows).
- Rebuilds the xlsx with one row per job: title, company, location, salary,
  contract type, posting age, recruiter (if any), target-sector tag.
- Uploads the updated file back to Drive, replacing the previous version.

This step is mechanical — no CV judgment involved, just structuring what n8n
already filtered. It's fast and doesn't need scoring to have run first.

### 2. Ask Claude to score the week
> "Score this week's jobs"
> "Score the spreadsheet against my CV"

What Claude does:
- Reads `config/search-profile.yaml` for the scoring weights and target sectors.
- Reads the CV per `cv.language` (or per-posting if set to `auto`).
- For every row, adds a **Fit Score (0-10)** and a one-line reason naming the
  biggest strength and the biggest gap — never inflated, a 5 is a real 5.
- Re-sorts the spreadsheet by score, colour-codes it (green ≥8, amber 6-7,
  red <6), and re-uploads it to Drive.

Do #1 first if you haven't refreshed since the last scrape — scoring works off
whatever's currently in the spreadsheet.

### 3. Ask for packages on the ones you like
> "Build a package for Euronext"
> "Packages for ranks 4 through 9"
> "Do the Mistral role, in French"
> "Package the fintech ones scoring above 7"

What Claude does, per job:
- Reads the CV (language per `cv.language`, or matching the posting if `auto`).
- Produces a tailored CV excerpt (retitled, reweighted — never fabricated), a
  cover letter under 250 words, and a LinkedIn outreach message under 90 words.
- Saves it locally to `applications/{date}_{Company}_{Role}/package.md` and
  uploads the same content as a Google Doc into a matching subfolder inside
  `JobApplications` on Drive.

Full mechanics of job selection (by company, rank range, sector, or score
threshold) are in [`prompts/build-package.md`](prompts/build-package.md). If a
selector matches more than 8 jobs, Claude lists them and asks which to build
rather than silently generating a pile of packages.

**You send them yourself.** Nothing here auto-applies or auto-messages.
LinkedIn detects and blocks automated outreach, and a message you didn't read
is a message you can't stand behind.

---

## Refining the search

All of this lives in `config/search-profile.yaml`:

| What you want | Where |
|---|---|
| Drop consulting / ESN / SSII firms | `filters.exclude_company_patterns` — 33 entries by default |
| Nothing older than N days | `filters.max_age_days` (default 60) |
| Allow freelance / contract roles | `filters.include_freelance: true` |
| Only large financial institutions | `filters.prefer_only: true` |
| Add or drop target companies | `target_sectors.large_financial` / `fintech` / `ai_platforms` |
| Different job titles | `search.titles` |
| Switch CV language | `cv.language`: `en`, `fr`, or `auto` |

`cv.language: auto` picks the CV that matches each individual posting's
language — a French posting gets a French package.

### On the consulting exclusion
The default exclusion list removes ESN/SSII/consultancies. Be aware this also
removes roles that may genuinely suit you: **Wivoo (a Wavestone company)**
scored 9/10 in the first run and is now filtered out. If you want consulting-side
AI product roles back, remove `Wivoo`/`Wavestone`/`Hubvisory` from the list, or
ask Claude for a package on a specific one — it will build it and tell you it's
normally filtered.

---

## Testing filters without burning Apify credits

```bash
python3 pipeline/filter_jobs.py \
  --config config/search-profile.yaml \
  --input data/last-raw.json \
  --seen  data/seen-jobs.json
```

Prints a summary to stderr showing exactly what was dropped and why:

```
  input                90
  consulting/ESN      -12
  freelance dropped   -2
  ----------------------------
  KEPT                 76
```

Tune the config, rerun, and only trigger the real scrape once it looks right.

---

## Setup (one time)

### n8n — self-hosted

1. **Import the workflow**: n8n → Workflows → Import from File →
   `n8n/weekly-job-scrape.json`

2. **Add the Apify credential**
   Credentials → New → *Header Auth*
   - Name: `Authorization`
   - Value: `Bearer <your Apify API token>`

   Token from [console.apify.com](https://console.apify.com) → Settings → API &
   Integrations. Free tier gives $5/month; a full run of ~90 jobs costs roughly
   $0.05, so weekly runs stay comfortably free.

3. **Add the Google Drive credential** — see **[docs/n8n-setup.md](docs/n8n-setup.md)**
   for the full walkthrough. Self-hosted n8n can't use n8n's one-click Google
   sign-in, so this means creating your own Google Cloud OAuth app (~10 min,
   one time).

   > **Do not skip the seven-day warning in that doc.** If the OAuth consent
   > screen stays on *External + Testing*, Google expires the token after 7 days
   > and your weekly scrape dies silently after the first run. Publish the app.

4. **Check the Drive folder ID** in the upload node matches
   `output.drive_folder_id` in the config — both should read
   `1kHLEHtByGC33M-75rw-4zV7XwTgJCx-E` (the `JobApplications` folder).
   Easiest: in the upload node set the Folder selector to **From list** and pick
   `JobApplications`. Details in [docs/n8n-setup.md](docs/n8n-setup.md#part-2--check-the-drive-folder-id).

5. **Activate** the workflow — but only after the manual test run below actually
   puts a file in Drive.

### Verify before trusting the schedule
Run the workflow manually once. The **Run Summary** node prints the filter
breakdown — confirm the kept count and the dropped examples look right before
leaving it on a schedule.

---

## CV Coach — the unattended two-agent pair

Two skills run this pipeline autonomously via a Hermes cron job (they live in
the Hermes skill store, `~/.hermes/skills/cv-coach/`, not in `.claude/skills/`
here, because they run outside a Claude Code session):

- **Agent 1 — `scan-jobs`** wraps `find-opportunities` and, on a schedule
  (Hermes cron job `cv-coach-scan`), auto-hands off to Agent 2 for any job
  scoring **Fit Score >= `coach.auto_prep_min_score`** in
  `config/search-profile.yaml` (default **9.3/10 = ">93%"** match) — no
  human checkpoint, by deliberate design at that bar.
- **Agent 2 — `prep-application`** runs `cv-match` → **CV Reviewer**
  sub-agent (independent recruiter persona) → `write-outreach` → **Cover
  Letter Reviewer** sub-agent (hiring-manager persona) → `interview-prep`,
  builds the usual `applications/<date>_<company>_<role>/` package, and
  additionally publishes a **Notion interview cheat-sheet page** per job
  under `coach.notion_parent_page_id` — key stories, metrics, talking
  points, Q&A, and the final cover letter, ready to skim before walking in.

Both never send, apply, or message anyone — same hard rule as everything
else in this repo. Trigger manually with "run the cv coach scan" / "prep
this application for X", or let the cron job run it (`coach.scan_schedule`
in the config, default every 6h).

## Repo layout

```
config/search-profile.yaml     ← the control panel; edit this
pipeline/filter_jobs.py        ← filter/dedupe engine (also used standalone)
pipeline/config_to_n8n.py      ← syncs YAML → n8n workflow
n8n/weekly-job-scrape.json     ← import into n8n
prompts/build-package.md       ← how Claude builds a package for any job
context/cv-master.md           ← English CV
context/cv-master-fr.md        ← French CV (richer fact source)
context/tracker.md             ← Google Sheet tracker reference
applications/                  ← generated packages, one folder per job
data/seen-jobs.json            ← dedupe history across weekly runs
```

## Known limits

- **Filter logic exists twice** — Python (`filter_jobs.py`) and JavaScript
  (the n8n Code node), because the n8n container has no Python. They're kept in
  sync by `config_to_n8n.py` for config, but if you change *logic*, change both.
- **No auto-apply, by design.** See above.
- **Recruiter names are sparse** — LinkedIn exposes one on roughly 5% of
  postings. For the rest the package tells you what kind of person to target.
- **Scoring is a judgment call**, not a measurement. Treat a 6 vs a 7 as noise;
  treat a 9 vs a 4 as signal.
