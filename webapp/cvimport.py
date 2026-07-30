"""CV panel backend: PDF → Markdown conversion with a diff preview.

Flow: upload PDF → pdfplumber extracts text → the package-writing LLM
restructures it into the exact section layout of the existing master file
(copying text only — the prompt forbids adding content) → the UI shows an
old-vs-new diff → a separate commit call writes the file.

The pending conversion is held in memory keyed by a token, so nothing touches
context/cv-master*.md until the user confirms the diff.
"""

from __future__ import annotations

import difflib
import re
import secrets
from pathlib import Path

from llm import generate, model_for

ROOT = Path(__file__).resolve().parent.parent

_pending: dict[str, dict] = {}

STRUCTURE_SYSTEM = """You convert the raw text of Nicolas Wajs's CV (extracted from a PDF)
into Markdown matching the EXACT structure of his existing master file.

Rules — all hard:
1. Use ONLY text present in the extracted PDF. Never add, embellish or infer
   content. Fixing whitespace/hyphenation broken by PDF extraction is allowed.
2. Reproduce the existing master file's section headings VERBATIM and in the
   same order (they are shown below). Map the PDF's content into them. If the
   PDF has no content for a section, keep the heading with a comment
   `<!-- no content in uploaded PDF -->`.
3. Experience entries use the same `### Role — Company, Team` heading style as
   the existing file.
4. Keep the trailing guidance sections of the existing file (e.g. narrative
   principles / notes) UNCHANGED — copy them from the existing file as-is;
   they are instructions, not CV content, and the PDF won't contain them.
5. Return only the Markdown document, no preamble, no code fence.

=== EXISTING MASTER FILE (structure + trailing sections to preserve) ===
{existing}"""


def extract_pdf_text(pdf_bytes: bytes) -> str:
    import io

    import pdfplumber

    parts = []
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            parts.append(page.extract_text() or "")
    text = "\n\n".join(parts).strip()
    if not text:
        raise ValueError("No extractable text found in this PDF (is it a scan?).")
    return text


def convert(pdf_bytes: bytes, which: str) -> dict:
    """Run extraction + restructuring. Returns {token, diff, new_markdown}."""
    target = ROOT / "context" / ("cv-master-fr.md" if which == "fr" else "cv-master.md")
    existing = target.read_text(encoding="utf-8")
    raw_text = extract_pdf_text(pdf_bytes)

    new_md = generate(
        STRUCTURE_SYSTEM.format(existing=existing),
        "Raw text extracted from the uploaded PDF:\n\n" + raw_text,
        model=model_for("package"),
    ).strip()
    # Strip an accidental wrapping code fence.
    m = re.match(r"^```(?:markdown)?\n(.*)\n```$", new_md, re.S)
    if m:
        new_md = m.group(1)
    new_md += "\n"

    diff = "\n".join(
        difflib.unified_diff(
            existing.splitlines(), new_md.splitlines(),
            fromfile=f"context/{target.name} (current)",
            tofile=f"context/{target.name} (from PDF)",
            lineterm="",
        )
    )
    token = secrets.token_hex(8)
    _pending[token] = {"target": target, "content": new_md}
    return {"token": token, "diff": diff, "new_markdown": new_md, "file": target.name}


def commit(token: str) -> str:
    entry = _pending.pop(token, None)
    if not entry:
        raise KeyError("No pending CV conversion for this token — re-upload the PDF.")
    target: Path = entry["target"]
    backup = target.with_suffix(".md.bak")
    backup.write_text(target.read_text(encoding="utf-8"), encoding="utf-8")
    target.write_text(entry["content"], encoding="utf-8")
    return f"wrote context/{target.name} (previous version kept at context/{backup.name})"


def discard(token: str) -> None:
    _pending.pop(token, None)
