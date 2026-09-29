#!/usr/bin/env python3
"""Add the outcomes feedback-loop columns to the job-matches tracker.

Usage:
    .venv/bin/python tools/add_outcome_columns.py [path/to/tracker.xlsx]

Appends four columns after the last existing column of every sheet that has a
header row (by default the tracker's single "Job Matches" sheet):

    status      — one of: drafted, sent, replied, interview, rejected, closed
    sent_date   — ISO date (YYYY-MM-DD) the application was sent, else empty
    outcome     — one of: reply, interview, offer, rejection, silence
    notes       — free text (optional convenience column)

Note: the tracker already carries a title-case ``Status`` column owned by the
weekly scrape workflow (values like "Not yet applied"). The new lowercase
``status`` column is deliberately distinct and uses the outcomes vocabulary
above; the pre-existing column and its data are left untouched. Header
matching is exact-case, so the two coexist.

Behaviours:
- Idempotent: columns are only appended when their header is absent, so
  running the script twice never duplicates a column.
- Preserves all existing sheets, columns, rows and cell values untouched.
- Writes ``<file>.bak`` next to the workbook before saving, so the pre-change
  state is always recoverable.

Exit codes: 0 on success (or nothing to do), 1 on a missing file.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import openpyxl

DEFAULT_XLSX = Path(__file__).resolve().parent.parent / (
    "applications/Job_Matches_Paris_ProductAI.xlsx"
)

STATUS_VALUES = ("drafted", "sent", "replied", "interview", "rejected", "closed")
OUTCOME_VALUES = ("reply", "interview", "offer", "rejection", "silence")

COLUMNS = [
    ("status", STATUS_VALUES),
    ("sent_date", None),
    ("outcome", OUTCOME_VALUES),
    ("notes", None),
]


def add_columns(xlsx_path: Path) -> int:
    """Append missing outcome columns to every sheet with a header row.

    Returns the number of columns appended.
    """
    wb = openpyxl.load_workbook(xlsx_path)
    appended = 0

    for ws in wb.worksheets:
        if ws.max_row < 1:
            continue
        headers = {
            str(cell.value).strip(): cell.column  # exact-case: 'Status' != 'status'
            for cell in ws[1]
            if cell.value is not None
        }
        for col_name, _values in COLUMNS:
            if col_name in headers:
                continue  # idempotency: already present, never duplicate
            new_col = ws.max_column + 1
            ws.cell(row=1, column=new_col, value=col_name)
            appended += 1

    if appended:
        backup = xlsx_path.with_suffix(xlsx_path.suffix + ".bak")
        shutil.copy2(xlsx_path, backup)
        wb.save(xlsx_path)
        print(f"backup written: {backup}")
    else:
        print("all outcome columns already present; nothing to do (idempotent)")

    wb.close()
    return appended


def main() -> int:
    xlsx_path = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else DEFAULT_XLSX
    if not xlsx_path.exists():
        print(f"ERROR: workbook not found: {xlsx_path}", file=sys.stderr)
        return 1
    appended = add_columns(xlsx_path)
    print(f"{xlsx_path.name}: {appended} column(s) appended")
    return 0


if __name__ == "__main__":
    sys.exit(main())
