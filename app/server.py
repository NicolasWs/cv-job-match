"""
Local web app for Nicolas's CV & Cover Letter tool.

Runs the four actions from the user guide by calling Claude:
  - cv-match         -> score + edits + tailored CV
  - write-outreach   -> cover letter, recruiter email, LinkedIn message
  - interview-prep   -> Q&A + STAR storytelling + support sheet
  - log              -> build a paste-ready tracker row (no LLM)

Setup:
    pip install flask anthropic
    export ANTHROPIC_API_KEY=sk-ant-...
    python app/server.py
    open http://localhost:5001
"""

import json
import os
import sys
import traceback
from datetime import date
from pathlib import Path

import anthropic
from flask import Flask, Response, request, send_from_directory, stream_with_context

ROOT = Path(__file__).resolve().parent.parent
CONTEXT = ROOT / "context"
SKILLS = ROOT / ".claude" / "skills"

# Models selectable from the UI dropdown. Sonnet 5 is the default: CV tailoring
# and cover letters are writing-quality-sensitive, and Sonnet is far cheaper
# and faster than Opus while still very capable. Haiku is offered for quick,
# low-stakes drafts.
MODELS = {
    "sonnet": "claude-sonnet-5",
    "haiku": "claude-haiku-4-5",
}
DEFAULT_MODEL_KEY = "sonnet"

app = Flask(__name__)
client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from the environment

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
    return {"models": MODELS, "default": DEFAULT_MODEL_KEY}


@app.route("/api/run", methods=["POST"])
def run():
    data = request.get_json(force=True)
    action = data.get("action")
    if action not in ACTIONS:
        return {"error": f"unknown action: {action}"}, 400
    if action != "interview-prep" and not (data.get("job_description") or "").strip():
        return {"error": "a job description is required for this action"}, 400

    model_key = data.get("model") or DEFAULT_MODEL_KEY
    if model_key not in MODELS:
        return {"error": f"unknown model: {model_key}"}, 400
    model = MODELS[model_key]

    system = build_system(ACTIONS[action])
    user = build_user(ACTIONS[action], data)

    def generate():
        print(f"[run] action={action} model={model} system_chars={len(system)} user_chars={len(user)}", file=sys.stderr)
        try:
            with client.messages.stream(
                model=model,
                max_tokens=20000,
                system=system,
                messages=[{"role": "user", "content": user}],
            ) as stream:
                for text in stream.text_stream:
                    yield f"data: {json.dumps({'text': text})}\n\n"
            yield f"data: {json.dumps({'done': True})}\n\n"
            print("[run] done", file=sys.stderr)
        except Exception as exc:  # noqa: BLE001 - always surface the failure to the UI
            traceback.print_exc(file=sys.stderr)
            yield f"data: {json.dumps({'error': f'{type(exc).__name__}: {exc}'})}\n\n"

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
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print(
            "WARNING: ANTHROPIC_API_KEY is not set in this shell — every /api/run "
            "call will fail. Run: export ANTHROPIC_API_KEY=sk-ant-...",
            file=sys.stderr,
        )
    app.run(host="127.0.0.1", port=5001, debug=False, threaded=True)
