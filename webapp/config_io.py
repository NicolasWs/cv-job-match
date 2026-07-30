"""Round-trip read/write of config/search-profile.yaml via ruamel.yaml.

ruamel preserves comments, ordering and formatting, so the Filters panel can
save without destroying the annotated YAML.
"""

from __future__ import annotations

import io
from pathlib import Path

from ruamel.yaml import YAML

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "config" / "search-profile.yaml"

_yaml = YAML()
_yaml.preserve_quotes = True
_yaml.width = 100


def load():
    """Return the config as a ruamel CommentedMap (behaves like a dict)."""
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return _yaml.load(f)


def save(data) -> None:
    buf = io.StringIO()
    _yaml.dump(data, buf)  # dump first so a serialization error can't truncate the file
    CONFIG_PATH.write_text(buf.getvalue(), encoding="utf-8")


def _set_list(target_list, new_values) -> None:
    """Replace a CommentedSeq's contents in place, keeping its node identity."""
    target_list.clear()
    target_list.extend([str(v).strip() for v in new_values if str(v).strip()])


def apply_form(form: dict):
    """Merge the Filters-panel form payload into the YAML structure and save.

    Only keys actually present in the payload are touched, so partial saves
    (e.g. just cv_language from the CV panel) can't wipe other fields.
    Comments and untouched sections (scoring, output) are preserved.
    """
    cfg = load()

    search = cfg["search"]
    if "titles" in form:
        _set_list(search["titles"], form["titles"])
    if "location" in form:
        search["location"] = str(form["location"]).strip()
    if "work_modes" in form:
        _set_list(search["work_modes"], form["work_modes"])

    filters = cfg["filters"]
    if "max_age_days" in form:
        filters["max_age_days"] = int(form["max_age_days"])
    if "include_freelance" in form:
        filters["include_freelance"] = bool(form["include_freelance"])
    if "prefer_only_target_sectors" in form:
        filters["prefer_only_target_sectors"] = bool(form["prefer_only_target_sectors"])
    if "exclude_company_patterns" in form:
        _set_list(filters["exclude_company_patterns"], form["exclude_company_patterns"])
    if "exclude_title_patterns" in form:
        _set_list(filters["exclude_title_patterns"], form["exclude_title_patterns"])

    sectors = cfg["target_sectors"]
    for key in ("large_financial", "fintech", "ai_platforms"):
        if key in (form.get("target_sectors") or {}):
            _set_list(sectors[key], form["target_sectors"][key])

    if form.get("cv_language") in ("en", "fr", "auto"):
        cfg["cv"]["language"] = form["cv_language"]

    save(cfg)
    return cfg


def plain(obj):
    """Recursively convert ruamel containers to plain dict/list for JSON."""
    if hasattr(obj, "items"):
        return {k: plain(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [plain(v) for v in obj]
    return obj
