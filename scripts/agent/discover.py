"""Discover changed Terraform modules from a file list."""

from __future__ import annotations

import re
from dataclasses import dataclass

_MODULE_PATH = re.compile(r"^modules/([^/]+)/")
BOT_COMMIT_PREFIX = "test-agent: update tests"


@dataclass(frozen=True)
class DiscoverResult:
    modules: list[str]
    stack_changed: bool
    docs_only: bool
    verify_only: bool
    skill: str = "discover-changed-modules"


def discover_changed_modules(
    changed_files: list[str],
    *,
    latest_commit_message: str = "",
) -> DiscoverResult:
    modules: set[str] = set()
    stack_changed = False
    has_non_docs = False
    for raw in changed_files:
        path = raw.replace("\\", "/").lstrip("./")
        match = _MODULE_PATH.match(path)
        if match:
            modules.add(match.group(1))
            has_non_docs = True
            continue
        if path.startswith("stacks/"):
            stack_changed = True
            has_non_docs = True
            continue
        if path.endswith((".md", ".txt")) or path.startswith(".github/"):
            continue
        has_non_docs = True

    verify_only = latest_commit_message.strip().startswith(BOT_COMMIT_PREFIX)
    docs_only = not has_non_docs and not modules and not stack_changed
    return DiscoverResult(
        modules=sorted(modules),
        stack_changed=stack_changed,
        docs_only=docs_only or (not modules and not stack_changed),
        verify_only=verify_only,
    )
