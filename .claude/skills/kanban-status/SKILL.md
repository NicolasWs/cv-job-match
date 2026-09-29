---
name: kanban-status
description: >
  Conversational one-shot updates to the Status field on the "Job Search
  Kanban" Notion database (e.g. "mark Mistral as applied", "the Danone PM
  role got a first interview"). Resolves a natural-language company/role
  reference to a unique Notion card, maps the requested phrase to one of the
  9 canonical Status values, and writes ONLY that field. Never guesses on
  ambiguity or an unmapped status phrase.
---

# Kanban Status Update

Implements NIC-44 (P1-T3 — Conversational Kanban status updates), scoped by
Product Planner in `cv-job-match-v2/docs/handoffs/NIC-44-product-planner-scope-validation.md`.
This skill is standalone (AC8): it does not require `run-my-week` or any
other orchestrator to be running, and it does not touch `run-my-week` or any
n8n automation (both explicitly out of scope for this ticket).

## Notion targets (hard-coded facts, from NIC-42)

- `database_id`: `dc98669c-8b63-4f20-b6c0-abdafe8222c6`
- `data_source_id`: `47340a66-9e15-4ea1-8edf-45bba44c2334`
- Properties: `Name` (title), `Status` (status, 9 values below), `Company`
  (rich_text), `Role` (rich_text), `Priority` (select).
- API version header required on every call: `Notion-Version: 2025-09-03`.
- Auth: `Authorization: Bearer $NOTION_API_KEY` — the token lives only in
  this header, in-memory / in the shell environment. Never echo it, never
  write it into a file, never log a full request that includes it in a way
  that lands in a committed artifact.

## The 9 canonical Status values (constants — never invent a 10th)

```
selected
cv scored
cover letter done
applied
first interview
second interview
offer
rejected
withdrawn
```

These are pulled verbatim from NIC-42's schema and from Section 6.2 of the
NIC-44 scope doc. The skill must never write any string to `Status` other
than one of these 9 exact values (exact casing, exact spelling, no synonyms
written directly).

## 1. Resolution: natural-language reference → unique Notion `page_id`

1. Parse the user's request into two parts:
   - an **entity reference**: company name and/or role fragment (e.g.
     "Mistral", "the Danone PM role", "the Mistral PM role")
   - a **target status phrase** (e.g. "applied", "got a call")
2. Query the data source:
   `POST /v1/data_sources/47340a66-9e15-4ea1-8edf-45bba44c2334/query`
   - If only a company/role-ish term is given, use an `or` filter across
     `Company` (`rich_text.contains`), `Role` (`rich_text.contains`), and
     `Name` (`title.contains`) with that term.
   - If the user supplied **both** a company fragment and a role fragment,
     use an `and` filter (`Company contains <company-term>` AND `Role
     contains <role-term>`) — do not silently narrow a 2+ match with a role
     guess (Section 6.1.4 of the scope doc). Only fall back to the broader
     `or` query when the user gave one term, not two.

   Example single-term query body:
   ```json
   {
     "filter": {
       "or": [
         {"property": "Company", "rich_text": {"contains": "AcmeCorp"}},
         {"property": "Name", "title": {"contains": "AcmeCorp"}}
       ]
     }
   }
   ```

   Example two-term (company + role) query body:
   ```json
   {
     "filter": {
       "and": [
         {"property": "Company", "rich_text": {"contains": "Nimbus Robotics"}},
         {"property": "Role", "rich_text": {"contains": "Product Manager"}}
       ]
     }
   }
   ```

3. Classify the result set (`len(results)`):
   - **Exactly 1 match** → proceed to the write (Section 2 below), then
     confirm per Section 3.
   - **0 matches** → no write. Tell the user explicitly that no matching
     card was found, naming the exact term(s) searched.
   - **2+ matches** → no write. List every candidate (Name / Company /
     Role / current Status) and ask the user to pick one or restate the
     request with a more specific role. This is the primary false-positive
     mitigation named in the scope doc's risk table.
