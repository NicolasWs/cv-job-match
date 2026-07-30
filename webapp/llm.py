"""Provider-agnostic LLM interface: generate(system_prompt, user_prompt, model).

Backends: Mistral (`mistralai` SDK), OpenAI (`openai` SDK, Responses API),
Google (`google-genai` SDK). Nothing outside this module touches a vendor SDK.

Model names were checked against provider docs at build time; if a provider
returns "model not found", check their models page for the current name —
do NOT silently fall back to an older model.
"""

from __future__ import annotations

import os

PROVIDERS = ("mistral", "openai", "google")

KEY_ENV = {
    "mistral": "MISTRAL_API_KEY",
    "openai": "OPENAI_API_KEY",
    "google": "GEMINI_API_KEY",  # GOOGLE_API_KEY also accepted, see _google_key()
}

# Sensible defaults per provider: a cheap model for the bulk scoring pass and
# a stronger one for package writing. Both are user-overridable in Settings.
DEFAULT_MODELS = {
    "mistral": {"scoring": "mistral-small-latest", "package": "mistral-medium-latest"},
    "openai": {"scoring": "gpt-5.6-luna", "package": "gpt-5.6-sol"},
    "google": {"scoring": "gemini-3.1-flash-lite", "package": "gemini-3.5-flash"},
}


class LLMError(Exception):
    """Raised with the provider's actual error text so the UI can show it."""


def _google_key() -> str | None:
    return os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")


def provider_configured(provider: str) -> bool:
    if provider == "google":
        return bool(_google_key())
    return bool(os.environ.get(KEY_ENV.get(provider, "")))


def current_provider() -> str:
    p = os.environ.get("LLM_PROVIDER", "").strip().lower()
    return p if p in PROVIDERS else "mistral"


def model_for(task: str) -> str:
    """task: 'scoring' or 'package'. Env override, else provider default."""
    env_var = "SCORING_MODEL" if task == "scoring" else "PACKAGE_MODEL"
    return os.environ.get(env_var, "").strip() or DEFAULT_MODELS[current_provider()][task]


def generate(system_prompt: str, user_prompt: str, model: str | None = None,
             provider: str | None = None, max_tokens: int = 8000) -> str:
    """Single entry point for every LLM call in the app."""
    provider = provider or current_provider()
    model = model or model_for("package")
    if not provider_configured(provider):
        raise LLMError(
            f"No API key configured for provider '{provider}' — set "
            f"{'GEMINI_API_KEY (or GOOGLE_API_KEY)' if provider == 'google' else KEY_ENV[provider]} "
            "in .env or the Settings panel."
        )
    try:
        if provider == "mistral":
            return _mistral(system_prompt, user_prompt, model, max_tokens)
        if provider == "openai":
            return _openai(system_prompt, user_prompt, model, max_tokens)
        if provider == "google":
            return _google(system_prompt, user_prompt, model, max_tokens)
    except LLMError:
        raise
    except Exception as exc:  # surface the provider's own error text verbatim
        raise LLMError(f"{provider} / {model}: {type(exc).__name__}: {exc}") from exc
    raise LLMError(f"unknown provider: {provider}")


def _mistral(system: str, user: str, model: str, max_tokens: int) -> str:
    from mistralai import Mistral

    client = Mistral(api_key=os.environ["MISTRAL_API_KEY"])
    resp = client.chat.complete(
        model=model,
        max_tokens=max_tokens,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    return resp.choices[0].message.content


def _openai(system: str, user: str, model: str, max_tokens: int) -> str:
    from openai import OpenAI

    client = OpenAI()  # reads OPENAI_API_KEY
    resp = client.responses.create(
        model=model,
        max_output_tokens=max_tokens,
        instructions=system,
        input=user,
    )
    return resp.output_text


def _google(system: str, user: str, model: str, max_tokens: int) -> str:
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=_google_key())
    resp = client.models.generate_content(
        model=model,
        contents=user,
        config=types.GenerateContentConfig(
            system_instruction=system, max_output_tokens=max_tokens
        ),
    )
    return resp.text or ""
