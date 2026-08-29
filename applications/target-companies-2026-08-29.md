# Company Radar — 2026-08-29 (OFFLINE PASS — no fresh scrape)

**Apify unreachable this run:** all four board scrapes (LinkedIn, WTTJ, HelloWork,
Glassdoor) returned `403 platform-feature-disabled — Monthly usage hard limit
exceeded` on every actor call. This is a genuine Apify account-level outage,
not a missing connector. No new postings were fetched. This radar and the
scoring below are an **offline re-pass over the existing
`Job_Matches_Paris_ProductAI.xlsx`** (1,259 rows / 1,001 unique company+title
pairs, last real scrape 2026-08-28) — no data was fabricated, nothing new was
added to the sheet.

## Top companies by best existing Fit Score (excluding excluded ESN/consulting patterns)

| Rank | Company | Best Fit Score | Openings (this dataset) | Notes |
|---|---|---|---|---|
| 1 | **LSEG** | 10/10 | 2 | Already has an application package (`applications/2026-07-30_LSEG_Senior-PM-AI/`) — no new auto-prep needed. |
| 2 | **Mistral AI** | 9/10 | 6 | Best-fit role (Product Monetization & Pricing Lead) is pricing/monetization, not a core PM role — flagged before as a partial angle. |
| 3 | **Qonto** | 9/10 | 3 | Already has a package (`applications/2026-07-30_Qonto_Staff-PM-AI/`). |
| 4 | **Euroclear** | 9/10 | 2 | Already has a package (`applications/2026-07-30_Euroclear_Digital-Assets-Product/`). |
| 5 | **Euronext** | 9/10 | 2 | Already has a package (`applications/2026-07-30_Euronext_...` — Chief Product Officer, Digital Assets). |
| 6 | **Western Union** | 9/10 | 1 | Already has a package (`applications/2026-07-30_WesternUnion_Director-Digital-Product/`). |
| 7 | Shine | 8/10 | 3 | Fintech target sector, VP Product — CPA Portfolio. |
| 8 | Dataiku | 8/10 | 2 | AI-platform target sector. |
| 9 | Quadient | 8/10 | 2 | E-invoicing, Director of Product & Strategy. |
| 10 | Valtech | 8/10 | 1 | AI Product Manager / Product Owner. |
| 11 | Axway | 8/10 | 1 | Principal Product Manager. |
| 12 | Pennylane | 7/10 | 18 | Fintech target, very high posting volume — worth a recurring check. |
| 13 | Hublo | 7/10 | 8 | Multiple PM roles across boards. |
| 14 | STATION F | 7/10 | 6 | Multiple AI PM roles. |
| 15 | Natixis | 7/10 | 5 | large_financial target sector. |

## Bottom line for this run
No new company crosses the `coach.auto_prep_min_score` (9.3) bar. The only
job at or above 9.0 that lacks an existing `applications/*/package.md` is
none — every 9+ scored job in the current sheet already has a package from
prior runs. **Next scan should retry the live scrape** once the Apify
monthly limit resets (Apify plans typically reset on the account's monthly
anniversary/billing date — check the Apify console).
