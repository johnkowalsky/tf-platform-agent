"""Run allowlisted Terraform commands without Azure credentials."""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

from allowlist import is_allowed_command
from sanitizer import sanitize_log

AZURE_ENV_KEYS = (
    "ARM_CLIENT_ID",
    "ARM_CLIENT_SECRET",
    "ARM_SUBSCRIPTION_ID",
    "ARM_TENANT_ID",
    "ARM_ACCESS_KEY",
)


@dataclass
class CommandResult:
    argv: list[str]
    cwd: str
    returncode: int
    stdout: str
    stderr: str

    @property
    def ok(self) -> bool:
        return self.returncode == 0

    @property
    def sanitized_failure(self) -> str:
        return sanitize_log((self.stderr or self.stdout)[-4000:])


def scrubbed_env(base: dict[str, str] | None = None) -> dict[str, str]:
    env = dict(base if base is not None else os.environ)
    for key in AZURE_ENV_KEYS:
        env.pop(key, None)
    env.pop("LLM_API_KEY", None)
    env.pop("OPENAI_API_KEY", None)
    env.pop("GITHUB_TOKEN", None)
    env.pop("GH_TOKEN", None)
    return env


def run_terraform(argv: list[str], *, cwd: Path) -> CommandResult:
    if not is_allowed_command(argv):
        raise ValueError(f"command not allowlisted: {argv}")
    completed = subprocess.run(
        argv,
        cwd=str(cwd),
        env=scrubbed_env(),
        capture_output=True,
        text=True,
        check=False,
    )
    return CommandResult(
        argv=argv,
        cwd=str(cwd),
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )


def test_module(module_dir: Path, *, junit_path: Path | None = None) -> list[CommandResult]:
    results = [run_terraform(["terraform", "init", "-backend=false"], cwd=module_dir)]
    if not results[-1].ok:
        return results
    test_argv = ["terraform", "test"]
    if junit_path is not None:
        test_argv.append(f"-junit-xml={junit_path}")
    results.append(run_terraform(test_argv, cwd=module_dir))
    return results


def validate_stack(stack_dir: Path) -> list[CommandResult]:
    results = [run_terraform(["terraform", "init", "-backend=false"], cwd=stack_dir)]
    if not results[-1].ok:
        return results
    results.append(run_terraform(["terraform", "fmt", "-check"], cwd=stack_dir))
    if not results[-1].ok:
        return results
    results.append(run_terraform(["terraform", "validate"], cwd=stack_dir))
    return results
