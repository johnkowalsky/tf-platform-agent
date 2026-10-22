# Skill: verify-terraform-tests

## Purpose

Prove generated or existing tests work without cloud credentials.

## Steps

1. Unset `ARM_CLIENT_ID`, `ARM_CLIENT_SECRET`, `ARM_SUBSCRIPTION_ID`,
   `ARM_TENANT_ID`, and `ARM_ACCESS_KEY`.
2. In each touched module directory run only:
   - `terraform init -backend=false`
   - `terraform test` (optionally with `-junit-xml=…`)
3. For stack-only changes run `terraform fmt -check` and
   `terraform validate` under `stacks/data-platform` after
   `terraform init -backend=false`.
4. Never run `terraform apply` as a shell command. Never pass the LLM API key
   into this step.

## Output

Pass/fail plus captured logs. A failing result blocks any commit.
