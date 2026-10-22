"""Sanitize PR comments and command logs before posting."""

from __future__ import annotations

import re

MAX_COMMENT_CHARS = 12_000
MAX_LOG_CHARS = 1_500
MARKER = "<!-- tf-platform-test-agent -->"

_SECRETISH = re.compile(
    r"(?i)(api[_-]?key|token|secret|password|bearer|authorization)\s*[:=]\s*\S+"
)
_GITHUB_TOKEN = re.compile(r"(?i)\b(gho_|ghu_|ghs_|ghr_|github_pat_)[A-Za-z0-9_]+")
_BASIC_AUTH = re.compile(r"(?i)authorization:\s*basic\s+[A-Za-z0-9+/=]+")
_GITHUB_REF = re.compile(r"(?<![`])(#\d+|[\w.-]+/[\w.-]+#\d+)(?![`])")


def sanitize_log(text: str, *, limit: int = MAX_LOG_CHARS) -> str:
    cleaned = text or ""
    cleaned = _BASIC_AUTH.sub("Authorization: Basic [redacted]", cleaned)
    cleaned = _SECRETISH.sub(r"\1=[redacted]", cleaned)
    cleaned = _GITHUB_TOKEN.sub(r"\1[redacted]", cleaned)
    if len(cleaned) > limit:
        cleaned = cleaned[: limit - 20] + "\n…[truncated]"
    return cleaned


def sanitize_comment(body: str) -> str:
    text = body.strip()
    text = _BASIC_AUTH.sub("Authorization: Basic [redacted]", text)
    text = _SECRETISH.sub(r"\1=[redacted]", text)
    text = _GITHUB_TOKEN.sub(r"\1[redacted]", text)
    text = _GITHUB_REF.sub(lambda m: f"`{m.group(1)}`", text)
    if len(text) > MAX_COMMENT_CHARS:
        text = text[: MAX_COMMENT_CHARS - 20] + "\n\n…[truncated]"
    if MARKER not in text:
        text = f"{MARKER}\n{text}"
    return text


def build_comment(
    *,
    decision: str,
    skills_used: list[str],
    modules: list[str],
    test_summary: str,
    findings: list[str],
    run_url: str,
    checkov_notes: list[str] | None = None,
    junit_artifact: str = "agent-terraform-junit",
) -> str:
    lines = [
        MARKER,
        "## Terraform test agent",
        "",
        f"**Decision:** `{decision}`",
        f"**Skills:** {', '.join(f'`{s}`' for s in skills_used) or '_none_'}",
        f"**Modules:** {', '.join(f'`{m}`' for m in modules) or '_none_'}",
        "",
        "### Test results",
        "",
        test_summary or "_no tests run_",
        "",
        f"JUnit artifact (workflow): `{junit_artifact}`",
        "",
    ]
    if findings:
        lines.extend(["### Findings for reviewers", ""])
        for finding in findings:
            lines.append(f"- {finding}")
        lines.append("")
    else:
        lines.extend(["### Findings for reviewers", "", "_none_", ""])
    if checkov_notes:
        lines.extend(["### Checkov (baseline deltas)", ""])
        for note in checkov_notes:
            lines.append(f"- {note}")
        lines.append("")
    lines.extend(
        [
            "Infrastructure changes stay with people. This agent only updates",
            "`modules/*/tests/**` when appropriate.",
            "",
            "Note: a `GITHUB_TOKEN` test commit does not re-run `terraform-ci`;",
            "this check run is the status on the bot commit.",
            "",
            f"[Workflow run]({run_url})" if run_url else "_no run url_",
        ]
    )
    return sanitize_comment("\n".join(lines))
