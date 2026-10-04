import os, json, urllib.request

def read_env():
    env = {}
    with open(os.path.expanduser('~/.hermes/.env')) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            k, v = line.split('=', 1)
            env[k] = v
    return env

env = read_env()
TOKEN = env.get('APIFY_TOKEN')

def get(url):
    with urllib.request.urlopen(url, timeout=60) as r:
        return json.loads(r.read())

runs = json.load(open('data/apify_runs.json'))
items = []

def pull(dataset_id, source):
    url = f"https://api.apify.com/v2/datasets/{dataset_id}/items?token={TOKEN}&clean=true"
    data = get(url)
    for it in data:
        it['_source'] = source
    return data

items += pull(runs['linkedin']['datasetId'], 'linkedin')
for g in runs.get('glassdoor', []):
    items += pull(g['datasetId'], 'glassdoor')
for w in runs.get('wttj', []):
    items += pull(w['datasetId'], 'wttj')
if 'hellowork' in runs:
    items += pull(runs['hellowork']['datasetId'], 'hellowork')

print("total raw items:", len(items))
json.dump(items, open('data/last-raw.json', 'w'), indent=2)
