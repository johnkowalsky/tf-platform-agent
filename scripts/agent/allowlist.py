"""Path and command allowlists for the Terraform test agent."""

from __future__ import annotations

import re
from pathlib import PurePosixPath

MAX_TEST_FILE_BYTES = 64_000

_TEST_PATH = re.compile(r"^modules/([^/]+)/tests/.+\.tftest\.hcl$")
_FORBIDDEN_SUBSTRINGS = (
    "backend \"",
    "backend{",
    "ARM_CLIENT",
    "client_secret",
    "client_id",
    "subscription_id",
)
_FORBIDDEN_HCL = (
    re.compile(r"\bcommand\s*=\s*apply\b"),
    re.compile(r"\bprovisioner\s+\""),
    re.compile(r'\bdata\s+"external"'),
    re.compile(r"\blocal-exec\b"),
    re.compile(r"\bremote-exec\b"),
)


def is_allowed_test_path(path: str, *, module: str | None = None) -> bool:
    normalized = path.replace("\\", "/").lstrip("./")
    if ".." in PurePosixPath(normalized).parts:
        return False
    match = _TEST_PATH.match(normalized)
    if not match:
        return False
    if module is not None and match.group(1) != module:
        return False
    return True


def validate_test_hcl(content: str) -> list[str]:
    errors: list[str] = []
    if len(content.encode("utf-8")) > MAX_TEST_FILE_BYTES:
        errors.append(f"file exceeds {MAX_TEST_FILE_BYTES} bytes")
    if 'mock_provider "azurerm"' not in content:
        errors.append('missing mock_provider "azurerm"')
    lowered = content.lower()
    for needle in _FORBIDDEN_SUBSTRINGS:
        if needle.lower() in lowered:
            errors.append(f"forbidden content: {needle}")
    if re.search(r"(?m)^\s*terraform\s*\{[^}]*backend\s", content, re.S):
        errors.append("backend block is not allowed in tests")
    for pattern in _FORBIDDEN_HCL:
        if pattern.search(content):
            errors.append(f"forbidden HCL pattern: {pattern.pattern}")
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
    if len(argv) >= 2 and argv[1] == "apply":
        return False
    if argv[1:3] == ["init", "-backend=false"]:
        return True
    if argv[1:3] == ["fmt", "-check"]:
        return True
    if argv[1:2] == ["validate"]:
        return True
    if argv[1:2] == ["test"]:
        return all(
            part == "test" or part.startswith("-junit-xml=") or part == "-json"
            for part in argv[1:]
        )
    return False