4. Never fabricate or guess a card. Never auto-pick "most recent" or
   "first" on a 2+ match.

## 2. NL status phrase → canonical value (synonym table)

Look the requested phrase up in this table (case-insensitive substring
match against the example phrases is acceptable, but the resulting write
must always be the exact canonical string in the left column):

| Canonical value | Example accepted phrases |
|---|---|
| `selected` | "mark as selected", "add to pipeline" (rare — normally set at card creation) |
| `cv scored` | "cv scored", "cv done", "cv is ready" |
| `cover letter done` | "cover letter done", "cover letter ready", "letter finished" |
| `applied` | "applied", "mark as applied", "I applied", "sent the application" |
| `first interview` | "first interview", "phone screen", "got a call", "screening call scheduled" |
| `second interview` | "second interview", "next round", "final round" (only if the card's current status is unambiguous — see below) |
| `offer` | "offer", "got an offer", "they offered" |
| `rejected` | "rejected", "turned down", "didn't get it", "no go" |
| `withdrawn` | "withdrawn", "pulled out", "no longer interested", "I withdrew" |

**Ambiguous phrase relative to current status:** "final round" / "next
round" could mean `second interview` for one process but something else for
another. Do not infer from the card's current status (Open Question OQ-2 in
the scope doc — default is "always ask"). If it's unclear which of two
plausible canonical values a phrase maps to, treat it exactly like an
unmapped phrase (below): ask, don't guess.

**Guardrail:** if the requested phrase does not map unambiguously to
exactly one of the 9 values, **do not write**. Respond by listing the 9
valid values verbatim and ask the user to clarify. Never invent a 10th
status, never silently round to the "closest" one.

## 3. Write guardrail — Status only, nothing else

`PATCH /v1/pages/{page_id}` where `{page_id}` is the resolved card's page
ID. The `properties` object in the request body must contain **exactly one
key: `Status`**:

```json
{ "properties": { "Status": { "status": { "name": "applied" } } } }
```

- `Name`, `Company`, `Role`, `Priority` must **never** appear in this
  payload, even with their existing unchanged values. Notion's PATCH only
  touches keys present in the request body, so omitting the rest is both
  necessary and sufficient.
- **Never read-then-rewrite the full property set "for safety."** That
  pattern is exactly what risks accidental overwrites (e.g. a stale
  `Priority` value reverting a manual edit made between read and write).
  Single-property PATCH only, every time.

## 4. Confirmation / interaction style

One-shot, no multi-turn form for the common case:

- **Unique match + valid status phrase** → perform the update immediately,
  then reply in **one line** naming what changed, including both the old
  and new value, e.g.:
  > Marked **AcmeCorp — Backend Engineer** as `applied` (was `cover letter done`).
  Including the *old* value is a lightweight audit signal so a wrong-card
  update is immediately visible.
- **Ambiguous or not-found** → the single short clarifying question
  described above, **no update performed**.
- **Unmapped status phrase** → list the 9 valid values, **no update
  performed**.

## Empirical test evidence (real API calls against the live NIC-42 database)

All calls below were executed for real against `database_id
dc98669c-8b63-4f20-b6c0-abdafe8222c6` / `data_source_id
47340a66-9e15-4ea1-8edf-45bba44c2334` using `curl` + `$NOTION_API_KEY`
(`Notion-Version: 2025-09-03`). Three test cards were created, exercised,
and archived (`archived: true`) at the end of the session — none remain
visible in the live Kanban view. Full request/response JSON transcripts are
attached to the NIC-44 Builder handoff, not committed to this repo (avoids
depositing test data or any accidental credential fragment into git
history).

Test cards used:
- **TEST NIC-44 Alpha** — Company "AcmeCorp", Role "Backend Engineer",
  created with Status `cover letter done` → used for the unique-match /
  Status-only-write / unmapped-phrase scenarios.
