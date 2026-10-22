"""Runner integration with a fake chat — no network, no real terraform on bad paths."""

from __future__ import annotations

import json
from pathlib import Path

from runner import run_agent


def test_cross_module_path_rejected_no_write(tmp_path: Path):
    # Minimal module tree
    module = tmp_path / "modules" / "function-app"
    module.mkdir(parents=True)
    (module / "main.tf").write_text('resource "null_resource" "x" {}\n', encoding="utf-8")
    (tmp_path / ".github" / "skills" / "discover-changed-modules").mkdir(parents=True)
    (tmp_path / ".github" / "skills" / "author-terraform-tests").mkdir(parents=True)
    (tmp_path / ".github" / "skills" / "verify-terraform-tests").mkdir(parents=True)
    (tmp_path / ".github" / "skills" / "report-pr-findings").mkdir(parents=True)
    for name in (
        "discover-changed-modules",
        "author-terraform-tests",
        "verify-terraform-tests",
        "report-pr-findings",
    ):
        (tmp_path / ".github" / "skills" / name / "SKILL.md").write_text("# skill\n", encoding="utf-8")
    (tmp_path / ".github" / "agents").mkdir(parents=True)
    (tmp_path / ".github" / "agents" / "terraform-test-agent.md").write_text("# agent\n", encoding="utf-8")

    bad = {
        "decision": "update_tests",
        "modules": [
            {
                "name": "function-app",
                "action": "update_tests",
                "path": "modules/network/tests/main.tftest.hcl",
                "content": 'mock_provider "azurerm" {}\nrun "x" { command = plan }\n',
            }
        ],
        "findings": [],
        "summary": "inject",
        "skills_used": ["author-terraform-tests"],
    }

    def fake_chat(*, system: str, user: str) -> str:
        return json.dumps(bad)

    result = run_agent(
        repo=tmp_path,
        trusted_root=tmp_path,
        changed_files=["modules/function-app/main.tf"],
        diff_excerpt="diff",
        chat=fake_chat,
        skip_llm=False,
    )
    assert result["written_files"] == []
    assert "Rejected" in (result.get("summary") or "")
    assert not (tmp_path / "modules" / "network" / "tests" / "main.tftest.hcl").exists()


def test_apply_in_hcl_rejected(tmp_path: Path):
    module = tmp_path / "modules" / "function-app"
    module.mkdir(parents=True)
    (module / "main.tf").write_text("# empty\n", encoding="utf-8")
    for name in (
        "discover-changed-modules",
        "author-terraform-tests",
        "verify-terraform-tests",
        "report-pr-findings",
    ):
        d = tmp_path / ".github" / "skills" / name
        d.mkdir(parents=True)
        (d / "SKILL.md").write_text("# skill\n", encoding="utf-8")
    (tmp_path / ".github" / "agents").mkdir(parents=True)
    (tmp_path / ".github" / "agents" / "terraform-test-agent.md").write_text("# agent\n", encoding="utf-8")

    bad = {
        "decision": "update_tests",
        "modules": [
            {
                "name": "function-app",
                "action": "update_tests",
                "path": "modules/function-app/tests/main.tftest.hcl",
                "content": 'mock_provider "azurerm" {}\nrun "x" { command = apply }\n',
            }
        ],
        "findings": [],
        "summary": "apply",
        "skills_used": ["author-terraform-tests"],
    }

    result = run_agent(
        repo=tmp_path,
        trusted_root=tmp_path,
        changed_files=["modules/function-app/main.tf"],
        chat=lambda **_: json.dumps(bad),
        skip_llm=False,
    )
    assert result["written_files"] == []
    assert not (module / "tests" / "main.tftest.hcl").exists()


def _skill_tree(tmp_path: Path) -> Path:
    module = tmp_path / "modules" / "function-app"
    module.mkdir(parents=True)
    (module / "main.tf").write_text("# module\n", encoding="utf-8")
    for name in (
        "discover-changed-modules",
        "author-terraform-tests",
        "verify-terraform-tests",
        "report-pr-findings",
    ):
        d = tmp_path / ".github" / "skills" / name
        d.mkdir(parents=True)
        (d / "SKILL.md").write_text("# skill\n", encoding="utf-8")
    (tmp_path / ".github" / "agents").mkdir(parents=True)
    (tmp_path / ".github" / "agents" / "terraform-test-agent.md").write_text(
        "# agent\n", encoding="utf-8"
    )
    return module


def test_retry_restores_then_keeps_second_draft(tmp_path: Path, monkeypatch):
    """First draft fails verify; second draft passes; only the second content remains."""
    import runner as runner_mod

    module = _skill_tree(tmp_path)
    original = 'mock_provider "azurerm" {}\n# original\n'
    (module / "tests").mkdir()
    (module / "tests" / "main.tftest.hcl").write_text(original, encoding="utf-8")

    drafts = [
        {
            "decision": "update_tests",
            "modules": [
                {
                    "name": "function-app",
                    "action": "update_tests",
                    "path": "modules/function-app/tests/main.tftest.hcl",
                    "content": 'mock_provider "azurerm" {}\n# first-bad\nrun "x" { command = plan }\n',
                }
            ],
            "findings": [],
            "summary": "first",
            "skills_used": ["author-terraform-tests"],
        },
        {
            "decision": "update_tests",
            "modules": [
                {
                    "name": "function-app",
                    "action": "update_tests",
                    "path": "modules/function-app/tests/main.tftest.hcl",
                    "content": 'mock_provider "azurerm" {}\n# second-good\nrun "x" { command = plan }\n',
                }
            ],
            "findings": [],
            "summary": "second",
            "skills_used": ["author-terraform-tests"],
        },
    ]
    calls = {"n": 0}

    def fake_chat(*, system: str, user: str) -> str:
        idx = min(calls["n"], len(drafts) - 1)
        calls["n"] += 1
        return json.dumps(drafts[idx])

    verify_calls = {"n": 0}

    def fake_verify(repo, *, modules, stack_changed, junit_dir=None):
        verify_calls["n"] += 1
        if verify_calls["n"] == 1:
            return False, "- `function-app` terraform test → FAIL\n", ["verify-terraform-tests"]
        return True, "- `function-app` terraform test → pass\n", ["verify-terraform-tests"]

    monkeypatch.setattr(runner_mod, "skill_verify", fake_verify)

    result = run_agent(
        repo=tmp_path,
        trusted_root=tmp_path,
        changed_files=["modules/function-app/main.tf"],
        chat=fake_chat,
        skip_llm=False,
        max_retries=2,
    )
    assert result["decision"] == "update_tests"
    assert result["written_files"] == ["modules/function-app/tests/main.tftest.hcl"]
    text = (module / "tests" / "main.tftest.hcl").read_text(encoding="utf-8")
    assert "second-good" in text
    assert "first-bad" not in text
    assert calls["n"] >= 2
