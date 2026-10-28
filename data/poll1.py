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

with open("data/apify_runs2.json") as f:
    runs = json.load(f)

# collect run ids that are pending
pending = []
pending.append(("linkedin", None, runs["linkedin"]["id"]))
for item in runs["wttj"]:
    d = item["resp"]
    if "id" in d:
        pending.append(("wttj", item["title"], d["id"]))

# poll until all done or 600s
deadline = time.time() + 600
statuses = {}
while time.time() < deadline:
    all_done = True
    for board, title, rid in pending:
        r = get_run(rid)
        st = r.get("data", r).get("status", "UNKNOWN")
        statuses[(board, title, rid)] = st
        if st not in ("SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"):
            all_done = False
    if all_done:
        break
    time.sleep(10)

print(json.dumps({f"{b}|{t}|{r}": s for (b, t, r), s in statuses.items()}, indent=2))
