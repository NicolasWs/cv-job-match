import os, json, time, sys
import requests
import yaml

TOKEN = None
for line in open(os.path.expanduser('~/.hermes/.env')):
    line = line.strip()
    if line.startswith('APIFY_TOKEN='):
        TOKEN = line.split('=', 1)[1].strip()
assert TOKEN, "no token"

cfg = yaml.safe_load(open('config/search-profile.yaml'))
titles = cfg['search']['titles']
location = cfg['search']['location']
work_modes = cfg['search']['work_modes']
max_age_days = cfg['filters']['max_age_days']
date_posted_map = {30: 'r2592000', 7: 'r604800', 1: 'r86400'}
date_posted = cfg['search'].get('date_posted', 'r2592000')

def start_run(actor, payload):
    url = f"https://api.apify.com/v2/acts/{actor.replace('/', '~')}/runs?token={TOKEN}"
    r = requests.post(url, json=payload, timeout=60)
    r.raise_for_status()
    d = r.json()['data']
    return d['id'], d['defaultDatasetId']

runs = {}

# LinkedIn
try:
    rid, ds = start_run('valig/linkedin-jobs-scraper', {
        "titles": titles, "location": location, "workModes": work_modes,
        "maxAgeDays": max_age_days
    })
    runs['linkedin'] = {'runId': rid, 'datasetId': ds}
except Exception as e:
    print(f"linkedin start failed: {e}", file=sys.stderr)

# WTTJ - one per title
runs['wttj'] = []
for t in titles:
    try:
        rid, ds = start_run('clearpath/welcome-to-the-jungle-jobs-api', {
            "query": t, "location": "Paris", "countryCode": "FR",
            "datePosted": date_posted, "includeDetails": True, "maxItems": 100
        })
        runs['wttj'].append({'title': t, 'runId': rid, 'datasetId': ds})
    except Exception as e:
        print(f"wttj {t} start failed: {e}", file=sys.stderr)

# HelloWork
try:
    rid, ds = start_run('solidcode/hellowork-scraper', {
        "searchQueries": titles, "location": "Paris", "datePosted": date_posted,
        "includeJobDetails": True, "maxResults": 150
    })
    runs['hellowork'] = {'runId': rid, 'datasetId': ds}
except Exception as e:
    print(f"hellowork start failed: {e}", file=sys.stderr)

# Glassdoor - one per title
runs['glassdoor'] = []
for t in titles:
    try:
        rid, ds = start_run('valig/glassdoor-jobs-scraper', {
            "keywords": t, "location": "Paris (France)", "daysOld": max_age_days, "limit": 100
        })
        runs['glassdoor'].append({'title': t, 'runId': rid, 'datasetId': ds})
    except Exception as e:
        print(f"glassdoor {t} start failed: {e}", file=sys.stderr)

json.dump(runs, open('data/apify_runs.json', 'w'), indent=2)
print("started:", json.dumps(runs, indent=2))
