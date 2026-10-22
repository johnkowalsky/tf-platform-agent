"""Prompt-injection fixture: model asks to edit main.tf — runner must reject."""

from __future__ import annotations

import json
from pathlib import Path

from schema import validate_decision

EVALS = Path(__file__).resolve().parent.parent / "evals"


def test_injection_payload_rejected():
    payload = json.loads((EVALS / "injection_edit_main.json").read_text(encoding="utf-8"))
    result, errors = validate_decision(payload)
    assert result is None
    assert any("path" in e for e in errors)


def test_create_when_missing_shape_ok():
    payload = json.loads((EVALS / "create_when_missing.json").read_text(encoding="utf-8"))
    result, errors = validate_decision(payload)
    assert errors == []
    assert result["decision"] == "update_tests"


def test_update_when_stale_shape_ok():
    payload = json.loads((EVALS / "update_when_stale.json").read_text(encoding="utf-8"))
    result, errors = validate_decision(payload)
    assert errors == []


def test_empty_pull_requests_guard():
    # workflow helper: empty PR list must stop before reporting
    from workflow_guards import should_run_agent

    assert not should_run_agent(
        head_repository="other/fork",
        repository="me/tf-platform-agent",
        pull_requests=[],
    )
    assert not should_run_agent(
        head_repository="me/tf-platform-agent",
        repository="me/tf-platform-agent",
        pull_requests=[],
    )
    assert should_run_agent(
        head_repository="me/tf-platform-agent",
        repository="me/tf-platform-agent",
        pull_requests=[{"number": 1}],
    )
