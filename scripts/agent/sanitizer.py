"""Sanitize PR comments before posting."""

from __future__ import annotations

import re

MAX_COMMENT_CHARS = 12_000
MARKER = "<!-- tf-platform-test-agent -->"

_SECRETISH = re.compile(
    r"(?i)(api[_-]?key|token|secret|password|bearer)\s*[:=]\s*\S+"
)
_GITHUB_REF = re.compile(r"(?<![`])(#\d+|[\w.-]+/[\w.-]+#\d+)(?![`])")


def sanitize_comment(body: str) -> str:
    text = body.strip()
    text = _SECRETISH.sub(r"\1=[redacted]", text)
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
    ]
    if findings:
        lines.extend(["### Findings for reviewers", ""])
        for finding in findings:
            lines.append(f"- {finding}")
        lines.append("")
    else:
        lines.extend(["### Findings for reviewers", "", "_none_", ""])
    lines.extend(
        [
            "Infrastructure changes stay with people. This agent only updates",
            "`modules/*/tests/**` when appropriate.",
            "",
            f"[Workflow run]({run_url})" if run_url else "_no run url_",
        ]
    )
    return sanitize_comment("\n".join(lines))
