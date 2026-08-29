# Target Companies — 2026-08-30 (offline pass, no fresh scrape)

**Note:** Apify returned a live 403 "Monthly usage hard limit exceeded" on a
test POST to `valig~linkedin-jobs-scraper` at scan time (usage cycle window
per `/users/me/limits` shows `endAt: 2026-08-29T23:59:59Z`, but the account's
`monthlyUsageUsd` was still $5.92 against a $5 cap and the actor call was
rejected outright). This is a genuine outage, not a missing connector. This
run is an **offline pass over the existing scored sheet**
(`applications/Job_Matches_Paris_ProductAI.xlsx`, 1259 scored rows) — no new
postings were scraped.

## Top scored jobs (existing data)

| Score | Company | Title | Status |
|---|---|---|---|
| 10.0 | LSEG | Senior Product Manager, AI | Not yet applied (package exists: `2026-07-30_LSEG_Senior-PM-AI`) |
| 9.0 | Euroclear | Digital Assets Product Development | Not yet applied (package exists) |
| 9.0 | Western Union | Director, Digital Product - Europe | Not yet applied (package exists) |
| 9.0 | Qonto | Staff Product Manager [AI Products expertise] | Not yet applied (package exists) |
| 9.0 | Wivoo, a Wavestone Company | Lead AI Product Manager - Agentic & ML | Not yet applied (package exists; excluded-company by name pattern, built anyway per repo precedent) |
| 9.0 | Euronext | Chief Product Officer, Digital Assets | Not yet applied |
| 9.0 | Mistral AI | Product Monetization & Pricing Lead | Not yet applied |
| 8.0 | Dataiku | Product Manager – Business Applications | Not yet applied |
| 8.0 | Shine | VP of Product - CPA Portfolio | Not yet applied |
| 8.0 | Axway | Principal Product Manager | Not yet applied |

## Auto-prep gate (>=9.3/10)
Only **LSEG — Senior Product Manager, AI (10.0/10)** clears the 9.3 bar.
It already has an application package folder
(`applications/2026-07-30_LSEG_Senior-PM-AI/package.md`), so per the
scan-jobs dedup rule it was **not** re-run through `prep-application`.

No new job cleared the 93% bar this cycle.
