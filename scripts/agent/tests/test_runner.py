"""Runner integration with a fake chat — no network, no real terraform on bad paths."""

from __future__ import annotations

import json
from pathlib import Path

from runner import run_agent

REPO = Path(__file__).resolve().parents[3]


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
