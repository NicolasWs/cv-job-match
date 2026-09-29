> **⚠️ DEPRECATED as of 2026-09-11 — read-only / historical reference only.**
> This Google Sheets tracker model is no longer the active job-application
> tracking system. Active tracking has moved to a **Notion Kanban DB**
> (database_id: `dc98669c-8b63-4f20-b6c0-abdafe8222c6`). Everything below
> this notice is preserved verbatim as historical reference only — do not
> use it to create new tracking entries.

---

# Job Application Tracker — Sheet Model v1

For Google Sheets or Excel on Drive. Balanced for simplicity + useful automation.

## Columns

| # | Column | Type | Description |
|---|--------|------|-------------|
| A | Company | text | Employer name |
| B | Role | text | Job title |
| C | Priority | list: High/Med/Low | How much this role matters |
| D | Match Score | list: Strong/Good/Partial | From JOB_MATCH agent |
| E | Status | list (see below) | Pipeline stage |
| F | Source / Link | url | Where the posting lives |
| G | Date Found | date | When spotted |
| H | Date Applied | date | When application sent |
| I | Contact Name | text | Recruiter / PM / hiring manager |
| J | Contact Email/LinkedIn | text/url | How to reach them |
| K | Last Action | text | e.g. "Sent cover letter" |
| L | Last Action Date | date | When K happened |
| M | Next Follow-up | date | When to chase |
| N | Assets | text/links | Cover letter / tailored CV links |
| O | Notes | text | Anything else |

### Status values (Column E)
`To apply → Applied → Screening → Interview 1 → Interview 2 → Final → Offer →
Rejected → Withdrawn`

## Sample rows

| Company | Role | Priority | Match | Status | Link | Date Found | Date Applied | Contact | Contact | Last Action | Last Date | Next Follow-up | Assets | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Mistral AI | PM, AI Products | High | Strong | Applied | url | 2026-07-18 | 2026-07-20 | J. Doe | linkedin/… | Sent CV+CL | 2026-07-20 | 2026-07-27 | drive/… | Referral via X |
| Dataiku | Product Owner Data | Med | Good | Screening | url | 2026-07-15 | 2026-07-16 | A. Roy | a.roy@… | Recruiter call | 2026-07-22 | 2026-07-25 | drive/… | Asked for portfolio |

## Formulas & conditional formatting (Google Sheets)

**Follow-up overdue** — highlight `Next Follow-up` (M) red when past due and not
closed:
```
=AND($M2<>"", $M2<TODAY(), NOT(REGEXMATCH($E2,"Rejected|Withdrawn|Offer")))
```

**Due within 3 days** — amber:
```
=AND($M2>=TODAY(), $M2<=TODAY()+3)
```

**Priority roles** — bold/green whole row when `Priority=High` and active:
```
=AND($C2="High", NOT(REGEXMATCH($E2,"Rejected|Withdrawn")))
```

**Pipeline count** (dashboard cell): applications currently in interview stages:
```
=COUNTIF(E:E,"Interview 1")+COUNTIF(E:E,"Interview 2")+COUNTIF(E:E,"Final")
```

**Days since applied** (helper column):
```
=IF($H2="","",TODAY()-$H2)
```

## Implementation notes
- Use **Data > Data validation** dropdowns for C, D, E to keep values clean.
- The JOB_MATCH agent fills C/D; the WRITING agent fills N (asset links).
- Excel equivalent: replace `REGEXMATCH` with `OR(ISNUMBER(SEARCH(...)))` and
  use conditional-formatting rules instead of Sheets' formula-based rules.
