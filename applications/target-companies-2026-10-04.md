# Target Companies — 2026-10-04

Scan: LinkedIn (100 raw, actor returned mostly off-profile retail/service
roles this run — titles param appears to have been ignored by
`valig/linkedin-jobs-scraper`, worth re-checking next run) + Glassdoor
(290 raw across 4 of 5 configured titles; "Director of Product" title
hit a 402 Payment Required on this Apify plan). WTTJ and HelloWork actors
both returned 400 Bad Request on every call — likely actor renamed/retired;
needs investigation before next scheduled scan.

310 jobs survived filters. 20 unique postings hit a named target-sector
company. None are close Product Manager matches — mostly ops/governance/
marketing/legal roles at target companies, not product roles.

## Closest fits (none clear a strong PM match)

| Company | Role | Fit | Angle |
|---|---|---|---|
| AXA France | Head of AI Governance | ~7/10 | AI + financial-services domain overlap, but governance not product build — would need to pivot pitch toward AI risk/compliance framing |
| HSBC | Director, COO Banking Continental Europe | ~6/10 | Director seniority + banking domain, but ops/COO not product |
| Trustpair | Head of Fraud Operations | ~5-6/10 | Fintech target sector, fraud/risk adjacent to product but not a PM title |
| Natixis | Head of Third-Party Oversight | ~5/10 | Target sector hit, but no product or AI angle |
| Swan | Head of Marketing | ~5/10 | Fintech target sector, marketing not product |
| Mistral AI | Head of Financial Systems Engineering / Head of FDE Learning Programs | ~4-5/10 | AI-first target company, but internal finance/ops & L&D roles, not product — a package for the Financial Systems Engineering req already exists (2026-09-29) |

## Action
No job this run clears the 9.3/10 auto-prep bar — no new packages built.
Recommend fixing the WTTJ/HelloWork actor calls and the LinkedIn titles
param before the next scheduled scan, since this run's LinkedIn results
were unusable for sector-matching.
