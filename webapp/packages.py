"""Application-package builder: LLM generation + local save + Drive mirror.

Runs in a background thread; the UI polls /api/packages/status. One build at a
time (single-user tool), progress tracked per job: queued → generating → saved
(or error).
"""

from __future__ import annotations

import datetime
import re
import threading
from pathlib import Path

import gdrive
from llm import LLMError, generate, model_for

ROOT = Path(__file__).resolve().parent.parent
PROMPT_PATH = ROOT / "prompts" / "build-package.md"

_lock = threading.Lock()
_state: dict = {"running": False, "jobs": []}

FR_HINTS = re.compile(
    r"\b(nous|vous|poste|équipe|missions|profil|recherché|entreprise|développer|expérience)\b", re.I
)


def _slug(text: str, max_len: int = 60) -> str:
    s = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE).strip()
    s = re.sub(r"[\s_]+", "-", s)
    return s[:max_len].strip("-") or "untitled"


def detect_language(description: str) -> str:
    """Crude fr/en detection for cv.language == auto."""
    return "fr" if len(FR_HINTS.findall(description or "")) >= 3 else "en"


def _cv_for(language_setting: str, description: str, cfg: dict) -> tuple[str, str]:
    lang = language_setting if language_setting in ("en", "fr") else detect_language(description)
    path = ROOT / cfg["cv"]["master_fr" if lang == "fr" else "master_en"]
    return lang, path.read_text(encoding="utf-8")


def _build_one(job: dict, cfg: dict, score: dict | None) -> dict:
    lang, cv_text = _cv_for(cfg["cv"].get("language", "auto"), job.get("description", ""), cfg)
    prompt_spec = PROMPT_PATH.read_text(encoding="utf-8")

    system = (
        prompt_spec
        + "\n\n=== NICOLAS'S CV (source of truth — never fabricate beyond it) ===\n"
        + cv_text
    )
    score_block = (
        f"\nScoring output (reuse in Fit summary): {score['score']}/10 — {score['reason']}"
        if score and "score" in score else ""
    )
    user = (
        f"Job to build the package for:\n"
        f"Title: {job.get('title')}\nCompany: {job.get('company')}\n"
        f"Location: {job.get('location')}\nContract: {job.get('contract_type')}\n"
        f"Recruiter: {job.get('recruiter') or 'unknown'}\nURL: {job.get('url')}\n"
        f"CV language selected: {lang}{score_block}\n\n"
        f"Full description:\n{job.get('description') or '(none provided)'}"
    )
    package_md = generate(system, user, model=model_for("package")).strip()

    today = datetime.date.today().isoformat()
    folder_name = f"{today}_{_slug(job.get('company', '?'))}_{_slug(job.get('title', '?'))}"
    local_dir = ROOT / cfg.get("output", {}).get("applications_dir", "applications") / folder_name
    local_dir.mkdir(parents=True, exist_ok=True)
    (local_dir / "package.md").write_text(package_md + "\n", encoding="utf-8")

    drive_note = ""
    folder_id = (cfg.get("output") or {}).get("drive_folder_id", "")
    if folder_id and folder_id != "REPLACE_WITH_DRIVE_FOLDER_ID":
        try:
            sub_id = gdrive.ensure_subfolder(folder_id, folder_name)
            gdrive.upload_bytes(
                sub_id, "package.md", (package_md + "\n").encode("utf-8"), "text/markdown"
            )
        except Exception as exc:  # local save succeeded — report Drive issue, don't fail the job
            drive_note = f"saved locally, Drive mirror failed: {exc}"
    else:
        drive_note = "saved locally only (drive_folder_id not configured)"

    return {"path": str(local_dir.relative_to(ROOT) / "package.md"), "note": drive_note}


def start_build(jobs: list[dict], cfg: dict, scores: dict) -> bool:
    """Kick off a background build. Returns False if one is already running."""
    with _lock:
        if _state["running"]:
            return False
        _state.update(
            running=True,
            jobs=[
                {"id": j["id"], "company": j.get("company"), "title": j.get("title"),
                 "status": "queued", "detail": ""}
                for j in jobs
            ],
        )

    def worker() -> None:
        for i, job in enumerate(jobs):
            with _lock:
                _state["jobs"][i]["status"] = "generating"
            try:
                result = _build_one(job, cfg, scores.get(job["id"]))
                with _lock:
                    _state["jobs"][i].update(status="saved", detail=result["note"] or result["path"],
                                             path=result["path"])
            except (LLMError, OSError, Exception) as exc:  # noqa: BLE001 — every failure must reach the UI
                with _lock:
                    _state["jobs"][i].update(status="error", detail=str(exc))
        with _lock:
            _state["running"] = False

    threading.Thread(target=worker, daemon=True).start()
    return True


def status() -> dict:
    with _lock:
        return {"running": _state["running"], "jobs": [dict(j) for j in _state["jobs"]]}
