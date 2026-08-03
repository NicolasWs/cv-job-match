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

## Step 3 — Score (if not already scored)

Apply `scoring.weights` from the config. Produce for each job a 0-10 fit score
and a two-line justification naming **the biggest strength and the biggest gap**.
Never inflate a score to be encouraging — a 5 that is honest is more useful than
an 8 that isn't.

## Step 3.5 — Research the company (feeds the cover letter's "why this
## company / why now" beat)

For each selected job, gather 1–3 concrete, current signals about the
company: recent news, a product launch, a challenge or priority named by a
founder/exec on their own site, blog, or in an interview. If a web search
tool is available, use it and prefer the company's own words over
third-party speculation. If none is available, use only what's in the job
posting itself. Never invent news, launches, or quotes — if nothing specific
turns up, say so and fall back to the most concrete detail in the posting.

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
{addressed to the named recruiter if known, else the hiring team. Must
include one sentence — in the opening or as a standalone line before the
close — that argues *why this company, why now*, grounded in the company
research from Step 3.5. This is motivation, not fit: don't just restate
qualifications.}

## LinkedIn Outreach Message
{≤ 90 words, specific to this posting}
```

## Step 5 — Save

- Local: `applications/{YYYY-MM-DD}_{Company}_{Role-slug}/package.md`
- Drive: create a subfolder in `JobApplications` named the same way, upload
  `package.md` as a Google Doc.
- Then call `present_files` on what was created.

---

## Hard rules

- **Never invent experience, metrics, employers, or dates.** Every claim traces
  to the CV. If the posting wants something Nicolas hasn't done, the honest move
  is to name the gap and pivot to the closest real evidence — that is what makes
  these letters credible.
- **Match the posting's language natively.** A French posting gets French
  written as French, not translated English.
- **Apply the narrative principles** from `context/narrative-rules.md` (or the
  defaults in `cv-master.md`): lead with impact, emphasize skills over duration,
  freelance since Jul 2025 is a deliberate strategic choice and not a gap.
- **Keep cover letters under 250 words.** Three paragraphs: why this role, the
  evidence, the close.
- **The "why this company / why now" beat is required, and must be sourced.**
  Trace it to the job posting, company notes, or a web search result from
  Step 3.5 — never invent news, launches, or quotes the company hasn't
  actually stated.
- **Flag excluded-but-interesting.** If a requested company matches
  `exclude_company_patterns` (a consultancy/ESN), build the package anyway if
  explicitly asked, but say plainly that it's normally filtered out and why.