- **TEST NIC-44 Bravo** — Company "Nimbus Robotics", Role "Product
  Manager", Status `applied`.
- **TEST NIC-44 Charlie** — Company "Nimbus Robotics", Role "Data
  Engineer", Status `selected`.
  (Bravo + Charlie share `Company = "Nimbus Robotics"` with different
  `Role`, purpose-built for the 2+ match scenario.)

### (a) Unique match → Status-only write succeeds
- Query `Company/Name contains "AcmeCorp"` → 1 result (TEST NIC-44 Alpha,
  page_id `3d705073-c5b0-8197-b926-cb39d52f4e1f`).
- `PATCH /v1/pages/{page_id}` body: `{"properties": {"Status": {"status":
  {"name": "applied"}}}}` — response 200, `Status.status.name` returned as
  `"applied"`.
- `GET` before vs. after: `Name`, `Company`, `Role`, `Priority` all
  byte-identical (`AcmeCorp` / `Backend Engineer` / `Med` unchanged);
  `Status` changed `cover letter done` → `applied`. Confirms AC1, AC2
  (payload contained only the `Status` key), AC3, AC7.

### (b) 0 matches → no write
- Query `Company/Name contains "ZorbTechGalaxyXYZ"` (a term with no
  matching card) → `results: []`, 0 matches.
- No `PATCH` call issued. Skill response would name the exact term
  searched and state no matching card was found. Confirms AC4.

### (c) 2+ matches → no write, candidates listed
- Query `Company/Name contains "Nimbus Robotics"` → 2 results (TEST NIC-44
  Bravo, page_id `3d705073-c5b0-81d7-89d4-e736be1c163b`, Role "Product
  Manager", Status `applied`; TEST NIC-44 Charlie, page_id
  `3d705073-c5b0-8172-9dc1-fc10c9f2e400`, Role "Data Engineer", Status
  `selected`).
- No `PATCH` call issued. Confirms AC5.
- Follow-up: combined `and` filter (`Company contains "Nimbus Robotics"`
  AND `Role contains "Product Manager"`) narrows correctly to exactly 1
  result (Bravo only) — confirms Section 6.1.4's "company+role together
  must both match" behavior works as designed.

### (d) Unmapped status phrase → no write, 9 values listed
- Scenario: "mark AcmeCorp as ghosted" — entity resolves uniquely (1
  match), but "ghosted" does not appear anywhere in the Section 2 synonym
  table.
- No `PATCH` call issued (verified by re-`GET`ing the card immediately
  after: `Status` still read `applied`, i.e. the value set by test (a),
  unchanged by this scenario). Confirms AC6.

### Case-sensitivity of `rich_text.contains` (Risk table, Section 8)

**Empirically confirmed: `rich_text.contains` (and `title.contains`) are
case-insensitive substring matches.** Querying `Company contains "AcmeCorp"`
(exact case), `"acmecorp"` (lowercase), `"ACMECORP"` (uppercase), and
`"AcMeCoRp"` (mixed case) against the same live card all returned
identically 1 matching result each. This deviates from the scope doc's
Section 8 caution ("not yet empirically confirmed... if case-sensitive,
normalize casing before filtering") — no normalization step is required.
The skill's resolution logic (Section 1 above) can pass the user's search
term to Notion as-is without lowercasing/uppercasing it first.

### AC8 — standalone invocability

This skill has no dependency on `run-my-week` state, checkpoints, or any
other skill's output — it only needs `NOTION_API_KEY` in the environment
and the `data_source_id`/`database_id` constants above. It can be invoked
directly in a fresh session with zero prior pipeline state.

## Deviations from the scope doc

None in the resolution/synonym/guardrail design. The one adjustment is
documented above: Section 8's case-sensitivity risk resolved to "no
normalization needed" rather than "normalize before filtering," because
Notion's `contains` filter is empirically case-insensitive for both
`rich_text` and `title` property types on this data source.
