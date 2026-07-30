# cv-job-match control panel

Local single-user web UI for the job-search pipeline. It reads/writes
`config/search-profile.yaml` (the single source of truth), reuses
`pipeline/filter_jobs.py` for filtering, consumes the weekly n8n scrape output
from Google Drive, scores jobs with an LLM, and builds application packages
into `applications/` (mirrored to Drive).

It **never applies to jobs or sends messages** — it only builds packages.

## Run it

```bash
cd webapp
pip install -r requirements.txt
python3 server.py
# open http://localhost:5050
```

## LLM API key (Mistral / OpenAI / Google — pick one)

Set whichever key you have, either in the **Settings** panel of the UI
(written to the git-ignored `.env` at the repo root) or by hand:

```bash
# repo root .env — one of:
MISTRAL_API_KEY=...
OPENAI_API_KEY=...
GEMINI_API_KEY=...      # GOOGLE_API_KEY also works

LLM_PROVIDER=mistral    # or: openai | google
```

Only the selected provider's key is required; the app starts fine with the
others empty.

### Switching provider & models

In **Settings**: pick the provider, then set two models —

| | scoring (cheap, bulk weekly pass) | package writing (strong) |
|---|---|---|
| Mistral | `mistral-small-latest` | `mistral-medium-latest` |
| OpenAI | `gpt-5.6-luna` | `gpt-5.6-sol` |
| Google | `gemini-3.1-flash-lite` | `gemini-3.5-flash` |

Defaults fill in automatically when you change provider. If a model comes back
"not found", check the provider's models page for the current name (they move
fast); the app surfaces the provider's raw error rather than silently falling
back. Overrides are stored as `SCORING_MODEL` / `PACKAGE_MODEL` in `.env`.

## Google Drive credentials

The app needs Drive access to list/download the weekly `jobs-YYYY-MM-DD.json`
scrapes, upload the spreadsheet, and mirror packages. Two options (both files
live in the git-ignored `credentials/` folder at the repo root):

1. **OAuth (recommended — reuses your n8n Google Cloud project, see
   `docs/n8n-setup.md`)**: in that project create an OAuth client of type
   *Desktop app*, download its JSON to `credentials/oauth-client.json`.
   First Drive action opens a browser consent screen; the token is cached in
   `credentials/token.json`.
2. **Service account**: put its key at `credentials/service-account.json` and
   share the *JobApplications* Drive folder with the service-account email.

Also set `output.drive_folder_id` in `config/search-profile.yaml` to the
JobApplications folder ID (last segment of its Drive URL) — the same one the
n8n workflow uploads to.

## Day-to-day use (top to bottom)

1. **Filters** — tweak titles, exclusions, sectors; *Save* writes the YAML
   (comments preserved) and runs `pipeline/config_to_n8n.py --write` so the
   weekly scrape stays in sync (CLI output shown in the panel).
2. **CV** — optionally replace either CV from a PDF. Review the diff before
   writing; the previous version is kept as `context/cv-master*.md.bak`.
3. **This week's jobs** — *Refresh list* → pick the newest scrape → *Load*
   (runs the pipeline filter, shows drop stats) → *Score visible jobs*
   (0-10, colour-coded, cached by job ID so re-scoring is free) →
   *Update Drive spreadsheet* (`Job_Matches_Paris_ProductAI.xlsx`, merged by
   job ID so your hand-edits survive).
4. **Build packages** — tick jobs in the table, hit build. Progress shows
   queued → generating → saved per job. More than 8 selected asks for
   confirmation first. Output: `applications/{date}_{Company}_{Role}/package.md`
   + the same folder/file mirrored in Drive.
