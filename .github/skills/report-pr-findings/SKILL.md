# Skill: report-pr-findings

## Purpose

Publish the agent's decision, skills used, test results, and reviewer findings
on the pull request that started the run.

## Implementation

Executed by `runner.skill_report_payload` and `gh_report` (upsert comment +
upsert check run).

## Steps

1. Build a structured comment from validated fields (decision, skills, modules,
   test summary, findings, Checkov baseline notes, link to the workflow run).
2. Sanitize: length cap, secret redaction (including Authorization headers and
   `gho_` / `github_pat_` tokens), escape GitHub issue/PR references that should
   not auto-link.
3. Upsert one comment marked with an HTML marker so synchronize events do not
   spam.
4. Upsert a check run on the head SHA (and on the bot commit SHA after a test
   push).

## Rules

- Findings advise people; they never edit infrastructure.
- Do not call the module "safe" or "secure".
- Do not open a second pull request.
