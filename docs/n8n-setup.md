# n8n weekly scrape — setup notes

The workflow in `n8n/weekly-job-scrape.json` runs every Monday 07:00:
Apify actor `valig/linkedin-jobs-scraper` → light filter/dedupe →
upload `jobs-YYYY-MM-DD.json` to the Google Drive **JobApplications** folder.

## Import & credentials

1. In n8n: *Workflows → Import from file* → pick `n8n/weekly-job-scrape.json`.
2. **Apify token** — create an HTTP Query Auth credential named `Apify token`
   with query param `token` = your Apify API token.
3. **Google Drive account** — create a *Google Drive OAuth2* credential:
   - Google Cloud Console → create OAuth client (type: Web application),
     enable the Drive API, add n8n's redirect URL.
   - Connect it in n8n and name it `Google Drive account`.
4. Set the upload node's folder to your **JobApplications** folder. Its ID is
   the last path segment of the folder URL
   (`https://drive.google.com/drive/folders/<FOLDER_ID>`), and must match
   `output.drive_folder_id` in `config/search-profile.yaml`.

## Keeping it in sync with the config

The workflow embeds a copy of the search titles, filters and folder id.
After changing `config/search-profile.yaml` (directly or via the webapp
Filters panel), run:

    python3 pipeline/config_to_n8n.py --write

then re-import the workflow file into n8n (or paste the updated nodes).
The webapp does this automatically on every config save.

## Reusing the same Google credentials for the webapp

The webapp's Drive access (`webapp/gdrive.py`) can reuse the same Google Cloud
project: create a second OAuth client of type **Desktop app** in that project,
download its JSON to `credentials/oauth-client.json`, and the webapp will run
the browser consent flow on first use (token cached in `credentials/token.json`).
