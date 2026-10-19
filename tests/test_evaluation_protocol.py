"""Pre-registration cannot silently bless infrastructure failures or extra runs."""

import httpx
import pytest

from core.clock import FakeClock
from core.llm import ProviderUnavailableError, RealProviderAdapter
from scripts.evaluation_support import PacedProvider
from scripts.postfix_protocol import authorize_run, validity


def test_more_than_ten_percent_infrastructure_invalidates_run():
    assert validity(10, 100)["valid_run"]
    assert not validity(11, 100)["valid_run"]


def test_only_one_invalid_run_rerun_with_identical_hash():
    authorize_run(2, "same", {"config_hash": "same", "infrastructure_failure_rate": .11})
    for number, digest, previous in [(3, "same", {"config_hash": "same", "infrastructure_failure_rate": 1}),
                                     (2, "different", {"config_hash": "same", "infrastructure_failure_rate": 1}),
                                     (2, "same", {"config_hash": "same", "infrastructure_failure_rate": .1})]:
        with pytest.raises(ValueError):
            authorize_run(number, digest, previous)


def test_evaluation_waits_for_cooldown_before_starting_next_request_deadline(monkeypatch):
    clock = FakeClock()
    pacer = PacedProvider()
    pacer.clock = clock
    pacer.delegate = RealProviderAdapter("synthetic", "gemini-2.5-flash", [], clock)
    start = clock.monotonic()
    calls = []
    def post(*args, **kwargs):
        calls.append(clock.monotonic())
        if len(calls) == 1:
            return httpx.Response(429, headers={"retry-after": "60"})
        return httpx.Response(200, json={"candidates": [{"content": {"parts": [{"text": "valid response"}]}}]})
    monkeypatch.setattr(httpx, "post", post)
    with pytest.raises(ProviderUnavailableError):
        pacer.generate("synthetic request")
    assert pacer.generate("next synthetic request").content == "valid response"
    assert calls == [start, start + 60]
