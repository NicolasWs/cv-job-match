import json, os
import urllib.request

TOKEN = os.environ["APIFY_TOKEN"]

def get_items(dataset_id):
    url = f"https://api.apify.com/v2/datasets/{dataset_id}/items?token={TOKEN}&clean=true"
    req = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read())

datasets = {
    "linkedin": "Zv1hSKCDKPqhfr2xT",
    "wttj_ai_pm": "cFHtTcZp5LLXPEPag",
    "wttj_head_of_product": "xvxladA1CNtt7Uejm",
    "wttj_pm_fintech": "21yOs3kwsgxEcEPsQ",
    "wttj_lead_pm": "dq74zNU7L0J3EUZVp",
    "wttj_director": "iuaPxgyGfV6eZmmqM",
    "hellowork": "NMAaXyhZsgPlz4LcZ",
}

all_items = {}
for name, ds in datasets.items():
    try:
        items = get_items(ds)
        all_items[name] = items
        print(name, len(items))
    except Exception as e:
        print(name, "ERROR", e)
        all_items[name] = []

with open("data/raw_items_2026-10-05.json", "w") as f:
    json.dump(all_items, f)
