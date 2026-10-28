---
name: company-research
description: Research a target company for a specific job opportunity — company/website summary, recent significant company news (funding, leadership, restructuring, expansion, product launches), a recent company video, open-position counts, and a full investor-style Due Diligence memo (business model, competitive benchmark, financial health, bull/bear case, open questions) — all sourced, dated, and never fabricated. Use whenever the user asks to "research this company", "look into {Company}", "what's going on at {Company}", "do due diligence on {Company}", or before an application/interview when deep company context is needed.
---

# Company Research

Produce a bounded, sourced, dated research brief for ONE company, tied to a
specific job opportunity. Every claim must be independently checkable via a
real source URL. "Nothing found" is always a valid, first-class output —
never fabricate or pad with generic filler to look complete.

This skill has four components, built incrementally across separate tickets:

| Section | Status | Ticket |
|---|---|---|
| Company / website summary | **implemented** | NIC-49 |
| Recent Company News | **implemented** | NIC-52 |
| Recent company video | **implemented** | NIC-50 |
| Open position counts | **implemented** | NIC-51 |
| Due Diligence memo | **implemented** | NIC-54 |

Each section below is self-contained — it can be run independently, or all
combined into one brief (assembly of the full brief onto a Notion job page is
a separate ticket, NIC-53; this skill only produces the content). The Due
Diligence memo is the deep-dive layer — run it whenever the user wants
investor-grade scrutiny on a company, not just the news/summary sections.

## Inputs (common to all sections)
- **Company name** — from the job opportunity/Notion job page. If ambiguous
  (a common word, or multiple distinct companies share the name), disambiguate
  using the job posting's industry/HQ city.
- **Today's date** — read from the environment/session at run time. Every
  section that has a recency rule computes its cutoff from *this* date, never
  a hardcoded or previously-cached date.

---

## Section: Company / website summary (NIC-49)

_Not yet implemented — placeholder for the sibling ticket. Do not build this
here; NIC-49's Builder owns this section's procedure and output contract._

---

## Section: Recent Company News (NIC-52)

Produce a maximum of 3 significant, dated, sourced news items about the
company from the last 6 months — or an explicit "none found" statement.
Never fabricate a headline, date, source, or rationale.

### 1. Search

Use the session's native web-search/fetch capability only. **No new paid
Apify actor, no dedicated news API, no LinkedIn access.**

Recommended query pattern (run at least once):
```
"{company name}" (funding OR acquisition OR layoffs OR restructuring OR "new CEO" OR expansion OR "product launch") {current year}
```
If the company name is ambiguous, add a disambiguating term from the job
posting (industry, HQ city) to the query. Follow up with a fetch of the most
promising result pages to confirm the specific publish date and details
before including an item — a search-result snippet alone is not sufficient
to populate the per-item fields in step 4.

### 2. Significance filter — five categories

An item qualifies **only** if it is about the specific company being
researched (not the industry in general, not a competitor, not a vague
market-trend piece) **and** fits one of these five categories:

| Category | Include (examples) | Exclude (examples) |
|---|---|---|
| Funding / financial event | Funding round (seed/Series A–D+), acquisition of the company, the company acquiring another company, IPO filing/completion, major investment announcement | Routine investor-relations boilerplate with no new dollar figure or milestone |
| Expansion | New office/market/country launch, publicly announced major hiring wave, entering a new product line/vertical | A single new job posting (that's not "news" — that's the job board itself) |
| Leadership change | New CEO/C-suite hire or departure, board changes, founder transition | A LinkedIn post congratulating an internal promotion with no press coverage |
| Restructuring | Layoffs, reorg announcement, department closure/consolidation, leadership departure tied to a strategy shift | Normal attrition, individual employee departures |
| Product launch / major partnership | A new flagship product/feature launch with press coverage, a strategic partnership announcement | Minor feature updates, changelog entries, routine marketing content |

**Always excluded, regardless of category:** industry awards/rankings,
generic "best places to work" listicles, sponsored content/press-release
mills with no independent verification, opinion/analyst pieces that don't
report a specific event, and anything with no discoverable specific publish
date (see step 3).

For each candidate item, note internally which category it matched (this
traceability step does not appear in the final output, but every kept item
must be able to name its category if asked — this is what makes the filter
followable/auditable rather than a vague judgment call).

**Source quality bar:** prefer primary sources (the company's own
newsroom/press page, a named mainstream or trade-press outlet) over
content-farm aggregators or unverified social posts. A single unverified
tweet/LinkedIn-style post is not sufficient sourcing on its own for an
otherwise-qualifying event.

