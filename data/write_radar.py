import json
from pathlib import Path
from datetime import datetime, timezone

kept = json.load(open("data/filtered-2026-10-05.json"))
seen_path = Path("data/seen-jobs.json")
seen_ids = set()
if seen_path.exists():
    seen_ids = set(json.loads(seen_path.read_text()).get("ids", []))

new_ids = {j["id"] for j in kept if j.get("id")}
all_ids = sorted(seen_ids | new_ids)
seen_path.write_text(json.dumps({"updated": datetime.now(timezone.utc).isoformat(), "ids": all_ids}, indent=2))
print("seen-jobs.json updated:", len(seen_ids), "->", len(all_ids))

# Company Radar
scored = json.load(open("data/scored-2026-10-05.json"))
from collections import defaultdict
companies = defaultdict(lambda: {"openings": 0, "best": 0, "sector": False, "roles": []})
for j in scored:
    c = j.get("companyName") or "(unknown)"
    if c == "(unknown)":
        continue
    d = companies[c]
    d["openings"] += 1
    d["best"] = max(d["best"], j["_fit_score"])
    if j.get("_target_sector"):
        d["sector"] = True
    d["roles"].append(j["title"])

ranked = sorted(companies.items(), key=lambda kv: (-kv[1]["best"], -kv[1]["openings"], not kv[1]["sector"]))[:15]

lines = ["# Target Companies — 2026-10-05\n",
         "Scan: 376 raw postings (LinkedIn 40, WTTJ 250, HelloWork 86, Glassdoor 0 — monthly Apify usage cap hit) -> 338 unique -> 170 kept after filters -> 8 target-sector hits.\n",
         "Best Fit Score this run: 6/10 (Mistral AI — Product Director, Studio; Swan — Payment Product Manager). No job cleared the 9.3/10 auto-prep bar.\n",
         "| Company | Best Fit | Openings | Sector hit | Sample role |",
         "|---|---|---|---|---|"]
for c, d in ranked:
    lines.append(f"| {c} | {d['best']}/10 | {d['openings']} | {'yes' if d['sector'] else 'no'} | {d['roles'][0][:50]} |")

Path("applications/target-companies-2026-10-05.md").write_text("\n".join(lines))
print("radar written")
