#!/usr/bin/env python3
"""
filter_jobs.py — apply search-profile.yaml filters to raw Apify LinkedIn results.

Used two ways:
  1. From n8n (weekly):  cat raw.json | python3 filter_jobs.py --config config/search-profile.yaml
  2. Ad hoc from Claude: python3 filter_jobs.py --input raw.json --output filtered.json

Reads raw Apify job records on stdin (or --input), writes filtered records to
stdout (or --output), and prints a human-readable summary to stderr.

Exit codes: 0 = success, 1 = config/input error.
"""

import argparse
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("PyYAML required:  pip3 install pyyaml")


# ---------------------------------------------------------------------------
# Age parsing
# ---------------------------------------------------------------------------

_AGE_UNITS = {
    "minute": 1 / 1440, "minutes": 1 / 1440,
    "hour": 1 / 24, "hours": 1 / 24,
    "day": 1, "days": 1,
    "week": 7, "weeks": 7,
    "month": 30, "months": 30,
    "year": 365, "years": 365,
}


def age_in_days(job):
    """
    Best-effort age of a posting in days.

    Prefers the absolute `postedDate` field; falls back to parsing the relative
    `postedTimeAgo` string ("3 weeks ago", "16 hours ago", "2 minutes ago").
    Returns None when neither can be parsed — callers should KEEP such jobs
    rather than silently dropping them.
    """
    posted = job.get("postedDate")
    if posted:
        for fmt in ("%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d"):
            try:
                dt = datetime.strptime(posted, fmt).replace(tzinfo=timezone.utc)
                return (datetime.now(timezone.utc) - dt).days
            except (ValueError, TypeError):
                continue

    ago = (job.get("postedTimeAgo") or "").lower().strip()
    m = re.match(r"(\d+)\s+(\w+)\s+ago", ago)
    if m:
        n, unit = int(m.group(1)), m.group(2)
        if unit in _AGE_UNITS:
            return int(n * _AGE_UNITS[unit])
    return None


# ---------------------------------------------------------------------------
# Filters
# ---------------------------------------------------------------------------

def compile_patterns(patterns):
    """Word-boundary, case-insensitive regexes. Avoids 'ESN' matching 'Dessein'."""
    return [re.compile(r"\b" + re.escape(p) + r"\b", re.IGNORECASE) for p in patterns]


FREELANCE_MARKERS = compile_patterns([
    "freelance", "contract", "contractor", "CDD", "interim", "intérim",
    "mission", "consultant indépendant", "temporary",
])


def looks_freelance(job):
    haystack = " ".join([
        job.get("title", ""),
        job.get("contractType", "") or "",
    ])
    return any(p.search(haystack) for p in FREELANCE_MARKERS)


def sector_of(job, targets):
    """Return which target sector bucket a company falls into, or None."""
    company = (job.get("companyName") or "").lower()
    for bucket, names in targets.items():
        for name in names:
            if name.lower() in company:
                return bucket
    return None


