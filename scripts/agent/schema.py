"""Validate model decisions before any write."""

from __future__ import annotations

from typing import Any

from allowlist import is_allowed_test_path, validate_test_hcl

VALID_DECISIONS = frozenset({"skip", "update_tests", "comment_only"})


def validate_decision(payload: Any) -> tuple[dict[str, Any] | None, list[str]]:
    errors: list[str] = []
    if not isinstance(payload, dict):
        return None, ["decision must be a JSON object"]

    decision = payload.get("decision")
    if decision not in VALID_DECISIONS:
        errors.append(f"decision must be one of {sorted(VALID_DECISIONS)}")

    modules = payload.get("modules", [])
    if modules is None:
        modules = []
    if not isinstance(modules, list):
        errors.append("modules must be a list")
        modules = []

    normalized_modules: list[dict[str, Any]] = []
    for index, item in enumerate(modules):
        if not isinstance(item, dict):
            errors.append(f"modules[{index}] must be an object")
            continue
        name = item.get("name")
        if not isinstance(name, str) or not name or "/" in name or ".." in name:
            errors.append(f"modules[{index}].name is invalid")
            continue
        entry: dict[str, Any] = {"name": name, "action": item.get("action", decision)}
        if entry["action"] == "update_tests":
            path = item.get("path")
            content = item.get("content")
            if not isinstance(path, str) or not is_allowed_test_path(path):
                errors.append(f"modules[{index}].path is not an allowed test path")
            else:
                entry["path"] = path.replace("\\", "/").lstrip("./")
            if not isinstance(content, str) or not content.strip():
                errors.append(f"modules[{index}].content must be non-empty HCL")
            else:
                hcl_errors = validate_test_hcl(content)
                errors.extend(f"modules[{index}]: {err}" for err in hcl_errors)
                entry["content"] = content
        normalized_modules.append(entry)

    findings = payload.get("findings", [])
    if findings is None:
        findings = []
    if not isinstance(findings, list):
        errors.append("findings must be a list")
        findings = []
    clean_findings: list[str] = []
    for finding in findings:
        if isinstance(finding, str) and finding.strip():
            clean_findings.append(finding.strip())

    summary = payload.get("summary", "")
    if summary is None:
        summary = ""
    if not isinstance(summary, str):
        errors.append("summary must be a string")
        summary = ""

    if errors:
        return None, errors

    return {
        "decision": decision,
        "modules": normalized_modules,
        "findings": clean_findings,
        "summary": summary.strip(),
        "skills_used": list(payload.get("skills_used") or []),
    }, []
