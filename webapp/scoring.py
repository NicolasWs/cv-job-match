"""LLM scoring of jobs against the CV, with a per-job-ID cache.

Cache key = job id + hash of (job description, CV text, weights, model), so
re-scoring an unchanged job is free, while edits to the CV, the weights or the
posting invalidate just the affected entries.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from llm import LLMError, generate, model_for

ROOT = Path(__file__).resolve().parent.parent
CACHE_PATH = Path(__file__).resolve().parent / ".cache" / "scores.json"

SYSTEM_PROMPT = """You score how well ONE job posting fits Nicolas Wajs's profile.

Use these weights (they sum to 1.0) to combine the dimensions into a single
0-10 fit score:
{weights}

Nicolas's CV (source of truth — never assume skills or experience not in it):
<<<CV
{cv}
CV>>>

Return ONLY valid JSON, no prose, no code fence:
{{"score": <number 0-10, one decimal allowed>, "reason": "<one line: top strength; biggest gap — honest, max 140 chars>"}}"""


def _load_cache() -> dict:
    if CACHE_PATH.exists():
        try:
            return json.loads(CACHE_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
    return {}


def _save_cache(cache: dict) -> None:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8")


def _fingerprint(job: dict, cv_text: str, weights: dict, model: str) -> str:
    payload = json.dumps(
        [job.get("description", ""), job.get("title", ""), cv_text, weights, model],
        sort_keys=True, ensure_ascii=False,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _parse_score(text: str) -> dict:
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        raise LLMError(f"scoring model returned no JSON: {text[:200]}")
    data = json.loads(m.group(0))
    score = max(0.0, min(10.0, float(data["score"])))
    return {"score": round(score, 1), "reason": str(data.get("reason", "")).strip()}


def score_jobs(jobs: list[dict], cv_text: str, weights: dict, on_progress=None) -> dict:
    """Score each job (cache-aware). Returns {job_id: {score, reason} | {error}}.

    on_progress(done, total, cached_count) is called after each job, so long
    scoring passes can report live progress.
    """
    model = model_for("scoring")
    system = SYSTEM_PROMPT.format(weights=json.dumps(weights, indent=2), cv=cv_text)
    cache = _load_cache()
    results: dict[str, dict] = {}
    dirty = False
    say = on_progress or (lambda *_a: None)

    for i, job in enumerate(jobs):
        jid = job["id"]
        fp = _fingerprint(job, cv_text, weights, model)
        cached = cache.get(jid)
        if cached and cached.get("fp") == fp:
            results[jid] = {"score": cached["score"], "reason": cached["reason"], "cached": True}
            say(i + 1, len(jobs), sum(1 for r in results.values() if r.get("cached")))
            continue
        user = (
            f"Job posting:\nTitle: {job.get('title')}\nCompany: {job.get('company')}\n"
            f"Location: {job.get('location')}\nContract: {job.get('contract_type')}\n"
            f"Sector tag: {job.get('sector') or 'none'}\n\n"
            f"Description:\n{(job.get('description') or '')[:8000]}"
        )
        try:
            parsed = _parse_score(generate(system, user, model=model, max_tokens=300))
            cache[jid] = {"fp": fp, **parsed}
            results[jid] = {**parsed, "cached": False}
            dirty = True
        except (LLMError, ValueError, KeyError, json.JSONDecodeError) as exc:
            results[jid] = {"error": str(exc)}
        if dirty and (i + 1) % 10 == 0:
            _save_cache(cache)  # long passes shouldn't lose paid scores on a crash
        say(i + 1, len(jobs), sum(1 for r in results.values() if r.get("cached")))

    if dirty:
        _save_cache(cache)
    return results


def cached_scores(jobs: list[dict]) -> dict:
    """Return whatever scores are already cached for these jobs (no LLM calls)."""
    cache = _load_cache()
    return {
        j["id"]: {"score": cache[j["id"]]["score"], "reason": cache[j["id"]]["reason"], "cached": True}
        for j in jobs if j["id"] in cache
    }
