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
    with urllib.request.urlopen(url, timeout=30) as r:
        return json.loads(r.read())

runs = json.load(open('data/apify_runs.json'))
ids = [('linkedin', runs['linkedin']['runId'])]
for g in runs.get('glassdoor', []):
    ids.append((f"glassdoor-{g['title']}", g['runId']))
for w in runs.get('wttj', []):
    ids.append((f"wttj-{w['title']}", w['runId']))
if 'hellowork' in runs:
    ids.append(('hellowork', runs['hellowork']['runId']))

for name, rid in ids:
    try:
        res = get(f"https://api.apify.com/v2/actor-runs/{rid}?token={TOKEN}")
        d = res['data']
        print(name, rid, d['status'], d.get('stats', {}).get('datasetItemCount'))
    except Exception as e:
        print(name, rid, "ERR", e)
