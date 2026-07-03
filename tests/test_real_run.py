from __future__ import annotations

from types import SimpleNamespace

import pytest

from orchestratebench.real_run import _call_claude, _is_transient_api_error


class FakeStatusError(Exception):
    def __init__(self, status_code: int) -> None:
        super().__init__(f"status={status_code}")
        self.status_code = status_code


class APIConnectionError(Exception):
    pass


class APIStatusError(Exception):
    def __init__(self, status_code: int) -> None:
        super().__init__(f"status={status_code}")
        self.status_code = status_code


def _response(text: str) -> SimpleNamespace:
    return SimpleNamespace(content=[SimpleNamespace(type="text", text=text)])


def test_is_transient_api_error_uses_status_code_over_class_name() -> None:
    assert _is_transient_api_error(FakeStatusError(503))
    assert not _is_transient_api_error(APIStatusError(401))


def test_call_claude_retries_transient_failures(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = {"count": 0}
    sleeps: list[int] = []

    def create(**_: object):
        calls["count"] += 1
        if calls["count"] == 1:
            raise FakeStatusError(503)
        return _response("RESULT=7")

    monkeypatch.setattr("orchestratebench.real_run.time.sleep", sleeps.append)
    client = SimpleNamespace(messages=SimpleNamespace(create=create))

    value, _ = _call_claude(client, "prompt", max_retries=3)

    assert value == 7
    assert calls["count"] == 2
    assert sleeps == [1]


def test_call_claude_does_not_retry_non_transient_status_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = {"count": 0}
    sleeps: list[int] = []

    def create(**_: object):
        calls["count"] += 1
        raise APIStatusError(401)

    monkeypatch.setattr("orchestratebench.real_run.time.sleep", sleeps.append)
    client = SimpleNamespace(messages=SimpleNamespace(create=create))

    with pytest.raises(APIStatusError):
        _call_claude(client, "prompt", max_retries=3)

    assert calls["count"] == 1
    assert sleeps == []


def test_call_claude_retries_connection_errors_without_status(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = {"count": 0}
    sleeps: list[int] = []

    def create(**_: object):
        calls["count"] += 1
        if calls["count"] == 1:
            raise APIConnectionError("temporary disconnect")
        return _response("RESULT=11")

    monkeypatch.setattr("orchestratebench.real_run.time.sleep", sleeps.append)
    client = SimpleNamespace(messages=SimpleNamespace(create=create))

    value, _ = _call_claude(client, "prompt", max_retries=3)

    assert value == 11
    assert calls["count"] == 2
    assert sleeps == [1]
