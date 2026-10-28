import json, os, time
import urllib.request
import urllib.error

TOKEN = os.environ["APIFY_TOKEN"]

def post(actor, body):
    url = f"https://api.apify.com/v2/acts/{actor}/runs?token={TOKEN}"
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return {"error": e.read().decode()}

def get_run(run_id):
    url = f"https://api.apify.com/v2/actor-runs/{run_id}?token={TOKEN}"
    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return {"error": e.read().decode()}

titles = ["AI Product Manager", "Head of Product", "Product Manager Fintech", "Lead Product Manager", "Director of Product"]

results = {"wttj_extra": None, "hellowork": None, "glassdoor": []}

# WTTJ Director of Product (missed earlier)
results["wttj_extra"] = post("clearpath~welcome-to-the-jungle-jobs-api", {
    "query": "Director of Product", "location": "Paris", "countryCode": "FR",
    "datePosted": "30", "includeDetails": True, "maxItems": 100
})

# HelloWork (1 run, all titles)
results["hellowork"] = post("solidcode~hellowork-scraper", {
    "searchQueries": titles,
    "location": "Paris",
    "datePosted": "1m",
    "includeJobDetails": True,
    "maxResults": 150
})

with open("data/apify_runs3.json", "w") as f:
    json.dump(results, f, indent=2)

# poll these two
pending = []
d = results["wttj_extra"].get("data", results["wttj_extra"])
if "id" in d:
    pending.append(("wttj_director", d["id"]))
d2 = results["hellowork"].get("data", results["hellowork"])
if "id" in d2:
    pending.append(("hellowork", d2["id"]))

deadline = time.time() + 400
statuses = {}
while time.time() < deadline and pending:
    all_done = True
    for name, rid in pending:
        r = get_run(rid)
        st = r.get("data", r).get("status", "UNKNOWN")
        statuses[(name, rid)] = st
        if st not in ("SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"):
            all_done = False
    if all_done:
        break
    time.sleep(10)

print("batch2 statuses:", json.dumps({f"{n}|{r}": s for (n, r), s in statuses.items()}, indent=2))

# Now launch Glassdoor, 5 titles, respecting concurrency (1 run per title, sequential if needed)
gd_results = []
for t in titles:
    while True:
        r = post("valig~glassdoor-jobs-scraper", {
            "keywords": t, "location": "Paris (France)", "daysOld": 60, "limit": 100
        })
        d = r.get("data", r)
        if "error" in d.get("error", {}) if isinstance(d.get("error"), dict) else False:
            pass
        if "id" in d:
            gd_results.append({"title": t, "id": d["id"]})
            break
        else:
            # concurrency error, wait and retry
            time.sleep(15)

with open("data/apify_runs_gd.json", "w") as f:
    json.dump(gd_results, f, indent=2)

# poll glassdoor
deadline = time.time() + 400
statuses2 = {}
pending2 = [(item["title"], item["id"]) for item in gd_results]
while time.time() < deadline and pending2:
    all_done = True
    for name, rid in pending2:
        r = get_run(rid)
        st = r.get("data", r).get("status", "UNKNOWN")
        statuses2[(name, rid)] = st
        if st not in ("SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"):
            all_done = False
    if all_done:
        break
    time.sleep(10)

print("glassdoor statuses:", json.dumps({f"{n}|{r}": s for (n, r), s in statuses2.items()}, indent=2))
