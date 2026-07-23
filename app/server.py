"""
Local web app for Nicolas's CV & Cover Letter tool.

Runs the four actions from the user guide by calling Claude (or a fallback
provider if Anthropic isn't available):
  - cv-match         -> score + edits + tailored CV
  - write-outreach   -> cover letter, recruiter email, LinkedIn message
  - interview-prep   -> Q&A + STAR storytelling + support sheet
  - log              -> build a paste-ready tracker row (no LLM)

Setup:
    pip install -r app/requirements.txt
    cp .env.example .env      # then fill in your real keys — .env is git-ignored
    python app/server.py
    open http://localhost:5001

Only ANTHROPIC_API_KEY is required. MISTRAL_API_KEY / GOOGLE_API_KEY /
OPENAI_API_KEY are optional fallbacks: if the selected model's provider fails
before producing any output, the app automatically retries the next
configured provider and drops a short notice into the output.
"""

import json
import os
import sys
import traceback
from datetime import date
from pathlib import Path

import anthropic
import requests
from dotenv import load_dotenv
from flask import Flask, Response, request, send_from_directory, stream_with_context

ROOT = Path(__file__).resolve().parent.parent
CONTEXT = ROOT / "context"
SKILLS = ROOT / ".claude" / "skills"

load_dotenv(ROOT / ".env")  # loads real keys from a git-ignored .env, if present

# --- Providers -------------------------------------------------------------
# Each provider is keyed by the env var holding its API key. A provider is
# only usable (selectable, and eligible as a fallback) when that env var is
# set. Never hardcode real key values here — they belong in .env.
PROVIDER_KEY_ENV = {
    "anthropic": "ANTHROPIC_API_KEY",
    "mistral": "MISTRAL_API_KEY",
    "google": "GOOGLE_API_KEY",
    "openai": "OPENAI_API_KEY",
}


def provider_configured(provider: str) -> bool:
    return bool(os.environ.get(PROVIDER_KEY_ENV[provider]))


# Models selectable from the UI dropdown, in fallback priority order. Sonnet 5
# is the default: CV tailoring and cover letters are writing-quality-sensitive,
# and Sonnet is far cheaper and faster than Opus while still very capable.
# The Mistral/Google/OpenAI entries are fallbacks for when the Anthropic key
# doesn't work — "medium"-tier models, not the flagship tier of each provider.
MODEL_OPTIONS = {
    "sonnet": {
        "provider": "anthropic", "id": "claude-sonnet-5",
        "label": "Claude Sonnet 5 — best writing quality",
    },
    "haiku": {
        "provider": "anthropic", "id": "claude-haiku-4-5",
        "label": "Claude Haiku 4.5 — fastest, cheapest",
    },
    "mistral-medium": {
        "provider": "mistral", "id": "mistral-medium-latest",
        "label": "Mistral Medium — fallback",
    },
    "gemini": {
        "provider": "google", "id": "gemini-2.0-flash",
        "label": "Gemini 2.0 Flash — fallback",
    },
    "gpt": {
        "provider": "openai", "id": "gpt-4o-mini",
        "label": "GPT-4o mini — fallback",
    },
}
DEFAULT_MODEL_KEY = "sonnet"
FALLBACK_ORDER = ["sonnet", "haiku", "mistral-medium", "gemini", "gpt"]

app = Flask(__name__)
client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from the environment


def stream_openai_compatible(base_url: str, api_key: str, model: str, system: str, user: str):
    """Streams text deltas from an OpenAI-style chat-completions endpoint.

    OpenAI and Mistral both implement this same wire format, so one function
    covers both providers.
    """
    resp = requests.post(
        base_url,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={
            "model": model,
            "stream": True,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        },
        stream=True,
        timeout=120,
    )
    resp.raise_for_status()
    for raw_line in resp.iter_lines(decode_unicode=True):
        if not raw_line or not raw_line.startswith("data: "):
            continue
        payload = raw_line[len("data: "):]
        if payload.strip() == "[DONE]":
            break
        chunk = json.loads(payload)
        delta = (chunk.get("choices") or [{}])[0].get("delta", {})
        text = delta.get("content")
        if text:
            yield text


