"""Post PR comment and check run from agent output."""

from __future__ import annotations

import argparse
import json
import os
import urllib.error
import urllib.request
from pathlib import Path

from sanitizer import MARKER, sanitize_comment


def _api(method: str, url: str, payload: dict | None = None) -> dict:
    token = os.environ["GITHUB_TOKEN"]
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            body = response.read().decode("utf-8")
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GitHub API {exc.code}: {detail}") from exc


def upsert_comment(repo: str, pr_number: int, body: str) -> None:
    body = sanitize_comment(body)
    comments = _api(
        "GET",
        f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments?per_page=100",
    )
    existing_id = None
    for comment in comments if isinstance(comments, list) else []:
        if MARKER in (comment.get("body") or ""):
            existing_id = comment["id"]
            break
    if existing_id:
        _api(
            "PATCH",
            f"https://api.github.com/repos/{repo}/issues/comments/{existing_id}",
            {"body": body},
        )
    else:
        _api(
            "POST",
            f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments",
            {"body": body},
        )


def create_check_run(
    repo: str,
    *,
    head_sha: str,
    name: str,
    conclusion: str,
    summary: str,
    details_url: str = "",
) -> None:
    payload = {
        "name": name,
        "head_sha": head_sha,
        "status": "completed",
        "conclusion": conclusion,
        "output": {
            "title": name,
            "summary": summary[:65000],
        },
    }
    if details_url:
        payload["details_url"] = details_url
    _api("POST", f"https://api.github.com/repos/{repo}/check-runs", payload)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True, help="owner/name")
    parser.add_argument("--pr", type=int, required=True)
    parser.add_argument("--sha", required=True)
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--run-url", default="")
    args = parser.parse_args(argv)

    result = json.loads(args.result.read_text(encoding="utf-8"))
    comment = result.get("comment") or ""
    upsert_comment(args.repo, args.pr, comment)

    decision = result.get("decision")
    test_ok = "FAIL" not in (result.get("test_summary") or "")
    if decision == "update_tests" and result.get("written_files") and test_ok:
        conclusion = "success"
    elif test_ok:
        conclusion = "success"
    else:
        conclusion = "failure"

    create_check_run(
        args.repo,
        head_sha=args.sha,
        name="terraform-test-agent",
        conclusion=conclusion,
        summary=result.get("test_summary") or result.get("summary") or decision,
        details_url=args.run_url,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
