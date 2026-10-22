from discover import discover_changed_modules


def test_discovers_modules():
    result = discover_changed_modules(
        [
            "modules/function-app/main.tf",
            "modules/network/tests/main.tftest.hcl",
            "README.md",
        ]
    )
    assert result.modules == ["function-app", "network"]
    assert not result.verify_only


def test_bot_commit_is_verify_only():
    result = discover_changed_modules(
        ["modules/function-app/tests/main.tftest.hcl"],
        latest_commit_message="test-agent: update tests",
    )
    assert result.verify_only


def test_stack_only():
    result = discover_changed_modules(["stacks/data-platform/main.tf"])
    assert result.modules == []
    assert result.stack_changed
