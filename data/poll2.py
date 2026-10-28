import json, os, time
import urllib.request
import urllib.error

TOKEN = os.environ["APIFY_TOKEN"]

def get_run(run_id):
    url = f"https://api.apify.com/v2/actor-runs/{run_id}?token={TOKEN}"
    req = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read())

pending = [("wttj_director", "j5vELmcaklNCWS87T"), ("hellowork", "v46BkxceMNcdxK7VR")]
deadline = time.time() + 350
statuses = {}
while time.time() < deadline and pending:
    all_done = True
    for name, rid in pending:
        r = get_run(rid)
        st = r.get("data", {}).get("status", "UNKNOWN")
        statuses[name] = st
        if st not in ("SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"):
            all_done = False
    if all_done:
        break
    time.sleep(10)

print(json.dumps(statuses, indent=2))
