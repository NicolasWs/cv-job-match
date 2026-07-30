"""Filter + dedupe engine for scraped LinkedIn jobs.

Importable (used by the webapp) and runnable from the CLI:

    python3 pipeline/filter_jobs.py jobs-2026-07-23.json [--config config/search-profile.yaml]

Input: a JSON array of job dicts as produced by the Apify actor
`valig/linkedin-jobs-scraper`. Field names vary slightly between actor
versions, so lookups go through _get() with a list of candidate keys.

Output: (filtered_jobs, stats) where each kept job is normalised to a stable
shape (id, title, company, location, salary, contract_type, posted_at,
age_days, recruiter, url, description, sector) and stats summarises what was
dropped and why.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = ROOT / "config" / "search-profile.yaml"


def load_config(path: str | Path = DEFAULT_CONFIG) -> dict:
    import yaml  # PyYAML is fine for reading; the webapp uses ruamel for writes

    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _get(job: dict, *keys, default=None):
    """Return the first present, non-empty value among candidate keys."""
    for k in keys:
        v = job.get(k)
        if v not in (None, ""):
            return v
    return default


def _job_id(job: dict) -> str:
    jid = _get(job, "id", "jobId", "job_id")
    if jid:
        return str(jid)
    url = _get(job, "url", "link", "jobUrl", default="")
    m = re.search(r"/jobs/view/(\d+)", str(url))
    if m:
        return m.group(1)
    # Last resort: stable hash of company+title
    return f"{_get(job, 'companyName', 'company', default='?')}::{_get(job, 'title', default='?')}".lower()


def _age_days(job: dict) -> int | None:
    raw = _get(job, "postedAt", "posted_at", "postedDate", "listedAt", "publishedAt")
    if raw is None:
        return None
    if isinstance(raw, (int, float)):  # epoch ms
        dt = datetime.fromtimestamp(raw / 1000, tz=timezone.utc)
        return (datetime.now(timezone.utc) - dt).days
    s = str(raw).strip()
    # ISO date(times)
    m = re.match(r"(\d{4}-\d{2}-\d{2})", s)
    if m:
        return (date.today() - date.fromisoformat(m.group(1))).days
    # Relative forms like "3 days ago", "il y a 2 semaines", "5 hours ago"
    m = re.search(r"(\d+)\s*(hour|heure|day|jour|week|semaine|month|mois)", s, re.I)
    if m:
        n, unit = int(m.group(1)), m.group(2).lower()
        if unit.startswith(("hour", "heure")):
            return 0
        if unit.startswith(("day", "jour")):
            return n
        if unit.startswith(("week", "semaine")):
            return n * 7
        return n * 30
    return None


def _sector(company: str, target_sectors: dict) -> str | None:
    c = (company or "").lower()
    for sector, names in (target_sectors or {}).items():
        for name in names or []:
            if name.lower() in c:
                return sector
    return None


def _matches_any(text: str, patterns: list[str]) -> str | None:
    """Return the first pattern matching text (case-insensitive regex), else None."""
    for p in patterns or []:
        try:
            if re.search(p, text, re.I):
                return p
        except re.error:
            if p.lower() in text.lower():
                return p
    return None


FREELANCE_RE = re.compile(r"freelance|free-lance|indépendant|contract(or)?\b|mission", re.I)


def normalise(job: dict, target_sectors: dict) -> dict:
    company = str(_get(job, "companyName", "company", "company_name", default="")).strip()
    return {
        "id": _job_id(job),
        "title": str(_get(job, "title", "jobTitle", default="")).strip(),
        "company": company,
        "location": str(_get(job, "location", "place", default="")).strip(),
        "salary": _get(job, "salary", "salaryInfo", "salary_range", default=""),
        "contract_type": str(_get(job, "contractType", "employmentType", "contract_type", default="")).strip(),
        "work_mode": str(_get(job, "workType", "workplaceType", "work_mode", default="")).strip(),
        "posted_at": _get(job, "postedAt", "posted_at", "postedDate", "listedAt", default=""),
        "age_days": _age_days(job),
        "recruiter": str(_get(job, "recruiterName", "posterFullName", "recruiter", default="")).strip(),
        "url": _get(job, "url", "link", "jobUrl", default=""),
        "description": str(_get(job, "description", "descriptionText", "description_text", default="")),
        "sector": _sector(company, target_sectors),
    }


def filter_jobs(raw_jobs: list[dict], config: dict) -> tuple[list[dict], dict]:
    """Apply the config's filters to raw scraped jobs. Returns (kept, stats)."""
    filters = config.get("filters", {}) or {}
    target_sectors = config.get("target_sectors", {}) or {}
    max_age = filters.get("max_age_days")
    include_freelance = filters.get("include_freelance", True)
    prefer_only = filters.get("prefer_only_target_sectors", False)
    excl_company = filters.get("exclude_company_patterns", [])
    excl_title = filters.get("exclude_title_patterns", [])

    stats = {
        "input": len(raw_jobs),
        "duplicates": 0,
        "excluded_company": 0,
        "excluded_title": 0,
        "too_old": 0,
        "freelance_dropped": 0,
        "non_target_sector": 0,
        "kept": 0,
    }
    seen: set[str] = set()
    kept: list[dict] = []

    for raw in raw_jobs:
        job = normalise(raw, target_sectors)
        if job["id"] in seen:
            stats["duplicates"] += 1
            continue
        seen.add(job["id"])

        if _matches_any(job["company"], excl_company):
            stats["excluded_company"] += 1
            continue
        if _matches_any(job["title"], excl_title):
            stats["excluded_title"] += 1
            continue
        if max_age is not None and job["age_days"] is not None and job["age_days"] > max_age:
            stats["too_old"] += 1
            continue
        if not include_freelance and (
            FREELANCE_RE.search(job["contract_type"]) or FREELANCE_RE.search(job["title"])
        ):
            stats["freelance_dropped"] += 1
            continue
        if prefer_only and job["sector"] is None:
            stats["non_target_sector"] += 1
            continue

        kept.append(job)

    stats["kept"] = len(kept)
    return kept, stats


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("jobs_json", help="path to a jobs-YYYY-MM-DD.json scrape file")
    ap.add_argument("--config", default=str(DEFAULT_CONFIG))
    ap.add_argument("--out", help="write filtered jobs JSON here (default: stdout stats only)")
    args = ap.parse_args()

    with open(args.jobs_json, encoding="utf-8") as f:
        raw = json.load(f)
    if isinstance(raw, dict):  # some dumps wrap the array
        raw = raw.get("jobs") or raw.get("items") or []

    kept, stats = filter_jobs(raw, load_config(args.config))
    print(json.dumps(stats, indent=2), file=sys.stderr)
    if args.out:
        Path(args.out).write_text(json.dumps(kept, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"wrote {len(kept)} jobs -> {args.out}", file=sys.stderr)
    else:
        json.dump(kept, sys.stdout, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