### 3. Recency cutoff

Compute **today's date minus 6 calendar months** at generation time (not
hardcoded, not the date the job was first selected). An item qualifies only
if its own publish date is on or after that cutoff.

If a candidate item has no discoverable, specific publish date, **discard
it** — do not include it with a guessed or approximate date.

### 4. Per-item output — exactly 4 fields, in this order

```
- **Headline:** <verbatim or lightly-trimmed source headline, not embellished>
- **Date:** <YYYY-MM-DD, the source's own publish date>
- **Source:** <full article URL>
- **Why it matters for this application:** <one sentence, specific to this company/role, not generic filler>
```

### 5. Item count — max 3, never padded

Minimum 0, maximum 3 items.

- If more than 3 items qualify, keep the **3 most significant** and drop the
  rest — do not list them. Funding/leadership/restructuring events generally
  outrank a product launch or minor expansion, but use judgment on genuine
  impact, not just category order.
- If only 1 or 2 items qualify, output only those 1 or 2. **Never pad to 3
  with a lower-quality or borderline item just to hit the max.** Fewer,
  well-qualified items beats 3 items that look complete.

### 6. No significant news found — exact string

When zero items qualify after the filter and the recency cutoff, the
section's entire output is **exactly**:

```
No significant news found for {Company} in the last 6 months.
```

with `{Company}` substituted for the real company name. Not omitted, not an
apology, not hedged, not a substituted stale/irrelevant item. This is a
first-class, unremarkable, expected output for small/private/quiet
companies — not a failure mode to work around by lowering the significance
bar.

### 7. Retrieval stamp

The section states the date the search was run, distinct from each item's
own publish date:

```
_Retrieved: {today's date, YYYY-MM-DD}_
```

### 8. Search-failure vs. genuine "none found"

If the web-search/fetch tooling itself fails or times out, retry once. If it
still fails, report `Unable to complete news search this run.` — a distinct
message from the "no significant news found" string above (one is a tooling
failure, the other is a genuine negative result; do not conflate them).

### Worked example (illustrative only, not fabricated data — see this
ticket's real verification runs in `docs/ARCHITECTURE.md` / `docs/PLAN.md`,
NIC-52 section, in the `cv-job-match-v2` repo for actual search output)

```
## Recent Company News
_Retrieved: 2026-09-12_

- **Headline:** Mistral AI raises €3 billion Series D led by Samsung at €21B+ valuation
- **Date:** 2026-09-08
- **Source:** https://www.cnbc.com/2026/09/08/mistral-ai-funding-valuation-samsung.html
- **Why it matters for this application:** A record European Series D signals aggressive scaling ahead — a strong talking point for why product hiring is accelerating right now.

- **Headline:** Mistral AI acquires Vienna-based physics-AI startup Emmi AI
- **Date:** 2026-05-19
- **Source:** https://thenextweb.com/news/mistral-emmi-ai-physics-vienna-industrial
- **Why it matters for this application:** Shows Mistral expanding into industrial/physics-AI verticals — relevant if the role touches enterprise/industrial product lines.

- **Headline:** Mistral AI secures $830 million in debt financing for Paris data center
- **Date:** 2026-03-30
- **Source:** https://www.reuters.com/business/finance/frances-mistral-raises-830-million-debt-ai-data-centre-build-up-2026-03-30/
- **Why it matters for this application:** Confirms continued infrastructure investment in France — useful context for a Paris-based role's growth trajectory.
```

(A 4th qualifying item — the Sept 10, 2026 Cloudera partnership — was dropped
per the step 5 cap; a 5th candidate — the Feb 17, 2026 Koyeb acquisition —
was discarded per the step 3 recency cutoff, since it predates
2026-03-12.)

---

## Section: Recent company video (NIC-50)

_Not yet implemented — placeholder for the sibling ticket._

---

## Section: Open position counts (NIC-51)

_Not yet implemented — placeholder for the sibling ticket._

---

## Section: Due Diligence Memo (NIC-54)

Produce an investor-grade due-diligence memo on the company — the depth a
professional considering *buying the whole company* would want, not an
interview-cheat-sheet summary. Reuses Recent Company News (NIC-52) as one
input rather than re-searching it from scratch.

### 1. Research sweep

