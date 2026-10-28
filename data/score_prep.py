import json, re, yaml

cfg = yaml.safe_load(open('config/search-profile.yaml'))
jobs = json.load(open('data/filtered-2026-10-04.json'))

sectors = []
for cat in cfg['target_sectors'].values():
    sectors.extend(cat)

def norm(s):
    return re.sub(r'[^a-z0-9]', '', (s or '').lower())

sector_norms = [(s, norm(s)) for s in sectors]

hits = []
for j in jobs:
    company = j.get('company') or j.get('employer', {}).get('name') if isinstance(j.get('employer'), dict) else j.get('company')
    if not company:
        emp = j.get('employer')
        company = emp.get('name') if isinstance(emp, dict) else (j.get('companyName') or '')
    cn = norm(company)
    for s, sn in sector_norms:
        if sn and sn in cn:
            hits.append({
                'title': j.get('title'),
                'company': company,
                'url': j.get('url') or j.get('seoUrl') or j.get('jobUrl'),
                'source': j.get('_source'),
                'age_days': j.get('ageInDays') or j.get('_age_days'),
                'sector_match': s,
            })
            break

print("total kept jobs:", len(jobs))
print("target-sector hits:", len(hits))
seen_urls = set()
dedup = []
for h in hits:
    if h['url'] in seen_urls:
        continue
    seen_urls.add(h['url'])
    dedup.append(h)
print("unique target-sector hits:", len(dedup))
json.dump(dedup, open('data/sector-hits-2026-10-04.json', 'w'), indent=2)
for h in dedup:
    print(h['company'], '|', h['title'], '|', h['source'], '|', h['url'])
