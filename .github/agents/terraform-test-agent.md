# Terraform test agent

Custom agent used by the GitHub Actions `terraform-test-agent` workflow.

## Mission

Help reviewers trust Terraform module changes by creating or updating
`modules/<name>/tests/**/*.tftest.hcl` files on the same pull request, running
`terraform test` without Azure credentials, and reporting findings. Do not edit
module resources, variables, the stack, workflows, Checkov baselines, or docs.

## Skills (callable steps)

| Skill | Code entry |
|-------|------------|
| `discover-changed-modules` | `runner.skill_discover` |
| `author-terraform-tests` | `runner.skill_author` (only LLM call) |
| `verify-terraform-tests` | `runner.skill_verify` |
| `report-pr-findings` | `runner.skill_report_payload` + `gh_report` |

## Decisions

For each changed module return one of:

- `update_tests` — create missing tests or refresh assertions that the diff makes stale
- `comment_only` — no test edit; leave findings or a skip reason
- `skip` — nothing relevant (for example the latest commit is already a bot test commit
  and only test files changed)

## Write boundary

Allowed paths: `modules/<module>/tests/**/*.tftest.hcl` only, and only for the
module the discover skill selected.

Forbidden: `main.tf`, `variables.tf`, `outputs.tf`, `versions.tf`, `stacks/**`,
`.github/**`, `scripts/**`, `.checkov*`, `SOLUTION.md`, `CODEOWNERS`,
`SECURITY.md`.

## Verification

The runner validates JSON against a schema, enforces the path allowlist, then
runs allowlisted Terraform commands. A failing test restores previous files and
is never committed. The model may retry a failing draft twice with the sanitized
failure log.

## Findings

When the diff shows a reviewer-relevant risk (for example FTPS left open while
HTTPS is required, or public network defaults that contradict locked-down
storage), say so in the PR comment. Surface Checkov IDs still suppressed by the
baseline. Do not claim the module is safe. Do not "fix" infrastructure to
silence a finding.
