# Example run (FTPS stale-test scenario)

Defense record for the assignment’s example PR. This is **not** a live Actions
URL. After the repository is published, open a same-repo pull request that
matches this scenario so reviewers can see the real comment and check run.

## Human change

Edit only `modules/function-app/main.tf`:

```diff
-    ftps_state          = "AllAllowed"
+    ftps_state          = "Disabled"
```

Leave `modules/function-app/tests/main.tftest.hcl` asserting `AllAllowed` so
the suite is intentionally stale.

## Expected CI / agent sequence

1. `terraform-ci` / `static` — fmt, TFLint, validate, agent unit tests, Checkov
   pass.
2. `terraform-ci` / `module-tests` — `terraform test` fails on function-app
   (`continue-on-error: true` so the workflow still completes).
3. `terraform-test-agent` (default-branch workflow) starts for the same PR.
4. Skills:
   - `discover-changed-modules` → `function-app`
   - `author-terraform-tests` → `update_tests` on
     `modules/function-app/tests/main.tftest.hcl` (FTPS assertion → `Disabled`;
     keep `override_data` for `data.external.build_info`)
   - `verify-terraform-tests` → sandbox `terraform test` pass
   - `report-pr-findings` → upsert PR comment + check run
5. Bot commit message: `test-agent: update tests` (test files only).
6. Artifacts: workflow artifact `agent-terraform-junit` with
   `junit-function-app.xml`.

## Expected reviewer findings (deterministic)

- `public_network_access_enabled` defaults to `true` (inconsistency with
  locked-down storage / key vault).
- Checkov baseline IDs still suppressed for the module (listed in the comment;
  infrastructure is not auto-fixed).

## What this proves / does not prove

**Proves:** the agent updated plan-time mocked tests for a real module change,
verified them offline, and reported on the same PR.

**Does not prove:** a live Azure apply, Entra federation, or that FTPS
`Disabled` satisfies every org policy — people decide infrastructure.