def stream_google(api_key: str, model: str, system: str, user: str):
    """Streams text deltas from the Gemini streamGenerateContent SSE endpoint."""
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:"
        f"streamGenerateContent?alt=sse&key={api_key}"
    )
    resp = requests.post(
        url,
        json={
            "systemInstruction": {"parts": [{"text": system}]},
            "contents": [{"role": "user", "parts": [{"text": user}]}],
        },
        stream=True,
        timeout=120,
    )
    resp.raise_for_status()
    for raw_line in resp.iter_lines(decode_unicode=True):
        if not raw_line or not raw_line.startswith("data: "):
            continue
        chunk = json.loads(raw_line[len("data: "):])
        for candidate in chunk.get("candidates", []):
            for part in candidate.get("content", {}).get("parts", []):
                text = part.get("text")
                if text:
                    yield text


def stream_model(model_key: str, system: str, user: str):
    """Dispatches to the right provider for this model key; yields text chunks."""
    opt = MODEL_OPTIONS[model_key]
    provider, model_id = opt["provider"], opt["id"]

    if provider == "anthropic":
        with client.messages.stream(
            model=model_id, max_tokens=20000, system=system,
            messages=[{"role": "user", "content": user}],
        ) as stream:
            yield from stream.text_stream
    elif provider == "mistral":
        yield from stream_openai_compatible(
            "https://api.mistral.ai/v1/chat/completions",
            os.environ["MISTRAL_API_KEY"], model_id, system, user,
        )
    elif provider == "openai":
        yield from stream_openai_compatible(
            "https://api.openai.com/v1/chat/completions",
            os.environ["OPENAI_API_KEY"], model_id, system, user,
        )
    elif provider == "google":
        yield from stream_google(os.environ["GOOGLE_API_KEY"], model_id, system, user)
    else:
        raise ValueError(f"unknown provider: {provider}")

# Map each streaming action to its skill folder.
ACTIONS = {
    "cv-match": "cv-match",
    "write-outreach": "write-outreach",
    "interview-prep": "interview-prep",
}


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def skill_body(name: str) -> str:
    """Return a skill's SKILL.md with the YAML frontmatter stripped."""
    raw = read_text(SKILLS / name / "SKILL.md")
    if raw.startswith("---"):
        parts = raw.split("---", 2)
        if len(parts) == 3:
            return parts[2].strip()
    return raw.strip()


def build_system(action: str) -> str:
    cv_en = read_text(CONTEXT / "cv-master.md")
    cv_fr = read_text(CONTEXT / "cv-master-fr.md")
    instructions = skill_body(action)
    return (
        f"You are running the '{action}' skill for Nicolas Wajs's job-search "
        "assistant. Follow the skill instructions exactly and return only the "
        "deliverable as clean Markdown. Do not ask clarifying questions — if a "
        "detail is missing, make a sensible assumption and note it briefly.\n\n"
        "=== SKILL INSTRUCTIONS ===\n"
        f"{instructions}\n\n"
        "=== NICOLAS'S CV (English) ===\n"
        f"{cv_en or '(not provided)'}\n\n"
        "=== NICOLAS'S CV (French — richer technical detail, better fact source) ===\n"
        f"{cv_fr or '(not provided)'}\n\n"
        "Use the CV whose language matches the job posting; the French file is the "
        "better source of facts and metrics even when the output is in English. "
        "Never invent experience, metrics, or outcomes not present in the CVs."
    )


def build_user(action: str, data: dict) -> str:
    company = (data.get("company") or "").strip()
    role = (data.get("role") or "").strip()
    jd = (data.get("job_description") or "").strip()
    cv_override = (data.get("cv_override") or "").strip()

    parts = []
    if company:
        parts.append(f"Target company: {company}")
    if role:
        parts.append(f"Target role: {role}")
    if cv_override:
        parts.append(
            "The user pasted this CV — prefer it over the stored CV:\n"
            f"<<<CV\n{cv_override}\nCV>>>"
        )
    if jd:
        parts.append(f"Job description:\n<<<JOB\n{jd}\nJOB>>>")

    if action == "interview-prep":
        parts.append(
            "Produce the interview prep now for this company/role. If no job "
            "description was given, base it on Nicolas's profile and the role title."
        )
    return "\n\n".join(parts) if parts else "Proceed using the stored CV."