def filter_jobs(jobs, cfg, seen_ids=None):
    f = cfg.get("filters", {})
    targets = cfg.get("target_sectors", {})
    seen_ids = seen_ids or set()

    excl_company = compile_patterns(f.get("exclude_company_patterns", []))
    excl_title = compile_patterns(f.get("exclude_title_patterns", []))
    max_age = f.get("max_age_days", 60)
    include_freelance = f.get("include_freelance", False)
    prefer_only = f.get("prefer_only", False)

    kept, stats = [], {
        "input": len(jobs), "duplicate_in_batch": 0, "already_seen": 0,
        "excluded_company": 0, "excluded_title": 0, "too_old": 0,
        "freelance_dropped": 0, "outside_target": 0, "kept": 0,
    }
    dropped_examples = {}
    batch_ids = set()

    for job in jobs:
        jid = str(job.get("id", ""))

        if jid and jid in batch_ids:
            stats["duplicate_in_batch"] += 1
            continue
        if jid and jid in seen_ids:
            stats["already_seen"] += 1
            continue

        title = job.get("title", "") or ""
        company = job.get("companyName", "") or ""
        haystack = f"{company} {title}"

        hit = next((p for p in excl_company if p.search(haystack)), None)
        if hit:
            stats["excluded_company"] += 1
            dropped_examples.setdefault("company", []).append(f"{company} — {title}")
            continue

        if any(p.search(title) for p in excl_title):
            stats["excluded_title"] += 1
            dropped_examples.setdefault("title", []).append(f"{company} — {title}")
            continue

        age = age_in_days(job)
        if age is not None and age > max_age:
            stats["too_old"] += 1
            continue

        if not include_freelance and looks_freelance(job):
            stats["freelance_dropped"] += 1
            dropped_examples.setdefault("freelance", []).append(f"{company} — {title}")
            continue

        bucket = sector_of(job, targets)
        if prefer_only and bucket is None:
            stats["outside_target"] += 1
            continue

        job["_target_sector"] = bucket or ""
        job["_age_days"] = age if age is not None else ""
        job["_has_recruiter"] = bool(job.get("recruiterName"))
        kept.append(job)
        if jid:
            batch_ids.add(jid)

    stats["kept"] = len(kept)
    # Target-sector hits first, then freshest.
    kept.sort(key=lambda j: (j["_target_sector"] == "", j.get("_age_days") or 999))
    return kept, stats, dropped_examples


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", default="config/search-profile.yaml")
    ap.add_argument("--input", help="raw jobs JSON (default: stdin)")
    ap.add_argument("--output", help="filtered jobs JSON (default: stdout)")
    ap.add_argument("--seen", help="seen-jobs.json for cross-run dedupe")
    ap.add_argument("--update-seen", action="store_true",
                    help="append kept job IDs back into the seen file")
    args = ap.parse_args()

    cfg_path = Path(args.config)
    if not cfg_path.exists():
        sys.exit(f"Config not found: {cfg_path}")
    cfg = yaml.safe_load(cfg_path.read_text())

    raw = json.load(open(args.input)) if args.input else json.load(sys.stdin)
    # Accept either a bare list or Apify's {"items": [...]} envelope.
    jobs = raw.get("items", raw) if isinstance(raw, dict) else raw

    seen_ids, seen_path = set(), None
    if args.seen:
        seen_path = Path(args.seen)
        if seen_path.exists():
            seen_ids = set(json.loads(seen_path.read_text()).get("ids", []))

    kept, stats, examples = filter_jobs(jobs, cfg, seen_ids)

    out = json.dumps(kept, indent=2, ensure_ascii=False)
    if args.output:
        Path(args.output).write_text(out)
    else:
        print(out)

    if args.update_seen and seen_path:
        seen_path.parent.mkdir(parents=True, exist_ok=True)
        all_ids = sorted(seen_ids | {str(j.get("id")) for j in kept if j.get("id")})
        seen_path.write_text(json.dumps(
            {"updated": datetime.now(timezone.utc).isoformat(), "ids": all_ids},
            indent=2))

    print(f"""
Filter summary
--------------
  input                {stats['input']}
  duplicate in batch  -{stats['duplicate_in_batch']}
  already seen        -{stats['already_seen']}
  consulting/ESN      -{stats['excluded_company']}
  excluded title      -{stats['excluded_title']}
  older than {cfg['filters']['max_age_days']}d      -{stats['too_old']}
  freelance dropped   -{stats['freelance_dropped']}
  outside target      -{stats['outside_target']}
  ----------------------------
  KEPT                 {stats['kept']}
""", file=sys.stderr)

    for kind, items in examples.items():
        if items:
            print(f"  dropped ({kind}): {', '.join(items[:5])}"
                  + (f" … +{len(items)-5} more" if len(items) > 5 else ""),
                  file=sys.stderr)


if __name__ == "__main__":
    main()
