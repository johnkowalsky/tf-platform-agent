# Skill: discover-changed-modules

## Purpose

Map a pull request diff to Terraform modules that may need test updates.

## Implementation

Executed by `discover.discover_changed_modules` / `runner.skill_discover`.

## Steps

1. Read the list of changed files for the pull request (base…head).
2. Collect unique module names under `modules/<name>/` when any `.tf` file or
   any file under `tests/` changed.
3. Mark stack-only (`stacks/**`) or docs-only changes as non-module.
4. Set `verify_only` only when the latest commit message starts with
   `test-agent: update tests` **and** every non-docs path is an allowlisted
   `modules/<name>/tests/**/*.tftest.hcl` file.

## Output

Return a structured list of module names plus a `verify_only` flag. Never invent
module names outside `modules/`.
