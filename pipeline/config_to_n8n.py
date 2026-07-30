#!/usr/bin/env python3
"""
config_to_n8n.py — keep the n8n workflow in sync with search-profile.yaml.

The YAML is the single source of truth. The n8n workflow carries a copy of the
relevant fields in its "Search Config" node so it can run standalone.

Usage:
    # print the JSON blob to paste into the n8n Search Config node
    python3 pipeline/config_to_n8n.py

    # rewrite the workflow file in place (no manual paste needed)
    python3 pipeline/config_to_n8n.py --write
"""

import argparse
import json
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("PyYAML required:  pip3 install pyyaml")

REPO = Path(__file__).resolve().parent.parent
CONFIG = REPO / "config" / "search-profile.yaml"
WORKFLOW = REPO / "n8n" / "weekly-job-scrape.json"


def build_blob(cfg):
    """Flatten the YAML into the shape the n8n Code node expects."""
    s, f = cfg["search"], cfg["filters"]
    return {
        "titles": s["titles"],
        "location": s["location"],
        "work_modes": s["work_modes"],
        "limit_per_title": s["limit_per_title"],
        "date_posted": s["date_posted"],
        "max_age_days": f["max_age_days"],
        "include_freelance": f["include_freelance"],
        "prefer_only": f["prefer_only"],
        "exclude_company_patterns": f["exclude_company_patterns"],
        "exclude_title_patterns": f["exclude_title_patterns"],
        "target_sectors": cfg["target_sectors"],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true",
                    help="update n8n/weekly-job-scrape.json in place")
    args = ap.parse_args()

    cfg = yaml.safe_load(CONFIG.read_text())
    blob = build_blob(cfg)
    pretty = json.dumps(blob, indent=2, ensure_ascii=False)

    if not args.write:
        print(pretty)
        print("\n--- paste the above into the n8n 'Search Config' node "
              "(Mode: JSON) ---", file=sys.stderr)
        return

    wf = json.loads(WORKFLOW.read_text())
    for node in wf["nodes"]:
        if node.get("id") == "config":
            node["parameters"]["jsonOutput"] = "=" + pretty
            break
    else:
        sys.exit("Could not find the 'Search Config' node in the workflow.")

    # Keep the Drive folder in sync too.
    folder_id = cfg.get("output", {}).get("drive_folder_id")
    if folder_id:
        for node in wf["nodes"]:
            if node.get("id") == "drive-upload":
                node["parameters"]["folderId"]["value"] = folder_id

    WORKFLOW.write_text(json.dumps(wf, indent=2, ensure_ascii=False) + "\n")
    print(f"Updated {WORKFLOW.relative_to(REPO)} from "
          f"{CONFIG.relative_to(REPO)}", file=sys.stderr)
    print(f"  {len(blob['titles'])} titles · "
          f"{len(blob['exclude_company_patterns'])} exclusions · "
          f"freelance={'on' if blob['include_freelance'] else 'off'} · "
          f"max age {blob['max_age_days']}d", file=sys.stderr)


if __name__ == "__main__":
    main()
