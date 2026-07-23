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

## Run it

```bash
pip install -r app/requirements.txt      # Flask + Anthropic SDK
export ANTHROPIC_API_KEY=sk-ant-...       # your own key
python app/server.py
```

Then open **http://localhost:5000**.

## How it works

- `server.py` — Flask backend. `/api/run` builds a system prompt from the
  matching `.claude/skills/<action>/SKILL.md` plus both CVs, calls
  `claude-opus-4-8` with streaming, and relays tokens to the browser as
  Server-Sent Events. `/api/log` builds the tracker row in plain Python (no LLM).
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
