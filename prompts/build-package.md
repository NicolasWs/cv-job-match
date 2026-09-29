# Build Application Package — on-demand, any job

Generate a complete tailored application package for **one or more jobs** from
the weekly scrape results. Works for any job in the list, not just the top-ranked
ones.

## Trigger phrases
- "build a package for Euronext"
- "make packages for ranks 6 through 12"
- "package the top 3 fintech ones"
- "do the Mistral role, in French"

---

## Step 1 — Load context

1. Read `config/search-profile.yaml`.
2. Load the most recent `jobs-YYYY-MM-DD.json` from the Drive `JobApplications`
   folder (or the local path if the user points at one).
3. Pick the CV per `cv.language`:
   - `en` → `context/cv-master.md`
   - `fr` → `context/cv-master-fr.md`
   - `auto` → detect the language of **that job's** description and use the
     matching CV. A French posting gets a French package.
   Always read `cv.fact_source` (`cv-master-fr.md`) as well — it holds the
   precise stack, metrics, and full certification list even when writing in
   English.
4. **When a fact (stack, metric, certification) appears in `cv.fact_source`
   but not in the language-matched CV, prefer it and include it in the
   output.** Concretely: the LangChain/RAG, crewAI, Dataiku, and KNIME
   certifications (FR CV, Certifications section) and the 40% Woon
   sourcing-time-reduction metric (FR CV, TradeValue/Woon bullet) exist only
   in the FR file — they belong in EN packages too, never dropped.

## Step 2 — Resolve which jobs

Accept any of these selectors and resolve them against the scrape results:

| User says | Resolve to |
|---|---|
| a company name | all jobs at that company |
| "rank N" / "ranks N-M" | those positions in the scored list |
| "the fintech ones" | `target_sector == "fintech"` |
| "everything above 7" | `fit_score >= 7` |
| "the ones with a recruiter" | `has_recruiter == true` |

If a selector matches more than 8 jobs, list them and ask which to proceed with
rather than generating 20 packages unprompted.

## Step 2bis — Research the company

