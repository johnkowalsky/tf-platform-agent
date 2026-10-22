# Skill: author-terraform-tests

## Purpose

Draft or update mocked Terraform tests for modules the discover skill selected.

## Steps

1. Load only files under `modules/<name>/` from the pull request head.
2. Prefer `command = plan` with `mock_provider "azurerm" {}` (this repo's working
   style). Use `expect_failures` for variable validation cases.
3. When `tests/` is missing, create `tests/main.tftest.hcl`.
4. When tests exist but assertions are stale relative to the diff, update only
   those assertions.
5. Return JSON: decision, module, file path under `modules/<name>/tests/`, and
   full HCL content. Do not return shell commands.

## Constraints

- Keep `mock_provider "azurerm"`.
- No `backend` blocks, no provider credentials, no Azure resources.
- Size-cap each file (runner enforces).
