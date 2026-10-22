from sanitizer import build_comment, sanitize_comment, sanitize_log


def test_redacts_secrets_and_escapes_refs():
    body = "token: abc123 see #42 and Authorization: Basic dXNlcjpwYXNz gho_ABCDEFG123"
    cleaned = sanitize_comment(body)
    assert "[redacted]" in cleaned
    assert "`#42`" in cleaned
    assert "gho_[redacted]" in cleaned or "gho_" not in cleaned.replace("gho_[redacted]", "")


def test_sanitize_log_truncates():
    text = "x" * 5000
    out = sanitize_log(text, limit=100)
    assert len(out) <= 100
    assert "truncated" in out


def test_build_comment_includes_decision():
    comment = build_comment(
        decision="update_tests",
        skills_used=["discover-changed-modules", "author-terraform-tests"],
        modules=["function-app"],
        test_summary="- `function-app` terraform test → pass",
        findings=["note"],
        run_url="https://example.test/run/1",
        checkov_notes=["function-app: baseline still suppresses CKV_AZURE_221"],
    )
    assert "update_tests" in comment
    assert "Checkov" in comment
    assert "terraform-test-agent" in comment or "tf-platform-test-agent" in comment
