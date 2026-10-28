import json
d = json.load(open("data/raw_items_2026-10-05.json"))
j = d["wttj_ai_pm"][0]
print([k for k in j.keys()])
