import os, json, requests, sys

TOKEN = os.environ["APIFY_TOKEN"]
BASE = "https://api.apify.com/v2"

titles = ["AI Product Manager", "Head of Product", "Product Manager Fintech", "Lead Product Manager", "Director of Product"]
location = "Paris, France"
max_age_days = 60

def start(actor, payload):
    url = f"{BASE}/acts/{actor}/runs?token={TOKEN}"
    r = requests.post(url, json=payload, timeout=30)
    try:
        data = r.json()
    except Exception:
        return {"error": r.text, "status_code": r.status_code}
    if r.status_code >= 300:
        return {"error": data, "status_code": r.status_code}
    return {"runId": data["data"]["id"], "datasetId": data["data"]["defaultDatasetId"]}

runs = {}

# LinkedIn - one run
runs["linkedin"] = [start("valig~linkedin-jobs-scraper", {
    "titles": titles, "location": location, "workModes": ["1","3"], "maxAgeDays": max_age_days
})]

# Indeed - one run per title
runs["indeed"] = []
for t in titles:
    runs["indeed"].append(start("misceres~indeed-scraper", {
        "position": t, "country": "FR", "location": "Paris", "maxItems": 100
    }))

# WTTJ - one run per title
runs["wttj"] = []
for t in titles:
    runs["wttj"].append(start("clearpath~welcome-to-the-jungle-jobs-api", {
        "query": t, "location": "Paris", "countryCode": "FR", "datePosted": "LAST_30_DAYS", "includeDetails": True, "maxItems": 100
    }))

# HelloWork - one combined run
runs["hellowork"] = [start("solidcode~hellowork-scraper", {
    "searchQueries": titles, "location": "Paris", "datePosted": "LAST_30_DAYS", "includeJobDetails": True, "maxResults": 150
})]

# Glassdoor - one run per title
runs["glassdoor"] = []
for t in titles:
    runs["glassdoor"].append(start("valig~glassdoor-jobs-scraper", {
        "keywords": t, "location": "Paris (France)", "daysOld": max_age_days, "limit": 100
    }))

with open("/home/nicow/cv-job-match/data/apify_runs_20261028.json", "w") as f:
    json.dump(runs, f, indent=2)

print(json.dumps(runs, indent=2))
