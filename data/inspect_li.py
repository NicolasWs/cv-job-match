import json

jobs = json.load(open('data/last-raw.json'))
li = [j for j in jobs if j.get('_source') == 'linkedin']
print(len(li))
for j in li[:8]:
    print(sorted(j.keys()))
    print(j.get('title'), '|', j.get('companyName') or j.get('company'), '|', j.get('postedDate') or j.get('postedAt'))
