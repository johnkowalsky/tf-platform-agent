"""Discover changed Terraform modules from a file list."""

from __future__ import annotations

import re
from dataclasses import dataclass

from allowlist import is_allowed_test_path

_MODULE_TF = re.compile(r"^modules/([^/]+)/.+\.tf$")
_MODULE_TEST = re.compile(r"^modules/([^/]+)/tests/")
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
    relevant: list[str] = []

    for raw in changed_files:
        path = raw.replace("\\", "/").lstrip("./")
        if path.endswith((".md", ".txt")) or path.startswith(".github/"):
            continue
        relevant.append(path)
        tf_match = _MODULE_TF.match(path)
        test_match = _MODULE_TEST.match(path)
        if tf_match:
            modules.add(tf_match.group(1))
            has_non_docs = True
            continue
        if test_match:
            modules.add(test_match.group(1))
            has_non_docs = True
            continue
        if path.startswith("stacks/"):
            stack_changed = True
            has_non_docs = True
            continue
        has_non_docs = True

    bot_message = latest_commit_message.strip().startswith(BOT_COMMIT_PREFIX)
    # verify_only only when the tip is a bot commit and every relevant path is an
    # allowlisted test file (a human who also edits main.tf must not skip authoring).
    verify_only = bool(
        bot_message
        and relevant
        and all(is_allowed_test_path(p) for p in relevant)
    )

    docs_only = not has_non_docs and not modules and not stack_changed
    return DiscoverResult(
        modules=sorted(modules),
        stack_changed=stack_changed,
        docs_only=docs_only or (not modules and not stack_changed),
        verify_only=verify_only,
    )
