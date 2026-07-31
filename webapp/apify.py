"""On-demand LinkedIn scrape via the Apify actor `valig/linkedin-jobs-scraper`.

Same actor and input shape as the weekly n8n workflow, triggered from the app
instead. Needs APIFY_TOKEN in .env. Runs are started async and polled, since
scrapes routinely exceed Apify's 300s sync limit.
"""

from __future__ import annotations

import os
import time

import requests

ACTOR = "valig~linkedin-jobs-scraper"
BASE = "https://api.apify.com/v2"


class ApifyError(Exception):
    pass


def _token() -> str:
    token = os.environ.get("APIFY_TOKEN", "").strip()
    if not token:
        raise ApifyError("APIFY_TOKEN is not set — add it in Settings (stored in .env).")
    return token


def build_input(cfg: dict) -> dict:
    search = cfg.get("search", {})
    return {
        "titles": search.get("titles", []),
        "location": search.get("location", ""),
        "workModes": search.get("work_modes", []),
        "maxAgeDays": (cfg.get("filters") or {}).get("max_age_days", 14),
    }


def scrape(cfg: dict, on_progress=None, timeout_s: int = 900) -> list[dict]:
    """Start an actor run, poll until it finishes, return the dataset items."""
    token = _token()
    say = on_progress or (lambda _msg: None)

    say("starting Apify run…")
    resp = requests.post(
        f"{BASE}/acts/{ACTOR}/runs", params={"token": token},
        json=build_input(cfg), timeout=60,
    )
    if resp.status_code >= 400:
        raise ApifyError(f"Apify run start failed ({resp.status_code}): {resp.text[:300]}")
    run = resp.json()["data"]
    run_id, dataset_id = run["id"], run["defaultDatasetId"]

    started = time.time()
    status = run["status"]
    while status in ("READY", "RUNNING"):
        if time.time() - started > timeout_s:
            raise ApifyError(f"Apify run {run_id} still {status} after {timeout_s}s — "
                             f"check it in the Apify console.")
        time.sleep(5)
        r = requests.get(f"{BASE}/actor-runs/{run_id}", params={"token": token}, timeout=30)
        r.raise_for_status()
        data = r.json()["data"]
        status = data["status"]
        stats = data.get("stats") or {}
        say(f"Apify run {status.lower()} — {int(time.time() - started)}s elapsed, "
            f"{stats.get('itemCount', '?')} items so far")

    if status != "SUCCEEDED":
        raise ApifyError(f"Apify run finished with status {status} — see the Apify console for logs.")

    say("run finished — downloading dataset…")
    items: list[dict] = []
    offset = 0
    while True:
        r = requests.get(
            f"{BASE}/datasets/{dataset_id}/items",
            params={"token": token, "format": "json", "offset": offset, "limit": 1000},
            timeout=120,
        )
        r.raise_for_status()
        page = r.json()
        items.extend(page)
        if len(page) < 1000:
            break
        offset += 1000
    say(f"downloaded {len(items)} scraped jobs")
    return items
