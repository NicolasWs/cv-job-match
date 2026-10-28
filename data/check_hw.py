import json, os
import urllib.request

TOKEN = os.environ["APIFY_TOKEN"]

def get(url):
    req = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read())

r = get(f"https://api.apify.com/v2/actor-runs/v46BkxceMNcdxK7VR?token={TOKEN}")
d = r["data"]
print(json.dumps({"status": d.get("status"), "statusMessage": d.get("statusMessage"), "exitCode": d.get("exitCode"), "defaultDatasetId": d.get("defaultDatasetId")}, indent=2))
