"""Provider adapters for the real-LLM harness (cross-provider check, AES 2026).

The measured-run harness (``real_run.py``) talks to an Anthropic-shaped client:
``client.messages.create(model=..., max_tokens=..., messages=[...])`` returning an
object whose ``.content`` is a list of ``{type: "text", text: ...}`` blocks. To add
non-Claude models without touching the experiment logic, each adapter here exposes
that same surface.

Provider is chosen from the model id:
  claude-*            -> Anthropic   (ANTHROPIC_API_KEY)
  gemini-*            -> Google GenAI (GEMINI_API_KEY or GOOGLE_API_KEY)
  gpt-* / o<digit>*   -> OpenAI      (OPENAI_API_KEY)

Reasoning / thinking control. Gemini and OpenAI reasoning models bill hidden
reasoning tokens as output and count them against the output budget, which can
starve the visible ``RESULT=`` line. For comparability with the Claude runs (no
extended thinking), reasoning is kept at the provider's minimum by default:
  ORCHESTRATEBENCH_GEMINI_THINKING   thinking level, default "minimal"
                                     (set to an integer to use a token budget instead)
  ORCHESTRATEBENCH_OPENAI_REASONING  reasoning effort, default "minimal"
  ORCHESTRATEBENCH_NONCLAUDE_MAX_TOKENS  output budget for non-Claude calls, default 1024
Set either thinking variable to "off" to omit the parameter entirely (for models
that reject it). Every response also records whether visible text was empty, so
starved outputs can be counted rather than silently scored as failures.

API keys are read from the environment only; nothing is logged or written to disk.
"""

from __future__ import annotations

import os
import re
from types import SimpleNamespace
from typing import Any, Dict, List

NONCLAUDE_MAX_TOKENS = int(os.getenv("ORCHESTRATEBENCH_NONCLAUDE_MAX_TOKENS", "1024"))

# Counters for responses with no visible text (reasoning starvation / safety blocks).
EMPTY_RESPONSES: Dict[str, int] = {"count": 0}


def provider_for(model: str) -> str:
    m = model.lower()
    if m.startswith("claude"):
        return "anthropic"
    if m.startswith("gemini"):
        return "gemini"
    if m.startswith("gpt") or re.match(r"^o\d", m):
        return "openai"
    raise ValueError(f"cannot infer provider for model id {model!r}")


def required_key(model: str) -> List[str]:
    """Environment variables, any one of which authenticates this model's provider."""
    return {
        "anthropic": ["ANTHROPIC_API_KEY"],
        "gemini": ["GEMINI_API_KEY", "GOOGLE_API_KEY"],
        "openai": ["OPENAI_API_KEY"],
    }[provider_for(model)]


def has_key(model: str) -> bool:
    return any(os.getenv(k) for k in required_key(model))


def _wrap(text: str) -> SimpleNamespace:
    if not text.strip():
        EMPTY_RESPONSES["count"] += 1
    return SimpleNamespace(content=[SimpleNamespace(type="text", text=text or "")])


def _user_text(messages: List[Dict[str, Any]]) -> str:
    return "\n\n".join(str(m["content"]) for m in messages if m.get("role") == "user")


class _GeminiMessages:
    def __init__(self, client: Any) -> None:
        self._client = client

    def create(self, *, model: str, max_tokens: int, messages: List[Dict[str, Any]]) -> SimpleNamespace:
        from google.genai import types  # lazy import

        cfg: Dict[str, Any] = {"max_output_tokens": max(max_tokens, NONCLAUDE_MAX_TOKENS)}
        thinking = os.getenv("ORCHESTRATEBENCH_GEMINI_THINKING", "minimal").strip().lower()
        if thinking != "off":
            if thinking.lstrip("-").isdigit():
                cfg["thinking_config"] = types.ThinkingConfig(thinking_budget=int(thinking))
            else:
                cfg["thinking_config"] = types.ThinkingConfig(thinking_level=thinking)
        resp = self._client.models.generate_content(
            model=model,
            contents=_user_text(messages),
            config=types.GenerateContentConfig(**cfg),
        )
        return _wrap(getattr(resp, "text", None) or "")


class _OpenAIMessages:
    def __init__(self, client: Any) -> None:
        self._client = client

    def create(self, *, model: str, max_tokens: int, messages: List[Dict[str, Any]]) -> SimpleNamespace:
        kwargs: Dict[str, Any] = {
            "model": model,
            "input": _user_text(messages),
            "max_output_tokens": max(max_tokens, NONCLAUDE_MAX_TOKENS),
        }
        effort = os.getenv("ORCHESTRATEBENCH_OPENAI_REASONING", "minimal").strip().lower()
        if effort != "off":
            kwargs["reasoning"] = {"effort": effort}
        resp = self._client.responses.create(**kwargs)
        return _wrap(getattr(resp, "output_text", None) or "")


def make_client(model: str) -> Any:
    """Return an Anthropic-shaped client for ``model``; exits if its key is missing."""
    provider = provider_for(model)
    if not has_key(model):
        raise SystemExit(
            f"{' or '.join(required_key(model))} not set for {model} "
            f"(or run with ORCHESTRATEBENCH_MOCK=1)"
        )
    if provider == "anthropic":
        from anthropic import Anthropic

        return Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    if provider == "gemini":
        from google import genai

        key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        return SimpleNamespace(messages=_GeminiMessages(genai.Client(api_key=key)))
    from openai import OpenAI

    return SimpleNamespace(messages=_OpenAIMessages(OpenAI(api_key=os.environ["OPENAI_API_KEY"])))
