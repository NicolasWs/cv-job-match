# Local web app — CV & Cover Letter Tool

A small Flask app that runs the four actions **live through Claude**, in your
browser. Unlike the offline `tools/cv-job-composer.html` (which only builds a
prompt to paste), this app calls the Claude API and streams results in-page.

## What it does

| Tab | What happens |
|---|---|
| **Match CV** | Streams the `cv-match` result: score, edits, tailored CV |
| **Draft outreach** | Cover letter + recruiter email + LinkedIn message |
| **Interview prep** | Q&A + STAR storytelling + one-page support sheet |
| **Log job** | Builds a tab-separated row to paste into your Google Sheet |

The first three read your stored CVs (`context/cv-master.md` and
`context/cv-master-fr.md`) automatically and pick the right one by the posting's
language. Paste a CV in "CV override" only to try a different one.

**Model picker:** each of the three LLM-backed tabs has a dropdown listing every
provider you've configured a key for — **Claude Sonnet 5** (default; best
writing quality), **Claude Haiku 4.5** (fastest/cheapest), and, if configured,
**Mistral Medium**, **Gemini 2.0 Flash**, and **GPT-4o mini** as fallbacks. The
list is served from `/api/models` so it stays in sync with `server.py`.

**Automatic fallback:** if the model you picked fails before producing any
output (bad/expired key, rate limit, outage), the app automatically retries
with the next configured provider and drops a short `⚠️ ... falling back to
...` notice into the output, so a broken Anthropic key doesn't leave you stuck.

## Run it

```bash
pip install -r app/requirements.txt   # Flask, Anthropic SDK, requests, python-dotenv
cp .env.example .env                  # then edit .env with your real key(s)
python app/server.py
```

Then open **http://localhost:5001**. (Port 5000 is used by AirPlay Receiver on
recent macOS, so the app defaults to 5001 to avoid that conflict.)

### Setting up `.env`

Only `ANTHROPIC_API_KEY` is required. The others are optional fallbacks:

```
ANTHROPIC_API_KEY=sk-ant-...
MISTRAL_API_KEY=
GOOGLE_API_KEY=
OPENAI_API_KEY=
```

`.env` is git-ignored (see `.gitignore`) — **never commit real API keys**.
`server.py` loads it automatically via `python-dotenv` at startup.

## How it works

- `server.py` — Flask backend. `/api/run` builds a system prompt from the
  matching `.claude/skills/<action>/SKILL.md` plus both CVs, then streams from
  whichever provider the selected model belongs to:
  - **Anthropic** (Sonnet 5 / Haiku 4.5) via the official SDK's streaming client.
  - **Mistral** and **OpenAI** via their (identical) chat-completions SSE format.
  - **Google** (Gemini) via its `streamGenerateContent` SSE endpoint.

  All four are normalized to the same `data: {"text": "..."}` wire format sent
  to the browser, so the frontend doesn't need to know which provider ran.
  `/api/log` builds the tracker row in plain Python (no LLM).
- `index.html` — single-page UI with a tiny built-in Markdown renderer (no CDN).

## Notes & limits

- **Cost:** each run is one Claude API call billed to your key.
- **Editing skills:** the server reads `SKILL.md` and the CV files from disk on
  every request, so tweaks to those files take effect on the next run — no restart.
- **Tracker:** "Log job" produces a paste-ready row rather than writing to Drive
  directly (that would need Google API credentials). The Google Sheet stays the
  canonical tracker; paste the row into it, or update it from Claude Code.
- **Local only:** binds to `127.0.0.1`. Don't expose it publicly — it holds no
  auth and would run API calls on your key.

## Troubleshooting

If clicking **Run** shows nothing:

1. **Check the terminal running `python3 app/server.py`.** Every run prints a
   `[run] action=... system_chars=... user_chars=...` line, and any failure
   prints a full traceback plus a one-line summary. This is the fastest way
   to see what actually happened.
2. **Check the browser console** (Cmd+Option+J in Chrome/Arc, or
   Cmd+Option+I → Console). The app now logs parse issues and shows errors
   directly in the output panel instead of failing silently.
3. **Test the backend directly, bypassing the browser:**
   ```bash
   curl -N -X POST http://127.0.0.1:5001/api/run \
     -H "Content-Type: application/json" \
     -d '{"action":"cv-match","company":"Test","role":"Test","job_description":"Product Manager role focused on data platforms."}'
   ```
   You should see a stream of `data: {"text": "..."}` lines. If instead you
   see a `⚠️ ... failed ... falling back to ...` notice, that's the automatic
   fallback working as designed — check the named provider's key. If you see
   `data: {"error": "..."}` with no fallback, that error text tells you
   exactly what's wrong.
4. **No provider configured:** the server prints a warning at startup listing
   which providers it found keys for (or none) — check that `.env` exists and
   `python-dotenv` picked it up.
