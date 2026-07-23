# Application Tracker — reference

- **File:** Job Application Tracker — Nicolas (Google Sheet)
- **Owner:** nicolas.wajs@gmail.com
- **ID:** `1byMx-OFX0HM6rjCdKP4bKYdvEPuLvEOVWlx8C0iiUPE`
- **URL:** https://docs.google.com/spreadsheets/d/1byMx-OFX0HM6rjCdKP4bKYdvEPuLvEOVWlx8C0iiUPE/edit

## Columns
Company · Role · Priority · Match · Status · Source/Link · Date Found ·
Date Applied · Contact Name · Contact Email/LinkedIn · Last Action ·
Last Action Date · Next Follow-up · Assets · Notes

## Status pipeline
To apply → Applied → Screening → Interview 1 → Interview 2 → Final → Offer →
Rejected → Withdrawn

## Conditional formatting to add manually (Format ▸ Conditional formatting)
- Next Follow-up (col M) past due & not closed → red:
  `=AND($M2<>"", $M2<TODAY(), NOT(REGEXMATCH($E2,"Rejected|Withdrawn|Offer")))`
- Next Follow-up within 3 days → amber:
  `=AND($M2>=TODAY(), $M2<=TODAY()+3)`
- Priority High & active → green row:
  `=AND($C2="High", NOT(REGEXMATCH($E2,"Rejected|Withdrawn")))`
