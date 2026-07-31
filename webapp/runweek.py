"""One-click "Run my week" orchestrator.

Chains: get jobs (fresh Apify scrape OR newest Drive scrape file) → filter →
score everything → update the Drive spreadsheet (best-effort) → rank.
Stops there by design: package building stays a human decision.

Runs in a background thread; the UI polls status(). Results are pushed into a
callback so server.py can update its in-memory jobs table for panels 3/4.
"""

from __future__ import annotations

import datetime
import json
import threading
from pathlib import Path

import apify
import gdrive
import scoring
import xlsx_sync
from filter_jobs import filter_jobs

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"

STEPS = ("fetch", "filter", "score", "spreadsheet", "rank")

_lock = threading.Lock()
_state: dict = {"running": False, "steps": {}, "result": None, "error": None}


def _step(name: str, status: str, detail: str = "") -> None:
    with _lock:
        _state["steps"][name] = {"status": status, "detail": detail}


def _drive_ok(cfg: dict) -> bool:
    fid = (cfg.get("output") or {}).get("drive_folder_id", "")
    return bool(fid) and fid != "REPLACE_WITH_DRIVE_FOLDER_ID"


def _fetch_jobs(source: str, cfg: dict) -> tuple[list[dict], str]:
    if source == "apify":
        raw = apify.scrape(cfg, on_progress=lambda m: _step("fetch", "running", m))
        # Persist locally in the same shape/naming as the n8n output…
        DATA_DIR.mkdir(exist_ok=True)
        name = f"jobs-{datetime.date.today().isoformat()}.json"
        (DATA_DIR / name).write_text(json.dumps(raw, ensure_ascii=False), encoding="utf-8")
        label = f"fresh scrape → data/{name} ({len(raw)} jobs)"
        # …and mirror to Drive so it sits next to the weekly files (best-effort).
        if _drive_ok(cfg):
            try:
                gdrive.upload_bytes(
                    cfg["output"]["drive_folder_id"], name,
                    json.dumps(raw, ensure_ascii=False).encode("utf-8"), "application/json",
                )
                label += ", mirrored to Drive"
            except Exception as exc:
                label += f" (Drive mirror failed: {exc})"
        return raw, label

    # source == "drive": newest jobs-YYYY-MM-DD.json in the folder
    if not _drive_ok(cfg):
        raise RuntimeError(
            "output.drive_folder_id is not set — either configure Drive or choose "
            "'Fresh Apify scrape' as the source."
        )
    files = gdrive.list_scrape_files(cfg["output"]["drive_folder_id"])
    if not files:
        raise RuntimeError("No jobs-YYYY-MM-DD.json files found in the Drive folder.")
    newest = files[0]
    raw = gdrive.download_json(newest["id"])
    if isinstance(raw, dict):
        raw = raw.get("jobs") or raw.get("items") or []
    return raw, f"{newest['name']} ({len(raw)} jobs)"


def start(source: str, cfg: dict, on_jobs_ready) -> bool:
    """Kick off the flow. on_jobs_ready(jobs, stats, scores) updates the app table."""
    with _lock:
        if _state["running"]:
            return False
        _state.update(running=True, result=None, error=None,
                      steps={s: {"status": "pending", "detail": ""} for s in STEPS})

    def worker() -> None:
        try:
            _step("fetch", "running")
            raw, src_label = _fetch_jobs(source, cfg)
            _step("fetch", "done", src_label)

            _step("filter", "running")
            jobs, stats = filter_jobs(raw, cfg)
            _step("filter", "done",
                  f"kept {stats['kept']} of {stats['input']} "
                  f"(dupes {stats['duplicates']}, excluded co. {stats['excluded_company']}, "
                  f"titles {stats['excluded_title']}, old {stats['too_old']})")

            _step("score", "running", f"0/{len(jobs)}")
            cv_text = (ROOT / cfg["cv"]["master_en"]).read_text(encoding="utf-8")
            scores = scoring.score_jobs(
                jobs, cv_text, cfg["scoring"]["weights"],
                on_progress=lambda done, total, cached:
                    _step("score", "running", f"{done}/{total} ({cached} from cache)"),
            )
            errors = sum(1 for s in scores.values() if "error" in s)
            _step("score", "done" if not errors else "warn",
                  f"{len(scores)} scored" + (f", {errors} errors" if errors else ""))

            on_jobs_ready(jobs, stats, scores)

            _step("spreadsheet", "running")
            if _drive_ok(cfg):
                try:
                    r = xlsx_sync.build_and_upload(
                        jobs, {k: v for k, v in scores.items() if "score" in v},
                        cfg["output"]["drive_folder_id"], cfg["output"]["spreadsheet_name"],
                    )
                    _step("spreadsheet", "done",
                          f"{r['added']} new rows, {r['score_filled']} scores filled")
                except Exception as exc:
                    _step("spreadsheet", "warn", f"skipped — {exc}")
            else:
                _step("spreadsheet", "warn", "skipped — Drive not configured")

            _step("rank", "running")
            ranked = sorted(
                (j for j in jobs if "score" in scores.get(j["id"], {})),
                key=lambda j: scores[j["id"]]["score"], reverse=True,
            )
            top = [
                {"id": j["id"], "title": j["title"], "company": j["company"],
                 "score": scores[j["id"]]["score"], "reason": scores[j["id"]]["reason"]}
                for j in ranked[:8]
            ]
            _step("rank", "done", f"top {len(top)} picks ready")
            with _lock:
                _state["result"] = {"top": top, "total": len(jobs)}
        except Exception as exc:  # noqa: BLE001 — surface everything to the UI
            for name, s in _state["steps"].items():
                if s["status"] == "running":
                    _step(name, "error", str(exc))
                    break
            with _lock:
                _state["error"] = str(exc)
        finally:
            with _lock:
                _state["running"] = False

    threading.Thread(target=worker, daemon=True).start()
    return True


def status() -> dict:
    with _lock:
        return json.loads(json.dumps(_state))  # deep copy
