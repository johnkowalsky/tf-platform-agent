"""Deterministic reviewer findings from module source (not LLM-only)."""

from __future__ import annotations

import json
import re
from pathlib import Path

_FTPS_ALL = re.compile(r'ftps_state\s*=\s*"AllAllowed"')
_DEFAULT_TRUE = re.compile(r"default\s*=\s*true")


def collect_findings(repo_root: Path, modules: list[str]) -> list[str]:
    findings: list[str] = []
    for name in modules:
        main_tf = repo_root / "modules" / name / "main.tf"
        if not main_tf.is_file():
            continue
        text = main_tf.read_text(encoding="utf-8")
        vars_path = repo_root / "modules" / name / "variables.tf"
        vars_text = vars_path.read_text(encoding="utf-8") if vars_path.is_file() else ""

        if name == "function-app":
            if _FTPS_ALL.search(text):
                findings.append(
                    "function-app: site_config.ftps_state is AllAllowed while https_only is true; "
                    "reviewers should confirm whether FTPS should be Disabled."
                )
            if "public_network_access_enabled" in text and _DEFAULT_TRUE.search(vars_text):
                findings.append(
                    "function-app: public_network_access_enabled defaults to true; "
                    "storage and key-vault default to deny — call out the inconsistency."
                )
            if 'role_definition_name = "Storage Blob Data Owner"' in text:
                findings.append(
                    "function-app: runtime storage role is Storage Blob Data Owner; "
                    "confirm least privilege is acceptable for this workload."
                )
        if name == "data-factory":
            if "public_network_enabled" in text and _DEFAULT_TRUE.search(vars_text):
                findings.append(
                    "data-factory: public_network_enabled defaults to true."
                )
            if 'category = "PipelineRuns"' in text and 'category = "ActivityRuns"' in text:
                findings.append(
                    "data-factory: diagnostic logs enable PipelineRuns and ActivityRuns only; "
                    "confirm that coverage is enough."
                )
        if name == "databricks-workspace":
            if "public_network_access_enabled" in vars_text and _DEFAULT_TRUE.search(
                vars_text
            ):
                findings.append(
                    "databricks-workspace: public_network_access_enabled defaults to true."
                )
    seen: set[str] = set()
    ordered: list[str] = []
    for item in findings:
        if item not in seen:
            seen.add(item)
            ordered.append(item)
    return ordered


def baseline_checkov_notes(repo_root: Path, modules: list[str]) -> list[str]:
    """Surface known Checkov IDs from the committed baseline for touched modules."""
    baseline_path = repo_root / ".checkov.baseline"
    if not baseline_path.is_file():
        return []
    try:
        data = json.loads(baseline_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []

    notes: list[str] = []
    for entry in data.get("failed_checks") or []:
        file_path = str(entry.get("file") or "")
        for name in modules:
            if f"/{name}/" in file_path or file_path.endswith(f"/{name}/main.tf"):
                for finding in entry.get("findings") or []:
                    ids = finding.get("check_ids") or []
                    resource = finding.get("resource") or "resource"
                    if ids:
                        notes.append(
                            f"{name}: baseline still suppresses {', '.join(ids)} on {resource}"
                        )
    seen: set[str] = set()
    ordered: list[str] = []
    for note in notes:
        if note not in seen:
            seen.add(note)
            ordered.append(note)
    return ordered
