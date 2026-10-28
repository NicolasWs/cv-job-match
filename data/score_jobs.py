import json, re

kept = json.load(open("data/filtered-2026-10-05.json"))

FIN_KEYWORDS = re.compile(r"\b(bank|banque|banking|finance|financi|fintech|insurance|assurance|asset management|gestion d'actifs|trading|payment|paiement|credit|risk|investment|capital markets)\b", re.I)
AI_STRONG = re.compile(r"\b(AI|IA|artificial intelligence|intelligence artificielle|machine learning|ML|LLM|genai|gen-ai|agentic|agent IA)\b")
AI_WEAK = re.compile(r"\b(data|automation|automatisation|analytics)\b", re.I)
SENIOR_HIGH = re.compile(r"\b(head of|director|directeur|VP|vice president|chief|staff|principal)\b", re.I)
SENIOR_MED = re.compile(r"\b(lead|senior|manager|responsable)\b", re.I)

scored = []
for j in kept:
    title = j.get("title", "") or ""
    desc = j.get("description", "") or ""
    company = j.get("companyName", "") or ""
    text = f"{title} {desc}"

    domain = 3 if FIN_KEYWORDS.search(company) or FIN_KEYWORDS.search(title) else (1.5 if FIN_KEYWORDS.search(desc) else 0)
    seniority = 2 if SENIOR_HIGH.search(title) else (1 if SENIOR_MED.search(title) else 0)
    ai = 2 if AI_STRONG.search(text) else (0.5 if AI_WEAK.search(text) else 0)
    sector_bonus = 2 if j.get("_target_sector") else 0
    recruiter = 1 if j.get("recruiterName") else 0

    score = round(domain + seniority + ai + sector_bonus + recruiter, 2)
    j["_fit_score"] = score
    scored.append(j)

scored.sort(key=lambda x: -x["_fit_score"])

with open("data/scored-2026-10-05.json", "w") as f:
    json.dump(scored, f, indent=2, ensure_ascii=False)

print("Top 25:")
for j in scored[:25]:
    print(f"{j['_fit_score']:>4} | {j['companyName']:<30} | {j['title'][:60]:<60} | {j['source']}")

print()
print(">=9.3:", len([j for j in scored if j["_fit_score"] >= 9.3]))
print(">=8:", len([j for j in scored if j["_fit_score"] >= 8]))
