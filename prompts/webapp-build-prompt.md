# Build prompt — cv-job-match control panel

Copy everything below the line into Claude Opus or Claude Fable as a single
message, in a session that has access to the `cv-job-match` repo (mount it or
paste the specific files it asks for). Fill in the `<TODO>` markers first —
mainly your Google Drive folder ID and Apify actor details, both already in
`config/search-profile.yaml` if you're unsure.

---

## Prompt to paste

You are building a small local web application called **cv-job-match control
panel**. It is the UI for an existing job-search pipeline (repo already
contains config, filtering, and scoring logic) that today is only operable by
asking an AI assistant in chat to run each step. Your job is to give it a
proper UI so it's usable without a chat session.

### What already exists (read these before writing anything)

- `config/search-profile.yaml` — the single source of truth for CV paths,
  search titles, filters (exclude-company patterns, max age, freelance
  toggle, prefer-only-target-sectors), target company lists, and scoring
  weights. **The UI must read and write this exact file** — don't invent a
  new config format.
- `pipeline/filter_jobs.py` — Python filter/dedupe engine. Takes raw job JSON
  + the YAML config, returns filtered jobs + a stats summary. Reuse this
  logic (import it or shell out to it) rather than reimplementing filtering
  in the web app.
- `context/cv-master.md` and `context/cv-master-fr.md` — the two CVs
  (English / French) in Markdown. These are what packages are built from.
- `n8n/weekly-job-scrape.json` — the n8n workflow that runs weekly, scrapes
  LinkedIn via the Apify actor `valig/linkedin-jobs-scraper`, filters, and
  uploads a file named `jobs-YYYY-MM-DD.json` to a Google Drive folder
  (folder ID in `config/search-profile.yaml` under `output.drive_folder_id`).
  This keeps running independently — **the web app does not replace it**, it
  consumes its output and lets the user act on it.
- `prompts/build-package.md` — the spec for what a "package" is: a tailored
  CV excerpt + cover letter + LinkedIn message per job, written by an LLM,
  saved as `applications/{date}_{Company}_{Role}/package.md` locally and
  mirrored to a matching subfolder in the same Google Drive folder.
- `applications/` — existing example packages already in this shape; look at
  2-3 of them to match the Markdown structure exactly.

### What to build

A **single-user, local web app** (one process, no auth, no multi-tenant
concerns) with four screens/panels:

**1. Filters panel**
A form that renders every field in `config/search-profile.yaml` under
`search`, `filters`, and `target_sectors` — titles list (add/remove chips),
location, work modes checkboxes, max age (days, numeric), include-freelance
toggle, prefer-only toggle, exclude-company-patterns (editable tag list, pre
-populated with the ~33 existing entries), exclude-title-patterns, and the
three target-sector lists (large_financial / fintech / ai_platforms) as
editable tag lists. **Save** writes the YAML back to
`config/search-profile.yaml`, preserving comments and structure as much as
practical (use a YAML library that round-trips, e.g. `ruamel.yaml` in
Python, not a naive dump that destroys comments). After saving, call
`python3 pipeline/config_to_n8n.py --write` (shell out to it) so the n8n
workflow file stays in sync — show the CLI output in the UI.

**2. CV panel**
Upload a PDF to replace either the English or French CV. On upload:
extract text from the PDF (use `pdfplumber` or `pypdf` in Python, or an
equivalent in your chosen stack), convert to the same Markdown structure as
the existing `context/cv-master.md` (headings for Experience, Education &
Certifications, Skills, Languages — look at the existing file for the exact
section names and ordering), and write it to `context/cv-master.md` or
`context/cv-master-fr.md` depending on which the user is replacing. Show a
diff-style preview (old vs new) before committing the write, since this file
feeds every downstream package. Also expose the current `cv.language` setting
(`en` / `fr` / `auto`) from the config as a dropdown here, since it's CV-
related.

