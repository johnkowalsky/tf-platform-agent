"""Path and command allowlists for the Terraform test agent."""

from __future__ import annotations

import re
from pathlib import PurePosixPath

MAX_TEST_FILE_BYTES = 64_000

_TEST_PATH = re.compile(r"^modules/[^/]+/tests/.+\.tftest\.hcl$")
_FORBIDDEN_SUBSTRINGS = (
    "backend \"",
    "backend{",
    "ARM_CLIENT",
    "client_secret",
    "client_id",
    "subscription_id",
)


def is_allowed_test_path(path: str) -> bool:
    normalized = path.replace("\\", "/").lstrip("./")
    if ".." in PurePosixPath(normalized).parts:
        return False
    return bool(_TEST_PATH.match(normalized))


def validate_test_hcl(content: str) -> list[str]:
    errors: list[str] = []
    if len(content.encode("utf-8")) > MAX_TEST_FILE_BYTES:
        errors.append(f"file exceeds {MAX_TEST_FILE_BYTES} bytes")
    if 'mock_provider "azurerm"' not in content and "mock_provider \"azurerm\"" not in content:
        if "mock_provider" not in content:
            errors.append('missing mock_provider "azurerm"')
    lowered = content.lower()
    for needle in _FORBIDDEN_SUBSTRINGS:
        if needle.lower() in lowered:
            errors.append(f"forbidden content: {needle}")
    if re.search(r"(?m)^\s*terraform\s*\{[^}]*backend\s", content, re.S):
        errors.append("backend block is not allowed in tests")
    return errors


ALLOWED_COMMANDS = frozenset(
    {
        "terraform init -backend=false",
        "terraform fmt -check",
        "terraform validate",
        "terraform test",
    }
)


def is_allowed_command(argv: list[str]) -> bool:
    if not argv or argv[0] != "terraform":
        return False
    if "apply" in argv and "-junit-xml" not in " ".join(argv):
        # shell terraform apply is never allowed; tftest command=apply is HCL only
        if argv[1:] == ["apply"] or (len(argv) >= 2 and argv[1] == "apply"):
            return False
    if argv[1:3] == ["init", "-backend=false"]:
        return True
    if argv[1:3] == ["fmt", "-check"]:
        return True
    if argv[1:2] == ["validate"]:
        return True
    if argv[1:2] == ["test"]:
        # allow optional -junit-xml=path
        return all(
            part == "test" or part.startswith("-junit-xml=") or part == "-json"
            for part in argv[1:]
        )
    return False