For each selected job, gather **2–3 recent public signals** about the company —
a product launch, a funding round, an exec quote, a roadmap post, a market
move. For every signal, note **where and when** it was found (e.g. "company
engineering blog, March 2026") so each citation stays checkable.

- The cover letter must reference **at least one specific company
  product/initiative/statement** from this research — real company detail,
  not generic praise. (For a named recruiter, see the personalization rule
  in Step 4.)
- **Honesty guardrail:** if no verifiable signal is found, the letter must
  say what is specifically known — e.g. from the posting itself — and
  **never invent a signal**. An invented product, quote, or date breaks the
  same rule as an invented CV fact. Every cited signal carries a source
  note or is omitted.

## Step 3 — Score (if not already scored)

Apply `scoring.weights` from the config. Produce for each job a 0-10 fit score
and a two-line justification naming **the biggest strength and the biggest gap**.
Never inflate a score to be encouraging — a 5 that is honest is more useful than
an 8 that isn't. Anchor the score on this rubric:

- **9–10:** near-exact overlap — every major requirement evidenced with a CV
  metric, no material gap.
- **7–8:** strong domain/seniority overlap with **one named material gap** —
  the justification must name it concretely.
- **5–6:** partial overlap — 2+ material gaps or a seniority stretch.
- **≤ 4:** don't send.

These anchors extend the honesty rule above (never inflate): a 7+ score
whose justification names no concrete gap is not an honest score.

## Step 4 — Generate the package

For each selected job, produce a `package.md` with these sections:

```
# {Company} — {Role} ({Location})
Job URL: {url}
Recruiter: {name} — {linkedin_url}        ← omit the line entirely if none
Fit score: {n}/10 — {one-line reason}

## Match Score
{Strong|Good|Partial}. Biggest strength: … Biggest gap: …

## Edit Suggestions
- **Retitle:** …
- **Rewrite summary:** …
- **Downplay / drop:** …
- **Elevate / add:** …

## Tailored CV (excerpt)
{reordered, re-weighted CV — never fabricated}

## Cover Letter
{addressed to the named recruiter if known, else the hiring team}

## LinkedIn Outreach Message
{≤ 90 words, specific to this posting}
```

### Recruiter personalization

The template's `Recruiter: {name} — {linkedin_url}` field drives real
personalization. **When the LinkedIn URL is present:** read that recruiter's
profile and pull at least one real line from it — background, a mutual
connection, a recent post — then include one sentence in the cover letter
that could only have been written to that specific recruiter, and address
the letter to them by name. No URL on the line → address the hiring team;
never fabricate familiarity with a recruiter you know nothing about.

### Cover letter — opening, evidence order, why-now, close

- **Break the template across the batch:** within any single week's batch,
  never reuse the same opening structure or the same closing sentence
  across packages. If two letters could be swapped between companies
  unnoticed, one of them is not done.
- **Order evidence for this posting:** present proof points in the order
  that matters most for *this* role — not chronologically, and not the same
  order every package. Two postings drawing on the same underlying
  experience must still present that evidence differently.
- **Opening — choose one of three patterns per package:**
  1. **Company-signal lead:** open on a specific, sourced signal from
     Step 2bis (a launch, a market move) and connect it to the role.
  2. **Role-requirement lead:** open on the posting's hardest requirement
     and answer it with the single strongest CV evidence.
  3. **Industry-observation lead:** open on a shift in the company's market
     — regulation, technology, customer behavior — and place Nicolas
     inside it.
- **Why-now beat (required):** one sentence in the intro or a standalone
  line before the close arguing *why this company / why now* — motivation,
  distinct from the *why the fit exists* qualification argument. It must
  not restate qualifications.
- **Concrete close (required):** the closing paragraph must include a
  concrete availability window or follow-up commitment (e.g. "available
  from October", "I'll follow up the week of 15 September"). Never end on a
  soft invitation such as "I'd welcome a conversation about the role".

### LinkedIn outreach message

The LinkedIn message follows the same close rule as the letter: end with a
concrete ask tied to a window or date ("open to a quick chat this week?" —
not a bare "would love to connect"). Keep it ≤ 90 words and specific to
this posting.

## Step 5 — Save

- Local: `applications/{YYYY-MM-DD}_{Company}_{Role-slug}/package.md`
- Drive: create a subfolder in `JobApplications` named the same way, upload
  `package.md` as a Google Doc.
- Then call `present_files` on what was created.
- **Log the send:** when the package is actually sent, remind the user to
  set `status=sent` and `sent_date` on the job's row in the tracker
  (`applications/Job_Matches_Paris_ProductAI.xlsx`; the status/outcome
  vocabulary is documented in `tools/add_outcome_columns.py`) so outcomes
  can be reviewed later.

---

## Hard rules

- **Never invent experience, metrics, employers, or dates.** Every claim traces
  to the CV. If the posting wants something Nicolas hasn't done, the honest move
  is to name the gap and pivot to the closest real evidence — that is what makes
  these letters credible. The same rule governs company research: a signal
  without a checkable source is omitted, not embellished.
- **Match the posting's language natively.** A French posting gets French
  written as French, not translated English.
- **Apply the narrative principles** from `context/narrative-rules.md` (or the
  defaults in `cv-master.md`): lead with impact, emphasize skills over duration,
  freelance since Jul 2025 is a deliberate strategic choice and not a gap.
- **Keep cover letters under 250 words.** Three paragraphs: why this role and
  why now, the evidence ordered for this posting, and a concrete close.
- **Break the template.** Within any single week's batch, packages must not
  reuse the same opening structure or the same closing sentence (see Step 4's
  three opening patterns and concrete-close rule).
- **Flag excluded-but-interesting.** If a requested company matches
  `exclude_company_patterns` (a consultancy/ESN), build the package anyway if
  explicitly asked, but say plainly that it's normally filtered out and why.
