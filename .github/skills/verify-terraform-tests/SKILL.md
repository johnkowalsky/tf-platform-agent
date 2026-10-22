# Skill: verify-terraform-tests

## Purpose

Prove generated or existing tests work without cloud credentials.

## Implementation

Executed by `runner.skill_verify` / `terraform_cmds.test_module` and
`validate_stack`.

## Steps

1. Unset `ARM_CLIENT_ID`, `ARM_CLIENT_SECRET`, `ARM_SUBSCRIPTION_ID`,
   `ARM_TENANT_ID`, `ARM_ACCESS_KEY`, `LLM_API_KEY`, and `GITHUB_TOKEN`.
2. Copy each touched module into `agent-output/sandbox/<name>/` (no `.git`,
   no prior `.terraform`) and run only:
   - `terraform init -backend=false`
   - `terraform test` (optionally with absolute `-junit-xml=…` under
     `agent-output/`)
3. For stack-only changes run `terraform init -backend=false`, then
   `terraform fmt -check`, then `terraform validate` under
   `stacks/data-platform`.
4. Never run `terraform apply` as a shell command. Never pass the LLM API key
   into this step. Sanitize failure logs before they reach the PR comment.

## Output

Pass/fail plus sanitized logs. A failing result restores previous test files and
blocks any commit.
