"""cv-job-match control panel — local single-user web app.

    cd webapp && pip install -r requirements.txt && python3 server.py
    open http://localhost:5050

Panels: Filters (edits config/search-profile.yaml) → CV (PDF → Markdown with
diff preview) → This week's jobs (Drive scrape files → filter → score → xlsx)
→ Build packages. See README.md in this folder.
"""

from __future__ import annotations

import json
import subprocess
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "pipeline"))

from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_from_directory

load_dotenv(ROOT / ".env")

import config_io
import cvimport
import gdrive
import packages
import scoring
import xlsx_sync
from filter_jobs import filter_jobs  # pipeline engine, imported not reimplemented
from llm import DEFAULT_MODELS, KEY_ENV, PROVIDERS, LLMError, current_provider, model_for, provider_configured

app = Flask(__name__, static_folder="static")

# Single-user app: the currently loaded job table lives in memory.
_current: dict = {"jobs": [], "stats": None, "source": None}

ENV_PATH = ROOT / ".env"
ENV_KEYS = ("LLM_PROVIDER", "SCORING_MODEL", "PACKAGE_MODEL",
            "MISTRAL_API_KEY", "OPENAI_API_KEY", "GEMINI_API_KEY")


def _err(exc: Exception, code: int = 500):
    traceback.print_exc(file=sys.stderr)
    return jsonify({"error": f"{type(exc).__name__}: {exc}"}), code


@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


# --- Panel 1: Filters --------------------------------------------------------

@app.route("/api/config")
def get_config():
    return jsonify(config_io.plain(config_io.load()))


@app.route("/api/config", methods=["POST"])
def save_config():
    try:
        config_io.apply_form(request.get_json(force=True))
    except Exception as exc:
        return _err(exc, 400)
    # Keep the n8n workflow in sync; surface the CLI output in the UI.
    proc = subprocess.run(
        [sys.executable, str(ROOT / "pipeline" / "config_to_n8n.py"), "--write"],
        capture_output=True, text=True, cwd=ROOT,
    )
    return jsonify({
        "saved": True,
        "n8n_sync": {
            "ok": proc.returncode == 0,
            "output": (proc.stdout + proc.stderr).strip(),
        },
    })


# --- Settings (provider / models / keys in .env) -----------------------------

def _update_env_file(updates: dict) -> None:
    """Update .env in place, preserving unrelated lines and comments."""
    lines = ENV_PATH.read_text(encoding="utf-8").splitlines() if ENV_PATH.exists() else []
    remaining = dict(updates)
    out = []
    for line in lines:
        key = line.split("=", 1)[0].strip()
        if "=" in line and not line.lstrip().startswith("#") and key in remaining:
            out.append(f"{key}={remaining.pop(key)}")
        else:
            out.append(line)
    for key, value in remaining.items():
        out.append(f"{key}={value}")
    ENV_PATH.write_text("\n".join(out) + "\n", encoding="utf-8")


@app.route("/api/settings")
def get_settings():
    import os
    return jsonify({
        "provider": current_provider(),
        "providers": list(PROVIDERS),
        "scoring_model": model_for("scoring"),
        "package_model": model_for("package"),
        "defaults": DEFAULT_MODELS,
        "keys_set": {p: provider_configured(p) for p in PROVIDERS},
        "key_env": {**KEY_ENV, "google": "GEMINI_API_KEY"},
    })


@app.route("/api/settings", methods=["POST"])
def save_settings():
    import os
    data = request.get_json(force=True)
    updates: dict[str, str] = {}
    if data.get("provider") in PROVIDERS:
        updates["LLM_PROVIDER"] = data["provider"]
    for form_key, env_key in (("scoring_model", "SCORING_MODEL"), ("package_model", "PACKAGE_MODEL")):
        if form_key in data:
            updates[env_key] = str(data[form_key]).strip()
    for env_key in ("MISTRAL_API_KEY", "OPENAI_API_KEY", "GEMINI_API_KEY"):
        if data.get(env_key):  # only overwrite a key the user actually typed
            updates[env_key] = str(data[env_key]).strip()
    _update_env_file(updates)
    os.environ.update(updates)  # apply immediately, no restart needed
    return get_settings()


# --- Panel 2: CV -------------------------------------------------------------

@app.route("/api/cv/upload", methods=["POST"])
def cv_upload():
    which = request.form.get("which", "en")
    f = request.files.get("file")
    if not f:
        return jsonify({"error": "no file uploaded"}), 400
    try:
        return jsonify(cvimport.convert(f.read(), which))
    except (LLMError, ValueError) as exc:
        return _err(exc, 422)
    except Exception as exc:
        return _err(exc)


