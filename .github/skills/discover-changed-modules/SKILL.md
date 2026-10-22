# Skill: discover-changed-modules

## Purpose

Map a pull request diff to Terraform modules that may need test updates.

## Steps

1. Read the list of changed files for the pull request (base…head).
2. Collect unique module names under `modules/<name>/` when any `.tf` or
   `tests/**/*.tftest.hcl` file changed.
3. Mark stack-only (`stacks/**`) or docs-only changes as non-module.
4. If the latest commit message is `test-agent: update tests`, mark the run as
   verify-only so the agent does not author again.

## Output

Return a structured list of module names plus a `verify_only` flag. Never invent
module names outside `modules/`.
