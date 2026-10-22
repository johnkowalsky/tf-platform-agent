from pathlib import Path

from sandbox import is_sandbox_path, sandbox_module_copy


def test_sandbox_copy_excludes_git_and_is_under_root(tmp_path: Path):
    module = tmp_path / "modules" / "function-app"
    module.mkdir(parents=True)
    (module / "main.tf").write_text('resource "null_resource" "x" {}\n', encoding="utf-8")
    # Use a file named .git (not a repo) so environments that block .git dirs still work.
    (module / ".git").write_text("not-a-repo\n", encoding="utf-8")
    (module / ".terraform").mkdir()
    (module / ".terraform" / "x").write_text("y\n", encoding="utf-8")

    sandbox_root = tmp_path / "agent-output" / "sandbox"
    dest = sandbox_module_copy(tmp_path, "function-app", sandbox_root=sandbox_root)

    assert is_sandbox_path(dest, sandbox_root)
    assert not is_sandbox_path(module, sandbox_root)
    assert (dest / "main.tf").is_file()
    assert not (dest / ".git").exists()
    assert not (dest / ".terraform").exists()
