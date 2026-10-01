# Target Companies — 2026-10-01 (CV Coach scan, cron)

Fresh Apify scan across LinkedIn, Glassdoor, WTTJ, HelloWork (Apify quota reset
Sept 30 — first real scrape since the monthly cap hit in late August).

**Funnel:** 931 raw items (12 actor runs) → 741 after cross-board dedup → 481
after filters (excl. consulting/ESN, junior titles, freelance, already-seen) →
89 with a Product Manager/Owner/Head of Product title.

## Honest Fit Score (0-10) on the strongest candidates

| Company | Role | Fit | Why |
|---|---|---|---|
| JPMorganChase | Product Director — Intl Insurance Client & Advisor Experience (EMEA), Exec Director, Paris/London | **8.5/10** | Strong financial-services domain match (3/3), seniority fits 15+yr profile (2/2), AI is a feature not the core (1.5/2), JPMorgan is a named large_financial target (2/2), no named recruiter (0/1). |
| AXA France | Head of AI Governance | **7.5/10** | AXA is a named target, AI governance is squarely on-brand, BUT requires managing an 8-10 person team — a real gap vs Nicolas's IC/delivery-lead track record (seniority 1/2), domain 2.5/3, AI 2/2, sector 2/2, recruiter 0/1. |
| Euronext | Product Manager, Digital Assets (Paris/London) | **6/10** | Target-sector hit, but capital-markets/custody/tokenisation is a narrower domain fit than Nicolas's risk/trading background; no recruiter named. |
| Mistral AI | Head of, Financial Systems Engineering | — | Already has a package: `applications/2026-09-29_Mistral-AI_Head-of-Financial-Systems-Engineering/`. |
| BNP Paribas (Estreem) | Product Manager Issuing | 5/10 | Fintech/payments target sector but junior-leaning scope for Nicolas's seniority. |
| Crédit Agricole (BforBank) | Chef de Produit Assurance Vie Senior | 5/10 | Insurance product domain fit but IC product-manager scope under a "Chef de Produit Senior" non-exec title; no AI angle. |

**None cleared the 9.3/10 (`coach.auto_prep_min_score`) auto-prep bar this
run.** No new packages were auto-built.

## openpyxl / xlsx note
`Job_Matches_Paris_ProductAI.xlsx` was not updated this run — `openpyxl` is
unavailable in this cron session's Python and `pip install` is blocked by the
unattended-session security policy (no approvals.cron_mode: approve set).
This file is the Company Radar markdown instead; xlsx sync can be run from an
interactive session.
