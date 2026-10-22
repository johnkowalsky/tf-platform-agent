from sanitizer import MARKER, build_comment, sanitize_comment


def test_redacts_secrets_and_escapes_refs():
    text = sanitize_comment("api_key=supersecret see #12 and org/repo#99")
    assert "supersecret" not in text
    assert "`#12`" in text
    assert MARKER in text


def test_build_comment_includes_decision():
    body = build_comment(
        decision="update_tests",
        skills_used=["discover-changed-modules"],
        modules=["function-app"],
        test_summary="ok",
        findings=["ftps open"],
        run_url="https://example.test/run/1",
    )
    assert "update_tests" in body
    assert "ftps open" in body
