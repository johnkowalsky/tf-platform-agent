"""Commit only allowlisted test files with the bot message."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from allowlist import is_allowed_test_path
from workflow_guards import refuse_default_branch_push

BOT_MESSAGE = "test-agent: update tests"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--files", nargs="*", default=[])
    parser.add_argument("--head-branch", required=True)
    parser.add_argument("--default-branch", required=True)
    args = parser.parse_args(argv)

    if refuse_default_branch_push(args.head_branch, args.default_branch):
        print("refusing to push to the default branch", file=sys.stderr)
        return 2

    allowed = [f for f in args.files if is_allowed_test_path(f)]
    if not allowed:
        print("no allowed test files to commit")
        return 0

    repo = args.repo
    subprocess.run(["git", "config", "user.name", "tf-platform-test-agent"], cwd=repo, check=True)
    subprocess.run(
        ["git", "config", "user.email", "tf-platform-test-agent@users.noreply.github.com"],
        cwd=repo,
        check=True,
    )
    subprocess.run(["git", "add", "--"] + allowed, cwd=repo, check=True)
    status = subprocess.run(
        ["git", "diff", "--cached", "--quiet"], cwd=repo, check=False
    )
    if status.returncode == 0:
        print("nothing to commit")
        return 0
    subprocess.run(["git", "commit", "-m", BOT_MESSAGE], cwd=repo, check=True)
    # Push with GITHUB_TOKEN is configured by the workflow remote URL.
    subprocess.run(
        ["git", "push", "origin", f"HEAD:refs/heads/{args.head_branch}"],
        cwd=repo,
        check=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
