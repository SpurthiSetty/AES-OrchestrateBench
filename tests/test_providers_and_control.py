"""Tests for the cross-provider adapters and the no-injection control mode (AES 2026)."""

from __future__ import annotations

import csv
import sys
from types import SimpleNamespace

import pytest

from orchestratebench import providers, real_run
from orchestratebench.real_run import _call_claude, _is_transient_api_error, run_exp2, run_exp3


@pytest.mark.parametrize(
    "model,provider",
    [
        ("claude-sonnet-4-6", "anthropic"),
        ("gemini-3.8-flash", "gemini"),
        ("gpt-6.1-sol", "openai"),
        ("o4-mini", "openai"),
    ],
)
def test_provider_for(model: str, provider: str) -> None:
    assert providers.provider_for(model) == provider


def test_provider_for_rejects_unknown() -> None:
    with pytest.raises(ValueError):
        providers.provider_for("llama-4")


def test_has_key_accepts_either_gemini_variable(monkeypatch: pytest.MonkeyPatch) -> None:
    for k in ("GEMINI_API_KEY", "GOOGLE_API_KEY"):
        monkeypatch.delenv(k, raising=False)
    assert not providers.has_key("gemini-3.8-flash")
    monkeypatch.setenv("GOOGLE_API_KEY", "x")
    assert providers.has_key("gemini-3.8-flash")


def test_make_client_exits_without_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(SystemExit):
        providers.make_client("gpt-6.1-sol")


def _install_fake_genai(monkeypatch: pytest.MonkeyPatch, seen: dict) -> None:
    class ThinkingConfig:
        def __init__(self, **kw):
            seen["thinking"] = kw

    class GenerateContentConfig:
        def __init__(self, **kw):
            seen["config"] = kw

    types_mod = SimpleNamespace(ThinkingConfig=ThinkingConfig, GenerateContentConfig=GenerateContentConfig)
    monkeypatch.setitem(sys.modules, "google", SimpleNamespace(genai=SimpleNamespace(types=types_mod)))
    monkeypatch.setitem(sys.modules, "google.genai", SimpleNamespace(types=types_mod))


def test_gemini_adapter_matches_anthropic_shape(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: dict = {}
    _install_fake_genai(monkeypatch, seen)
    monkeypatch.delenv("ORCHESTRATEBENCH_GEMINI_THINKING", raising=False)

    def generate_content(**kw):
        seen["call"] = kw
        return SimpleNamespace(text="RESULT=42")

    client = SimpleNamespace(messages=providers._GeminiMessages(
        SimpleNamespace(models=SimpleNamespace(generate_content=generate_content))))
    value, _ = _call_claude(client, "Compute 40 + 2.")
    assert value == 42
    assert seen["call"]["contents"] == "Compute 40 + 2."
    assert seen["thinking"] == {"thinking_level": "minimal"}
    assert seen["config"]["max_output_tokens"] >= providers.NONCLAUDE_MAX_TOKENS


def test_gemini_numeric_thinking_budget(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: dict = {}
    _install_fake_genai(monkeypatch, seen)
    monkeypatch.setenv("ORCHESTRATEBENCH_GEMINI_THINKING", "0")
    msgs = providers._GeminiMessages(SimpleNamespace(models=SimpleNamespace(
        generate_content=lambda **kw: SimpleNamespace(text="RESULT=1"))))
    msgs.create(model="gemini-x", max_tokens=120, messages=[{"role": "user", "content": "p"}])
    assert seen["thinking"] == {"thinking_budget": 0}


def test_openai_adapter_and_empty_response_counter(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: dict = {}
    monkeypatch.delenv("ORCHESTRATEBENCH_OPENAI_REASONING", raising=False)

    def create(**kw):
        seen.update(kw)
        return SimpleNamespace(output_text="")

    providers.EMPTY_RESPONSES["count"] = 0
    client = SimpleNamespace(messages=providers._OpenAIMessages(
        SimpleNamespace(responses=SimpleNamespace(create=create))))
    value, _ = _call_claude(client, "prompt")
    assert value is None
    assert seen["reasoning"] == {"effort": "minimal"}
    assert providers.EMPTY_RESPONSES["count"] == 1


def test_genai_style_error_code_is_transient() -> None:
    class ServerError(Exception):
        code = 503

    class ClientError(Exception):
        code = 400

    assert _is_transient_api_error(ServerError())
    assert not _is_transient_api_error(ClientError())


def test_control_mode_exp2_is_clean(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(real_run, "MOCK", True)
    out = tmp_path / "ctrl.csv"
    rows = run_exp2(None, str(out), n_stages=4, n_runs=3, modes=[None])
    assert {r["failure_mode"] for r in rows} == {"none"}
    assert all(r["final_task_success"] and r["cascade_radius"] == 0 for r in rows)
    with out.open() as fh:
        assert {r["failure_mode"] for r in csv.DictReader(fh)} == {"none"}


def test_control_mode_exp3(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(real_run, "MOCK", True)
    rows = run_exp3(None, str(tmp_path / "c3.csv"), depths=(3, 5), n_runs=2, modes=[None])
    assert len(rows) == 2 * 2 * len(real_run.POLICIES)
    assert all(r["cascade_radius"] == 0 for r in rows)


def test_raw_log_writes_jsonl(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    log = tmp_path / "raw.jsonl"
    monkeypatch.setattr(real_run, "RAW_LOG", str(log))
    client = SimpleNamespace(messages=SimpleNamespace(
        create=lambda **_: SimpleNamespace(content=[SimpleNamespace(type="text", text="RESULT=5")])))
    _call_claude(client, "p")
    import json

    rec = json.loads(log.read_text().strip())
    assert rec["parsed"] == 5 and rec["prompt"] == "p"
