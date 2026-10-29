"""
One place for model selection and model-specific request settings.

Default: gpt-6-luna, OpenAI's replacement for gpt-4o-mini (which shuts down
on January 14, 2027). Luna is a reasoning model, so it takes a reasoning
effort and `max_completion_tokens` instead of `temperature` and
`max_tokens`. Older non-reasoning models (gpt-4o-mini, gpt-4.1-mini) keep
their previous settings, so switching back is a configuration change only.

Environment variables:
- OPENAI_MODEL: model for the standard path (default gpt-6-luna)
- OPENAI_AGENT_MODEL: model for the Agents SDK path (defaults to OPENAI_MODEL)
- OPENAI_REASONING_EFFORT: none, low, medium or high (default low). Extraction
  from short notes does not need deep reasoning; low keeps latency and cost down.
"""

from __future__ import annotations

import os

DEFAULT_MODEL = "gpt-6-luna"
DEFAULT_REASONING_EFFORT = "low"
VALID_REASONING_EFFORTS = {"none", "low", "medium", "high"}

# Models that do not accept a reasoning effort and still use temperature.
_NON_REASONING_PREFIXES = ("gpt-4", "gpt-3.5")

LEGACY_MAX_TOKENS = 1900
# Reasoning tokens count toward this limit, so it needs headroom beyond the
# visible JSON output.
REASONING_MAX_COMPLETION_TOKENS = 6000


def standard_model() -> str:
    return (os.getenv("OPENAI_MODEL") or "").strip() or DEFAULT_MODEL


def agent_model() -> str:
    return (os.getenv("OPENAI_AGENT_MODEL") or "").strip() or standard_model()


def is_reasoning_model(model: str) -> bool:
    return not model.strip().lower().startswith(_NON_REASONING_PREFIXES)


def reasoning_effort() -> str:
    effort = (os.getenv("OPENAI_REASONING_EFFORT") or "").strip().lower()
    return effort if effort in VALID_REASONING_EFFORTS else DEFAULT_REASONING_EFFORT


def chat_completion_settings(model: str) -> dict:
    """Keyword arguments for chat.completions.create that suit the model."""
    if is_reasoning_model(model):
        return {
            "max_completion_tokens": REASONING_MAX_COMPLETION_TOKENS,
            "reasoning_effort": reasoning_effort(),
        }
    return {"temperature": 0.2, "max_tokens": LEGACY_MAX_TOKENS}


def agent_model_settings(model: str):
    """ModelSettings for the Agents SDK, or None to use SDK defaults."""
    if not is_reasoning_model(model):
        return None
    try:
        from agents import ModelSettings
        from openai.types.shared import Reasoning
    except ImportError:
        return None
    return ModelSettings(reasoning=Reasoning(effort=reasoning_effort()))