**3. This week's jobs panel**
- **Refresh from scrape**: list the `jobs-YYYY-MM-DD.json` files present in
  the Google Drive `JobApplications` folder (newest first), let the user pick
  one (default: newest), fetch it, run it through `pipeline/filter_jobs.py`
  logic if not already filtered, and display it as a sortable/filterable
  table (columns: title, company, location, salary, contract type, posting
  age, recruiter name if present, target-sector tag).
- **Score** button: for each visible row, compute a 0-10 fit score plus a
  one-line strength/gap reason. This step needs an LLM call per job (or
  batched) — use the Claude API (`anthropic` Python/JS SDK) with the CV
  content and `scoring.weights` from the config as the prompt context. Cache
  scores by job ID so re-scoring doesn't re-charge for unchanged jobs.
  Display scores as a column, colour-coded (green ≥8, amber 6-7, red <6),
  sortable.
- **Update Google Drive spreadsheet**: writes the current table (with scores)
  to an `.xlsx` (e.g. via `openpyxl`) named `Job_Matches_Paris_ProductAI.xlsx`
  and uploads/overwrites it in the same Drive folder via the Google Drive
  API. Dedupe by job ID against whatever's already in that spreadsheet if it
  exists, rather than blindly overwriting rows for jobs the user has already
  annotated.

**4. Build packages panel**
Checkboxes on the jobs table (panel 3) feed this. For each selected job:
- Call the Claude API with `prompts/build-package.md` as the system/task
  prompt, the job's full description, the appropriate CV (by `cv.language`,
  or auto-detected from the posting's language), and the scoring output if
  available.
- Write the result to `applications/{date}_{Company}_{Role-slug}/package.md`
  locally.
- Create a matching subfolder in the Drive `JobApplications` folder (name
  format `{date}_{Company}_{Role}`, matching the local folder) and upload the
  package content as a Google Doc (or plain text — match what the existing
  example folders in `applications/` contain).
- Show progress per job (queued → generating → saved) since this is the
  slowest step and may process several jobs in sequence.
- If more than 8 jobs are selected at once, show a confirmation dialog before
  starting (cost/time warning) rather than silently running all of them.

### Non-negotiable constraints

- **No auto-apply, no auto-send.** This tool builds packages; it must never
  submit a job application or send a LinkedIn/email message on the user's
  behalf. Don't build that feature even if it seems like a natural next step.
- **Never fabricate CV content.** Every claim in a generated package must
  trace to the actual CV text. If you're generating the package-writing
  prompt yourself, include this constraint explicitly in it.
- **`config/search-profile.yaml` stays the source of truth.** Don't introduce
  a second config file or a database that duplicates its content — read and
  write that file directly.
- **Respect the existing file/folder naming conventions** in `applications/`
  and the Drive folder — don't invent new ones.

### Suggested stack (adjust if you have a strong reason not to)

- Backend: Python (FastAPI or Flask) — lets you reuse `pipeline/filter_jobs.py`
  directly as an import rather than reimplementing or shelling out.
- Frontend: a single-page app (React, or plain HTML+HTMX if you want to
  minimize build tooling) — this is a personal tool for one user, favor
  simplicity over architecture.
- Google Drive access: `google-api-python-client` with OAuth2 — reuse
  whatever credential setup the user already has for their n8n Drive
  connection if you can (see `docs/n8n-setup.md` for how that was configured);
  otherwise guide them through creating credentials for this app specifically.

### LLM provider — no Anthropic key available, support these three instead

The user does not have an Anthropic API key. Build the LLM-calling code
behind a **single provider-agnostic interface** (one function,
`generate(system_prompt, user_prompt, model) -> str`, or a small class if
your stack prefers) with **pluggable backends for Mistral, OpenAI, and
Google (Gemini)**. Nothing in panels 3 or 4 should hardcode a specific
vendor's SDK outside that one interface.