Run these searches (adapt wording to the company/sector; skip a row only
when it is genuinely inapplicable, e.g. no funding history for a 100-year-old
incumbent — say so, don't skip silently):

| Area | Query pattern |
|---|---|
| Business model / market | `"{company}" business model OR "how {company} makes money"` |
| Market size & category | `"{company}" market size OR "{company}" category leader OR "{company}" market share` |
| Competitors | `"{company}" vs OR "{company}" competitors OR "{company}" alternative` |
| Funding / financials | `"{company}" funding round OR valuation OR revenue OR ARR OR profitable` |
| Leadership & governance | `"{company}" CEO OR leadership OR board OR founder` |
| Reviews / culture / attrition | `"{company}" glassdoor OR employee reviews OR layoffs` |
| Risk / controversy | `"{company}" lawsuit OR investigation OR controversy OR churn OR customer complaints` |

Fetch (don't just skim snippets of) the most promising results before citing
a specific figure, date, or quote — a search-result snippet is not a source,
the fetched page is. Prefer primary/authoritative sources (company filings,
investor-relations pages, named mainstream/trade press, Glassdoor/Crunchbase
aggregate data) over SEO content farms.

### 2. Named competitors — minimum 2, maximum 4

Identify the company's real direct competitors (same product category and
buyer, not just "same industry"). For each, note one line on how the target
company compares — product scope, pricing posture, scale/market share,
funding stage, or technical approach — each claim sourced. If credible
competitors can't be found/verified, say so rather than guessing from
category alone.

### 3. Financial snapshot

Report what is actually disclosed, nothing inferred:
- Funding stage, most recent round amount + date, valuation if public,
  named investors — for VC-backed companies.
- Revenue/ARR, profitability, growth rate — only if publicly stated by the
  company or a named financial press source; never estimate or extrapolate.
- For private companies with no disclosed financials: state plainly
  `Financials not publicly disclosed — {Company} is privately held with no
  reported figures found.` This is a first-class, expected output, not a gap
  to paper over with a market-size guess.

### 4. Bull case (strengths / differentiators) — 3-5 points

What makes the company attractive/defensible: product differentiation,
technical moat, team/founder pedigree, market timing, customer traction,
partnerships, funding runway. Each point cited; each point should be the kind
of thing a candidate could credibly bring up in an interview as "why I want
to join."

### 5. Bear case (weaknesses / risks) — 3-5 points

What could go wrong or already has: competitive pressure, funding/runway
risk, leadership turnover, negative review themes (recurring complaints, not
one angry outlier), layoffs/restructuring, regulatory or legal exposure,
customer concentration or churn signals, product/market fit doubts. Each
point cited. This section exists specifically so weaknesses aren't softened
or omitted — an honest bear case is the point of the exercise.

### 6. Open questions — 5-8, investor-style

The probing questions a professional doing real due diligence would ask
before committing (money, or a job) — not generic interview-prep questions.
Mix of:
- Questions already answered by research (state the answer + source inline).
- Questions genuinely unresolved from public sources — flag each
  `**[ask live]**` as something worth raising with the interviewer/recruiter,
  since that is a legitimate and impressive thing to ask in an interview.

Examples of the register wanted: "What is the path to profitability given
the last disclosed burn rate?", "How concentrated is the customer base — is
there a key-account dependency?", "Has the competitive gap versus {named
competitor} widened or narrowed in the last 12 months?", "What explains the
{N}-month gap in leadership announcements / the recent exec departure?"

### 7. Output format

```
## Due Diligence Memo — {Company}
_Retrieved: {today's date, YYYY-MM-DD}_

### Thesis
<1-2 sentences: what this company is, and the one-line investment/career case for or against it>

### Bull Case
- <point> ([source](url))
- ...

### Bear Case
- <point> ([source](url))
- ...

### Competitive Benchmark
| Competitor | How {Company} compares |
|---|---|
| <name> | <one line, sourced> |

### Financial Snapshot
<funding stage / round / valuation / investors, or the "not disclosed" line>
([source](url) where applicable)

### Open Questions
1. <question> — <answer + source, or **[ask live]**>
...

### Sources
- [Title](url) — {YYYY-MM-DD if dated}
```

### 8. Guardrails

- Never fabricate a figure, quote, competitor, or date. Every factual claim
  in Bull Case, Bear Case, Financial Snapshot, and answered Open Questions
  carries an inline source link.
- Distinct from Recent Company News (NIC-52): that section is 3 recent dated
  events; this memo is the standing analytical picture. Reuse any NIC-52
  items that are relevant as Bull/Bear evidence instead of re-fetching them,
  but don't limit the memo's sourcing to only those 3 items.
- "Not enough public information to assess X" is a valid, expected answer
  for small/private companies — never pad with speculation to look thorough.
- If the company name is ambiguous, disambiguate the same way as the News
  section (industry/HQ city from the job posting) before researching.
