"""Guards for workflow_run payloads (unit-tested; used by the Actions job)."""

from __future__ import annotations


def should_run_agent(
    *,
    head_repository: str,
    repository: str,
    pull_requests: list,
) -> bool:
    if head_repository != repository:
        return False
    if not pull_requests:
        return False
    return True


def refuse_default_branch_push(head_branch: str, default_branch: str) -> bool:
    """Return True when a push must be refused."""
    return head_branch == default_branch
