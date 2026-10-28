import json, sys
sys.path.insert(0, "pipeline")
from filter_jobs import filter_jobs
import yaml
from pathlib import Path

raw = json.load(open("data/raw_items_2026-10-05.json"))

normalized = []

def norm_linkedin(j):
    return {
        "id": "li_" + str(j.get("id", "")),
        "title": j.get("title", ""),
        "companyName": j.get("companyName", ""),
        "location": j.get("location", ""),
        "postedDate": j.get("postedDate"),
        "postedTimeAgo": j.get("postedTimeAgo"),
        "contractType": j.get("contractType", ""),
        "recruiterName": j.get("recruiterName", ""),
        "description": j.get("description", ""),
        "url": j.get("url", ""),
        "source": "linkedin",
        "salary": j.get("salary", ""),
    }

def norm_wttj(j):
    offices = j.get("offices") or []
    loc = offices[0]["address"] if offices else ""
    return {
        "id": "wttj_" + str(j.get("id", "")),
        "title": j.get("name", ""),
        "companyName": j.get("organizationName", ""),
        "description_full": j.get("description", "") or j.get("profile", ""),
        "location": loc,
        "postedDate": j.get("publishedAt"),
        "postedTimeAgo": None,
        "contractType": j.get("contractType", ""),
        "recruiterName": "",
        "description": j.get("summary", ""),
        "url": j.get("url", ""),
        "source": "wttj",
        "salary": f"{j.get('salaryMin','')}-{j.get('salaryMax','')} {j.get('salaryCurrency','')}" if j.get("salaryMin") else "",
    }

def norm_hellowork(j):
    return {
        "id": "hw_" + str((j.get("companyUrl") or "") + (j.get("title") or "")),
        "title": j.get("title", ""),
        "companyName": j.get("company", ""),
        "location": j.get("location", ""),
        "postedDate": j.get("datePosted"),
        "postedTimeAgo": None,
        "contractType": j.get("contractType", ""),
        "recruiterName": "",
        "description": (j.get("qualifications", "") or "") + " " + " ".join(j.get("skills", []) or []),
        "url": j.get("companyUrl", ""),
        "source": "hellowork",
        "salary": j.get("salary", ""),
    }

for j in raw.get("linkedin", []):
    normalized.append(norm_linkedin(j))
for key in raw:
    if key.startswith("wttj"):
        for j in raw[key]:
            normalized.append(norm_wttj(j))
for j in raw.get("hellowork", []):
    normalized.append(norm_hellowork(j))

print("Total normalized:", len(normalized))

# Cross-board dedup by normalized company+title (loose)
def norm_key(j):
    import re
    c = re.sub(r"\b(sas|sa|sarl)\b", "", (j["companyName"] or "").lower()).strip()
    t = re.sub(r"\b(h/f|f/h|cdi|cdd|senior|junior)\b", "", (j["title"] or "").lower()).strip()
    t = re.sub(r"\s+", " ", t)
    return (c, t)

seen_keys = set()
deduped = []
for j in normalized:
    k = norm_key(j)
    if k in seen_keys:
        continue
    seen_keys.add(k)
    deduped.append(j)

print("After cross-board dedupe:", len(deduped))

cfg = yaml.safe_load(Path("config/search-profile.yaml").read_text())
seen_path = Path("data/seen-jobs.json")
seen_ids = set()
if seen_path.exists():
    seen_ids = set(json.loads(seen_path.read_text()).get("ids", []))

kept, stats, examples = filter_jobs(deduped, cfg, seen_ids)
print(json.dumps(stats, indent=2))
for kind, items in examples.items():
    if items:
        print(f"  dropped ({kind}): {', '.join(items[:5])}")

with open("data/filtered-2026-10-05.json", "w") as f:
    json.dump(kept, f, indent=2, ensure_ascii=False)

sector_hits = [j for j in kept if j.get("_target_sector")]
print("Sector hits:", len(sector_hits))
for j in sector_hits:
    print(" -", j["companyName"], "|", j["title"], "|", j["source"])
