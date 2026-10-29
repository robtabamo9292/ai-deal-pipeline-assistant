"""Model selection and model-specific request settings."""
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from src import model_config
from src.llm import analyze_deal_with_llm

VALID_JSON = (
    '{"company_name":"Acme","sector":"SaaS","subsector":"Workflow",'
    '"business_model":"Subscription","stage":"Seed","description":"Workflow software",'
    '"traction_signals":["$500K ARR"],"customer_signals":["Clinics"],'
    '"funding_signals":[],"risks":["Competition"],"diligence_questions":[],'
    '"crm_tags":[],"relationship_context":"Research notes",'
    '"recommended_next_step":"Review cohorts","evidence_excerpts":[]}'
)


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    for name in ["OPENAI_MODEL", "OPENAI_AGENT_MODEL", "OPENAI_REASONING_EFFORT"]:
        monkeypatch.delenv(name, raising=False)


def test_default_model_is_gpt_6_luna():
    assert model_config.standard_model() == "gpt-6-luna"
    assert model_config.agent_model() == "gpt-6-luna"


def test_environment_overrides_model(monkeypatch):
    monkeypatch.setenv("OPENAI_MODEL", "gpt-4o-mini")
    assert model_config.standard_model() == "gpt-4o-mini"
    assert model_config.agent_model() == "gpt-4o-mini"
    monkeypatch.setenv("OPENAI_AGENT_MODEL", "gpt-6-luna")
    assert model_config.agent_model() == "gpt-6-luna"


def test_reasoning_model_uses_reasoning_settings():
    settings = model_config.chat_completion_settings("gpt-6-luna")
    assert settings == {"max_completion_tokens": 6000, "reasoning_effort": "low"}


def test_legacy_model_keeps_temperature_settings():
    settings = model_config.chat_completion_settings("gpt-4o-mini")
    assert settings == {"temperature": 0.2, "max_tokens": 1900}


def test_invalid_reasoning_effort_falls_back_to_low(monkeypatch):
    monkeypatch.setenv("OPENAI_REASONING_EFFORT", "extreme")
    assert model_config.reasoning_effort() == "low"
    monkeypatch.setenv("OPENAI_REASONING_EFFORT", "medium")
    assert model_config.reasoning_effort() == "medium"


def test_agent_settings_only_for_reasoning_models():
    assert model_config.agent_model_settings("gpt-4o-mini") is None
    settings = model_config.agent_model_settings("gpt-6-luna")
    assert settings is not None
    assert settings.reasoning.effort == "low"
    assert settings.temperature is None


@pytest.mark.parametrize(
    ("model", "expected", "forbidden"),
    [
        ("gpt-6-luna", {"max_completion_tokens", "reasoning_effort"}, {"temperature", "max_tokens"}),
        ("gpt-4o-mini", {"temperature", "max_tokens"}, {"max_completion_tokens", "reasoning_effort"}),
    ],
)
def test_chat_request_sends_settings_for_the_model(monkeypatch, model, expected, forbidden):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_MODEL", model)
    client = MagicMock()
    client.chat.completions.create.return_value = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=VALID_JSON))]
    )
    with patch("src.llm.OpenAI", return_value=client):
        deal = analyze_deal_with_llm("Company: Acme. $500K ARR. Clinics use the product. " * 3)

    kwargs = client.chat.completions.create.call_args.kwargs
    assert kwargs["model"] == model
    assert expected.issubset(kwargs)
    assert not forbidden & set(kwargs)
    assert deal.model_name == model