@app.route("/")
def index():
    return send_from_directory(Path(__file__).resolve().parent, "index.html")


@app.route("/api/models")
def models():
    available = {
        key: opt["label"]
        for key, opt in MODEL_OPTIONS.items()
        if provider_configured(opt["provider"])
    }
    default = DEFAULT_MODEL_KEY if DEFAULT_MODEL_KEY in available else next(iter(available), None)
    return {"models": available, "default": default}


@app.route("/api/run", methods=["POST"])
def run():
    data = request.get_json(force=True)
    action = data.get("action")
    if action not in ACTIONS:
        return {"error": f"unknown action: {action}"}, 400
    if action != "interview-prep" and not (data.get("job_description") or "").strip():
        return {"error": "a job description is required for this action"}, 400

    requested_key = data.get("model") or DEFAULT_MODEL_KEY
    if requested_key not in MODEL_OPTIONS:
        return {"error": f"unknown model: {requested_key}"}, 400

    # Try the requested model first, then any other configured provider in
    # FALLBACK_ORDER, in case the requested one's API key is missing/invalid.
    attempts = [requested_key] + [
        k for k in FALLBACK_ORDER
        if k != requested_key and provider_configured(MODEL_OPTIONS[k]["provider"])
    ]
    if not provider_configured(MODEL_OPTIONS[requested_key]["provider"]) and not attempts[1:]:
        return {"error": "no provider is configured — set at least one API key in .env"}, 400

    system = build_system(ACTIONS[action])
    user = build_user(ACTIONS[action], data)

    def generate():
        for i, model_key in enumerate(attempts):
            opt = MODEL_OPTIONS[model_key]
            got_any_text = False
            print(f"[run] attempt {i + 1}/{len(attempts)}: {model_key} ({opt['id']})", file=sys.stderr)
            try:
                for text in stream_model(model_key, system, user):
                    got_any_text = True
                    yield f"data: {json.dumps({'text': text})}\n\n"
                yield f"data: {json.dumps({'done': True})}\n\n"
                print("[run] done", file=sys.stderr)
                return
            except Exception as exc:  # noqa: BLE001 - always surface the failure to the UI
                traceback.print_exc(file=sys.stderr)
                if got_any_text:
                    # Partial output already streamed to the user — report the
                    # error rather than silently splicing in another model.
                    yield f"data: {json.dumps({'error': f'{type(exc).__name__}: {exc} (after partial output)'})}\n\n"
                    return
                if i + 1 < len(attempts):
                    nxt = MODEL_OPTIONS[attempts[i + 1]]
                    notice = (
                        f"\n\n> ⚠️ **{opt['label']} failed** "
                        f"({type(exc).__name__}: {exc}) — falling back to **{nxt['label']}**...\n\n"
                    )
                    yield f"data: {json.dumps({'text': notice})}\n\n"
                    continue
                yield f"data: {json.dumps({'error': f'All models failed. Last error: {type(exc).__name__}: {exc}'})}\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.route("/api/log", methods=["POST"])
def log():
    """Build a tab-separated tracker row ready to paste into the Google Sheet."""
    d = request.get_json(force=True)
    row = [
        d.get("company", ""),
        d.get("role", ""),
        d.get("priority", "Med"),
        d.get("match", ""),
        d.get("status", "Applied"),
        d.get("link", ""),
        str(date.today()),          # Date Found
        d.get("date_applied", ""),
        d.get("contact_name", ""),
        d.get("contact", ""),
        d.get("last_action", ""),
        d.get("last_action_date", ""),
        d.get("next_follow_up", ""),
        d.get("assets", ""),
        d.get("notes", ""),
    ]
    return {"tsv": "\t".join(row)}


if __name__ == "__main__":
    configured = [p for p in PROVIDER_KEY_ENV if provider_configured(p)]
    if not configured:
        print(
            "WARNING: no provider API key is configured — every /api/run call "
            "will fail. Copy .env.example to .env and fill in at least "
            "ANTHROPIC_API_KEY.",
            file=sys.stderr,
        )
    else:
        print(f"[startup] configured providers: {', '.join(configured)}", file=sys.stderr)
    app.run(host="127.0.0.1", port=5001, debug=False, threaded=True)
