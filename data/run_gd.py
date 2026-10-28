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
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read())

titles = ["AI Product Manager", "Head of Product", "Product Manager Fintech", "Lead Product Manager", "Director of Product"]

gd_results = []
for t in titles:
    r = post("valig~glassdoor-jobs-scraper", {
        "keywords": t, "location": "Paris (France)", "daysOld": 60, "limit": 100
    })
    d = r.get("data", r)
    gd_results.append({"title": t, "raw": d})
    time.sleep(2)

with open("data/apify_runs_gd.json", "w") as f:
    json.dump(gd_results, f, indent=2)

print(json.dumps([{"title": x["title"], "id": x["raw"].get("id"), "err": x["raw"].get("error")} for x in gd_results], indent=2))
