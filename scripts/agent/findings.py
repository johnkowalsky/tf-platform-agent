"""Deterministic reviewer findings from module source (not LLM-only)."""

from __future__ import annotations

from pathlib import Path


def collect_findings(repo_root: Path, modules: list[str]) -> list[str]:
    findings: list[str] = []
    for name in modules:
        main_tf = repo_root / "modules" / name / "main.tf"
        if not main_tf.is_file():
            continue
        text = main_tf.read_text(encoding="utf-8")
        if name == "function-app":
            if 'ftps_state          = "AllAllowed"' in text or 'ftps_state = "AllAllowed"' in text:
                findings.append(
                    "function-app: site_config.ftps_state is AllAllowed while https_only is true; "
                    "reviewers should confirm whether FTPS should be Disabled."
                )
            if "public_network_access_enabled" in text and "default     = true" in (
                (repo_root / "modules" / name / "variables.tf").read_text(encoding="utf-8")
            ):
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
            if "public_network_enabled" in text:
                vars_text = (repo_root / "modules" / name / "variables.tf").read_text(
                    encoding="utf-8"
                )
                if "default     = true" in vars_text:
                    findings.append(
                        "data-factory: public_network_enabled defaults to true."
                    )
            if 'category = "PipelineRuns"' in text and 'category = "ActivityRuns"' in text:
                findings.append(
                    "data-factory: diagnostic logs enable PipelineRuns and ActivityRuns only; "
                    "confirm that coverage is enough."
                )
        if name == "databricks-workspace":
            vars_text = (repo_root / "modules" / name / "variables.tf").read_text(
                encoding="utf-8"
            )
            if "public_network_access_enabled" in vars_text and "default     = true" in vars_text:
                findings.append(
                    "databricks-workspace: public_network_access_enabled defaults to true."
                )
    # stable unique order
    seen: set[str] = set()
    ordered: list[str] = []
    for item in findings:
        if item not in seen:
            seen.add(item)
            ordered.append(item)
    return ordered
