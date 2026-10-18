"""Verify that background checks cannot spend a model call before their gates."""
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

CONTROL = Path(__file__).resolve().parents[1] / "payload/usr/libexec/codex-cachyos"
sys.path.insert(0, str(CONTROL))
import maintenance


@pytest.fixture
def isolated(monkeypatch, tmp_path):
    monkeypatch.setattr(maintenance, "STATE", tmp_path)
    monkeypatch.setattr(maintenance, "LOGS", tmp_path)
    monkeypatch.setattr(maintenance.time, "strftime", lambda *args: "2026-10-18")
    calls = []

    def no_model(*args, **kwargs):
        pytest.fail("A model process was started before authorization gates passed")

    monkeypatch.setattr(maintenance.subprocess, "Popen", no_model)

    def authenticate(argv, **kwargs):
        calls.append(argv)
        return SimpleNamespace(returncode=0, stdout="unchanged\n")

    monkeypatch.setattr(maintenance.subprocess, "run", authenticate)
    return tmp_path, calls


def test_missing_oauth_never_starts_model(isolated, monkeypatch):
    directory, _ = isolated
    monkeypatch.setattr(maintenance.subprocess, "run",
                        lambda *args, **kwargs: SimpleNamespace(returncode=1))
    assert maintenance.run_maintenance({}) == 0
    assert not (directory / "maintenance-state.json").exists()


@pytest.mark.parametrize("saved", [
    {"runs": 4, "consecutive_failures": 0},
    {"runs": 0, "consecutive_failures": 3},
])
def test_daily_budget_or_failure_limit_prevents_observation_and_model(isolated, saved):
    directory, calls = isolated
    saved["day"] = "2026-10-18"
    state = directory / "maintenance-state.json"
    state.write_text(json.dumps(saved))
    before = state.read_bytes()
    assert maintenance.run_maintenance({}) == 0
    assert len(calls) == 1  # Authentication status only, no inference.
    assert state.read_bytes() == before


def test_identical_observations_never_start_second_model_call(isolated):
    directory, calls = isolated
    observations = {name: {"exit_code": 0, "stdout": "unchanged\n"}
                    for name in ("kernel", "failed_units", "core_packages")}
    fingerprint = maintenance.hashlib.sha256(
        json.dumps(observations, sort_keys=True).encode()).hexdigest()
    state = directory / "maintenance-state.json"
    state.write_text(json.dumps({"day": "2026-10-18", "runs": 1,
                                "fingerprint": fingerprint}))
    before = state.read_bytes()
    assert maintenance.run_maintenance({}) == 0
    assert len(calls) == 4
    assert state.read_bytes() == before