@app.route("/api/cv/commit", methods=["POST"])
def cv_commit():
    try:
        return jsonify({"message": cvimport.commit(request.get_json(force=True)["token"])})
    except KeyError as exc:
        return _err(exc, 410)


@app.route("/api/cv/discard", methods=["POST"])
def cv_discard():
    cvimport.discard(request.get_json(force=True).get("token", ""))
    return jsonify({"discarded": True})


# --- Panel 3: This week's jobs ----------------------------------------------

@app.route("/api/drive/files")
def drive_files():
    cfg = config_io.plain(config_io.load())
    folder_id = cfg["output"]["drive_folder_id"]
    if not folder_id or folder_id == "REPLACE_WITH_DRIVE_FOLDER_ID":
        return jsonify({"error": "output.drive_folder_id is not set in config/search-profile.yaml"}), 400
    try:
        return jsonify({"files": gdrive.list_scrape_files(folder_id)})
    except gdrive.DriveError as exc:
        return _err(exc, 400)
    except Exception as exc:
        return _err(exc)


@app.route("/api/jobs/load", methods=["POST"])
def jobs_load():
    data = request.get_json(force=True)
    cfg = config_io.plain(config_io.load())
    try:
        raw = gdrive.download_json(data["file_id"])
    except gdrive.DriveError as exc:
        return _err(exc, 400)
    except Exception as exc:
        return _err(exc)
    if isinstance(raw, dict):
        raw = raw.get("jobs") or raw.get("items") or []
    # filter_jobs normalises + filters; running it on an already-filtered file
    # is idempotent, so we always run it.
    jobs, stats = filter_jobs(raw, cfg)
    _current.update(jobs=jobs, stats=stats, source=data.get("name"))
    return jsonify({
        "jobs": [{k: v for k, v in j.items() if k != "description"} for j in jobs],
        "stats": stats,
        "scores": scoring.cached_scores(jobs),
    })


@app.route("/api/jobs/score", methods=["POST"])
def jobs_score():
    if not _current["jobs"]:
        return jsonify({"error": "no jobs loaded"}), 400
    ids = set((request.get_json(force=True) or {}).get("ids") or [])
    jobs = [j for j in _current["jobs"] if not ids or j["id"] in ids]
    cfg = config_io.plain(config_io.load())
    cv_text = (ROOT / cfg["cv"]["master_en"]).read_text(encoding="utf-8")
    try:
        return jsonify({"scores": scoring.score_jobs(jobs, cv_text, cfg["scoring"]["weights"])})
    except LLMError as exc:
        return _err(exc, 502)


@app.route("/api/xlsx", methods=["POST"])
def xlsx():
    if not _current["jobs"]:
        return jsonify({"error": "no jobs loaded"}), 400
    cfg = config_io.plain(config_io.load())
    try:
        result = xlsx_sync.build_and_upload(
            _current["jobs"], scoring.cached_scores(_current["jobs"]),
            cfg["output"]["drive_folder_id"], cfg["output"]["spreadsheet_name"],
        )
        return jsonify(result)
    except gdrive.DriveError as exc:
        return _err(exc, 400)
    except Exception as exc:
        return _err(exc)


# --- Panel 4: Build packages -------------------------------------------------

@app.route("/api/packages/start", methods=["POST"])
def packages_start():
    ids = set((request.get_json(force=True) or {}).get("ids") or [])
    jobs = [j for j in _current["jobs"] if j["id"] in ids]
    if not jobs:
        return jsonify({"error": "no matching selected jobs — reload the jobs table"}), 400
    cfg = config_io.plain(config_io.load())
    if not packages.start_build(jobs, cfg, scoring.cached_scores(jobs)):
        return jsonify({"error": "a package build is already running"}), 409
    return jsonify({"started": len(jobs)})


@app.route("/api/packages/status")
def packages_status():
    return jsonify(packages.status())


if __name__ == "__main__":
    configured = [p for p in PROVIDERS if provider_configured(p)]
    print(f"[startup] provider: {current_provider()} | keys set: {', '.join(configured) or 'NONE'}",
          file=sys.stderr)
    if not configured:
        print("[startup] no LLM key configured — scoring/packages/CV-import will error "
              "until one is set in Settings or .env", file=sys.stderr)
    app.run(host="127.0.0.1", port=5050, debug=False, threaded=True)