> Model names below were checked against each provider's own docs at build
> time (`platform.openai.com/docs/models`, `docs.mistral.ai/models`,
> `ai.google.dev/gemini-api/docs/models`). Models move fast — if any of these
> come back "not found" when the app first calls them, check that page for
> the current name rather than guessing a variant; don't fall back to an
> older model silently.

- **OpenAI** — `openai` SDK, Responses API. Env var `OPENAI_API_KEY`.
  Current flagship tier is **GPT-5.6**, offered at three cost points:
  `gpt-5.6-sol` (frontier, best for package writing), `gpt-5.6-terra`
  (balanced), `gpt-5.6-luna` (cheapest, good fit for the bulk weekly scoring
  pass). The alias `gpt-5.6` currently points to `gpt-5.6-sol`.
- **Mistral** — `mistralai` SDK. Env var `MISTRAL_API_KEY`.
  Current flagship is **Mistral Medium 3.5** (frontier-class, agentic/coding
  optimized) for package writing. For cheap bulk scoring, use **Mistral
  Small 4** (their current efficient hybrid model) or the smaller
  **Ministral 3 8B** / **Ministral 3 3B** if Small 4 is overkill. Confirm the
  exact API model string on `docs.mistral.ai/models/overview` — Mistral
  versions its API IDs by release date (e.g. `mistral-medium-2508` was the
  prior release), so the live ID for the current release may differ slightly
  from the doc page's display name.
- **Google** — `google-genai` SDK. Env var `GEMINI_API_KEY` (confirm current
  convention in the SDK docs; some versions also accept `GOOGLE_API_KEY`).
  For package writing use **`gemini-3.5-flash`** (stable; Google's current
  "most intelligent" model for sustained agentic tasks). For the cheap
  scoring pass use **`gemini-3.1-flash-lite`** (stable, frontier-class
  performance at low cost) or **`gemini-3.5-flash-lite`** if available on
  your account. Avoid defaulting to anything marked **Preview** in the docs
  (e.g. `gemini-3.1-pro-preview`) for a scheduled/repeated workflow — preview
  models can be deprecated on short notice.

**Settings panel additions:**
- A provider dropdown (Mistral / OpenAI / Google) plus separate model fields
  for "scoring model" and "package-writing model" — let the user pick a
  cheaper model for the bulk scoring pass and a stronger one for the handful
  of packages they actually generate, same reasoning as before, just not
  tied to one vendor.
- Store whichever key(s) the user provides in a local `.env` file (never
  committed — add it to `.gitignore` if not already there) and read it at
  startup. Only require the key for the provider currently selected; don't
  block the app from starting if the other two are empty.
- If a call fails (bad key, rate limit, model not found), surface the actual
  provider error in the UI — don't swallow it into a generic "something went
  wrong."

**Prompt portability:** since `prompts/build-package.md` and the scoring
instructions were originally written for Claude, adapt the wording only if a
given provider's API has structural requirements (e.g., a hard split between
system and user turns) — don't rewrite the substance of what the prompt asks
for. The constraints (never fabricate CV content, name the biggest gap
honestly, match the posting's language) apply identically regardless of
which model executes them.

### Deliverable

A working local app (`cd webapp && <run command>` should be enough to start
it) with a README section explaining: how to set the Mistral / OpenAI /
Google API key (whichever the user has), how to switch provider and models
for scoring vs. package-writing, how to point it at the Google Drive
credentials, and how to run it day to day.
Wire panels 1-4 together in the order above; a user's typical session is
"tweak filters if needed → refresh this week's jobs → score → select a few →
build packages," so the UI should read top-to-bottom in that order.

---

Drop this into a fresh Opus or Fable session with the `cv-job-match` repo
mounted (or the key files pasted in if it can't access the filesystem
directly). Expect to iterate — a one-shot build will get you a working v1,
not a finished product; review what it writes to `search-profile.yaml` and
the Drive folder before trusting it unattended.
