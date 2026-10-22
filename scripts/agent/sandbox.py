"""Clean-room copy of a module tree for terraform test (no .git)."""

from __future__ import annotations

import shutil
from pathlib import Path


def sandbox_module_copy(repo: Path, module: str, *, sandbox_root: Path) -> Path:
    """
    Copy modules/<module> into sandbox_root/<module> for verification.

    The copy excludes .git and .terraform so plan/test does not inherit
    credentials from a checkout or a previous init.
    """
    src = repo / "modules" / module
    if not src.is_dir():
        raise FileNotFoundError(f"module not found: {src}")
    dest = sandbox_root / module
    if dest.exists():
        shutil.rmtree(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)

    def _ignore(directory: str, names: list[str]) -> set[str]:
        ignored = {".git", ".terraform", ".terraform.lock.hcl.bak"}
        return {n for n in names if n in ignored}

    shutil.copytree(src, dest, ignore=_ignore)
    # Ensure no nested .git slipped through
    for git_dir in dest.rglob(".git"):
        if git_dir.is_dir():
            shutil.rmtree(git_dir)
        elif git_dir.is_file():
            git_dir.unlink()
    return dest


def is_sandbox_path(path: Path, sandbox_root: Path) -> bool:
    try:
        path.resolve().relative_to(sandbox_root.resolve())
        return True
    except ValueError:
        return False
