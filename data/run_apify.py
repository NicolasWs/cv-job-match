import json, os, sys, time
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

titles = ["AI Product Manager", "Head of Product", "Product Manager Fintech", "Lead Product Manager", "Director of Product"]

runs = {}

# LinkedIn
li = post("valig~linkedin-jobs-scraper", {
    "titles": titles,
    "location": "Paris, France",
    "workModes": ["1", "3"],
    "maxAgeDays": 60,
    "limit": 40
})
runs["linkedin"] = li.get("data", li)

# WTTJ - one run per title
runs["wttj"] = []
for t in titles:
    r = post("clearpath~welcome-to-the-jungle-jobs-api", {
        "query": t, "location": "Paris", "countryCode": "FR",
        "datePosted": "30", "includeDetails": True, "maxItems": 100
    })
    runs["wttj"].append({"title": t, "resp": r.get("data", r)})

# HelloWork
hw = post("solidcode~hellowork-scraper", {
    "searchQueries": titles,
    "location": "Paris",
    "datePosted": "1m",
    "includeJobDetails": True,
    "maxResults": 150
})
runs["hellowork"] = hw.get("data", hw)

# Glassdoor - one run per title
runs["glassdoor"] = []
for t in titles:
    r = post("valig~glassdoor-jobs-scraper", {
        "keywords": t, "location": "Paris (France)", "daysOld": 60, "limit": 100
    })
    runs["glassdoor"].append({"title": t, "resp": r.get("data", r)})

with open("data/apify_runs2.json", "w") as f:
    json.dump(runs, f, indent=2)

print("done")
