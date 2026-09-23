# CV Self-Review (fresh-context read) — cv-v1.md vs frozen requirement list

No Agent/subagent tool is available in this execution environment, so this
is a single fresh-context self-review pass (re-reading the draft cold
against the rubric), not the full multi-round blind-critic loop the skill
describes for Claude Code sessions. Reporting one round, honestly.

## Frozen requirement list (weighted: must=2, nice=1)
1. (2) 12-15+ yrs enterprise SaaS PM experience
2. (2) 3+ yrs people management
3. (2) Direct eInvoicing/e-Reporting/tax-compliance/Financial Automation product experience
4. (2) Deep knowledge: Peppol, EU ViDA, country CTC models, UBL/Factur-X/XRechnung
5. (2) Delivered complex compliance-driven platform products on fixed regulatory timelines
6. (2) Technical fluency: APIs, integrations, validation/transformation engines, AI workflows
7. (2) Excellent English; working French/other EU language advantage
8. (2) Comfort in global matrixed org
9. (1) Leading global team of PM + product-marketing leaders
10. (1) External representation (OpenPeppol, EESPA, tax authorities)
11. (1) Own product P&L
12. (1) M&A evaluation/integration experience

## Relevance map
| # | Requirement | Evidence in CV | Strength |
|---|---|---|---|
| 1 | 15+ yrs enterprise SaaS PM | Full career arc, Opensee/Finastra/Thomson Reuters | H |
| 2 | People management | Mentored 30+30(Misys)/100+FTE(Reuters QA); no formal "manager" title | M |
| 3 | Direct eInvoicing/tax-compliance PM | **None** — not in CV, nothing to cite | **Gap** |
| 4 | Peppol/ViDA/CTC/UBL/Factur-X/XRechnung | **None** | **Gap** |
| 5 | Compliance-driven delivery on fixed deadlines | Opensee ISO27001/SOC2 go-live, Finastra regulatory advisory, Natixis regulated cutover | H |
| 6 | Technical fluency (APIs/integrations/AI) | NiFi, Python library, LangChain/RAG cert, AI SDLC delivery | H |
| 7 | English/French | Native French, fluent English | H |
| 8 | Global matrixed org | Finastra EMEA/Americas, Misys Europe/Asia | H |
| 9 | Leading PM + product-marketing team | Mentoring evidence exists; no product-marketing leadership shown | M |
| 10 | External representation (OpenPeppol/EESPA/tax authorities) | **None** | **Gap** |
| 11 | Own product P&L | Not explicit in CV | **Gap** |
| 12 | M&A evaluation | **None** | **Gap** |

## Findings
- **Major** — Requirements #3 and #4 (the two heaviest, most specific
  must-haves) have zero direct evidence. The CV correctly does not
  fabricate any; it names the gap plainly in a "Why this role" section
  instead. This is the right call per the guardrails, but it means the
  honest **Match Score is Partial, not Strong** — recorded as such below,
  not inflated.
- **Minor** — "3+ yrs people management" (#2) is evidenced by mentoring/
  training, not formal direct reports; kept honest by using "mentored/
  trained" language rather than claiming a management title that isn't in
  the source CV.
- **Minor** — P&L ownership (#11) and M&A (#12) are nice-to-haves with no
  CV evidence; left out rather than stretched.

## Revision made
Tightened the "Why this role" closing paragraph to state the eInvoicing/
Peppol gap in one direct sentence (was already present in v1, kept as
final — no fabrication risk found, so no further rewrite needed beyond
this gap statement already being explicit and prominent).

## Verdict
No further round run — the CV already reports the gap honestly rather than
masking it with vague language; inflating requirements #3/#4 coverage would
require fabricating experience, which the guardrails prohibit. Final CV is
`cv-v1.md` (kept as `cv-final.md` in the package).
