# Solution: Terraform test agent

A GitHub-native agent that creates or updates mocked `terraform test` files on
the same pull request, verifies them without Azure credentials, and reports
results plus reviewer findings.

## Main technical decisions (and what we gave up)

1. **Two workflows, one trust boundary.** `terraform-ci.yml` is secret-free and
   runs on `pull_request`. Its `static` job (fmt, TFLint, validate, agent unit
   tests, Checkov) is the hard gate. `module-tests` uses `continue-on-error` so
   a stale `tftest` still completes the workflow. `terraform-test-agent.yml`
   runs on `workflow_run` of that CI workflow and always uses the workflow file
   and skills from the **default branch**, so a PR cannot swap the agent or the
   secret path. When CI concludes `failure`, the agent continues only if the
   `static` job succeeded.
   *Gave up:* a single job with `contents: write` on untrusted PR code; Cursor
   Cloud / Copilot as the CI runner.

2. **Safe output on the same PR.** The assignment forbids a second pull request.
   The model returns JSON only. A deterministic checker accepts paths under
   `modules/<discovered-name>/tests/**/*.tftest.hcl` only, rejects
   `command = apply` / provisioners / `data "external"` in test HCL, and binds
   the path to the discovered module. The PR checkout has
   `persist-credentials: false`; `GITHUB_TOKEN` is applied only for the commit
   push. `terraform test` runs without `LLM_API_KEY` or `GITHUB_TOKEN`. Failed
   drafts are restored; only a passing result is committed with message
   `test-agent: update tests`.
   *Gave up:* GitHub Agentic Workflows `create-pull-request` (would open another
   PR); a PAT that re-triggers CI (would loop).

3. **Results visible on the PR.** A `workflow_run` job is not a PR check by
   itself. The agent upserts one sanitized comment and upserts a **check run**
   on the head SHA (and on the bot commit SHA after a test push). PR association
   uses `workflow_run.pull_requests` when present, otherwise the commits API.
   *Gave up:* relying on the Actions tab alone.

4. **Plan-time mocked tests.** Behavior uses `command = plan` with
   `mock_provider "azurerm"`. Mocked `command = apply` failed because azurerm
   validates resource ID formats against random mock IDs. Function-app uses
   `override_data` for `data.external.build_info` so plan does not execute
   `build-info.sh` from the PR tree.
   *Gave up:* AVM-style mocked apply and a `tests/unit/` layout rewrite.

5. **Skills are callable steps.** Each skill under `.github/skills/*/SKILL.md`
   maps to a function in `scripts/agent/runner.py`
   (`skill_discover`, `skill_author`, `skill_verify`, `skill_report_payload`).
   Only authoring calls an LLM.
   *Gave up:* treating skills as prompt-only documentation.

6. **Supply-chain gates after the agent path.** Actions are pinned to full SHAs.
   TFLint comes from a pinned release zip verified by SHA-256 and the release
   `checksums.txt`. Checkov runs via SHA-pinned `bridgecrewio/checkov-action`
   with the committed baseline. Agent pip installs use `--require-hashes`.
   Verify copies modules into `agent-output/sandbox/` (no `.git`).
   *Gave up:* egress `block` mode until a green run proves the host allowlist;
   SLSA provenance (nothing is released); auto-fixing Checkov findings in
   `main.tf`.

## How to run (prerequisites)

### Local

- Terraform ≥ 1.9 (CI pins 1.11.4 for `-junit-xml`)
- Python 3.12+
- No Azure subscription

```sh
cd modules/storage-account
terraform init -backend=false
terraform test

cd ../../scripts/agent
python -m pip install --require-hashes -r requirements.txt
PYTHONPATH=. python -m pytest -q tests/
```

### GitHub

1. Create a **public** repository named `tf-platform-agent` and push this tree
   (do not include any assignment instruction file).
2. Add repository secret `LLM_API_KEY`. Optional vars: `LLM_BASE_URL`,
   `LLM_MODEL` (OpenAI-compatible chat completions API).
3. Follow [SECURITY.md](SECURITY.md) for scanning, rulesets, and CODEOWNERS
   (replace `REPLACE_WITH_GITHUB_LOGIN`).
4. Open a pull request that changes Terraform under `modules/`. After
   `terraform-ci` finishes with a successful `static` job, `terraform-test-agent`
   runs, may commit tests, then comments and files a check run.

Without `LLM_API_KEY`, CI and verification still run; authoring is skipped and
the PR comment says so.

## Where the agent and skills live

| Piece | Path |
|-------|------|
| Agent contract | [`.github/agents/terraform-test-agent.md`](.github/agents/terraform-test-agent.md) |
| Skills | [`.github/skills/*/SKILL.md`](.github/skills/) |
| Trusted runner | [`scripts/agent/runner.py`](scripts/agent/runner.py) |
| Allowlist / schema / sanitizer | `scripts/agent/allowlist.py`, `schema.py`, `sanitizer.py` |
| PR report + check run | [`scripts/agent/gh_report.py`](scripts/agent/gh_report.py) |
| CI | [`.github/workflows/terraform-ci.yml`](.github/workflows/terraform-ci.yml) |
| Agent workflow | [`.github/workflows/terraform-test-agent.yml`](.github/workflows/terraform-test-agent.yml) |

During a run the default-branch copy of `scripts/agent` and `.github/skills` is
copied over the PR tree before execution. Skills are executed as named steps and
listed in the PR comment: `discover-changed-modules`, `author-terraform-tests`,
`verify-terraform-tests`, `report-pr-findings`.

## How the model is controlled and verified

1. Untrusted input (diff, module source, PR markdown) is data only — skills are
   never loaded from the PR head.
2. Model output must pass `validate_decision` (schema + path allowlist bound to
   the discovered module + HCL guards: require `mock_provider "azurerm"`, reject
   apply/provisioners/external/backends and credential substrings).
3. Injection evals under `scripts/agent/evals/` prove that a draft editing
   `main.tf` or another module's tests is rejected.
4. `terraform test` is the verifier. Failed drafts are restored and not
   committed. Retries (capped at 2) call the model again with the sanitized
   failure log.
5. Shell commands are allowlisted (`init -backend=false`, `fmt -check`,
   `validate`, `test`). Shell `terraform apply` is rejected.

## Example run (designed demo)

Full walkthrough: [docs/example-run.md](docs/example-run.md).

Open a same-repo PR that only changes
`modules/function-app/main.tf` so `site_config.ftps_state` goes from
`AllAllowed` to `Disabled`, and leave the FTPS assertion in
`modules/function-app/tests/main.tftest.hcl` stale on purpose. Stale module
tests fail the `module-tests` job (`continue-on-error`); as long as `static`
passes, `terraform-test-agent` still runs.

**Expected agent decisions after publish:**

- discover → `function-app`
- author → `update_tests` on `modules/function-app/tests/main.tftest.hcl`
  (assertion becomes `Disabled`; `override_data` for `build_info` kept)
- verify → sandbox `terraform test` pass; JUnit artifact `agent-terraform-junit`
- report → comment + check run; finding that
  `public_network_access_enabled` still defaults to `true`; Checkov baseline
  IDs for the module are listed for reviewers

**Skills used:** all four listed above.

Until the repository is published and that example PR is opened against a remote
with `LLM_API_KEY` set, [docs/example-run.md](docs/example-run.md) is the
defense record. Local pytest and module `terraform test` prove the controls;
they are not a substitute for the live PR.

## What the tests can and cannot show

**Can:** plan-time attribute and count assertions; variable validation failures
(`expect_failures`); naming conventions; presence of identity / network ACL
settings as expressed in configuration; overridden external data values.

**Cannot:** prove a real Azure apply; Azure Policy; private DNS resolution;
identity federation in Entra; that `data.external` scripts are safe beyond
overriding them in tests; runtime behavior of the Function App.

## Assumptions

- Reviewers accept plan-time mocked tests as the offline contract.
- Same-repo pull requests are the primary collaboration path; forks get CI only.
- An OpenAI-compatible Chat Completions API is available for authoring.
- The publisher creates the public GitHub repository and emails the careers link.

## Limitations / residual risks

- `GITHUB_TOKEN` pushes do not re-trigger `terraform-ci`; the check run is the
  status on the bot commit (no PAT loop).
- Mocked apply is not used (provider ID validation).
- Checkov baseline records known module findings; the agent does not “fix”
  infrastructure. The PR comment surfaces baseline IDs for touched modules.
- harden-runner egress stays `audit` until a host allowlist is proven; flip to
  `block` in production.
- Authored tests for modules with `data "external"` must include `override_data`
  (enforced). Verify runs in a sandbox copy without `.git`; that still does not
  replace network egress controls.
- The recorded example in `docs/example-run.md` is not a live GitHub PR until
  the operator publishes the repo and opens one.

## Scale (many modules, teams, repositories)

- Matrix `terraform test` per changed module; cheap classify before any LLM call.
- Share the runner as a reusable workflow or composite action across repos.
- Central CODEOWNERS / org rulesets for `.github/**` and agent scripts.
- Per-team LLM budgets and model allowlists.

## Production delta

- Flip harden-runner to egress `block` with an explicit domain allowlist.
- Optional approval environment before test commits on protected repos.
- Stronger sandbox for any remaining `data.external` (no network, no `.git`).
- Threat-detection step between model output and commit (secret/patch scan).
- Metrics: author success rate, retry count, finding precision.
- Bot trailer plus verify-only re-run so branch protection sees a green
  `terraform-ci` on the bot commit without a looping PAT.

## Publish checklist (operator)

See [SECURITY.md](SECURITY.md). Outside this codebase edit session:

1. Publish the tree to a public GitHub repository (no assignment file).
2. Ensure hardened workflows and `scripts/agent` are on the **default branch**
   (`workflow_run` loads them from there).
3. Set secret `LLM_API_KEY`; optional vars `LLM_BASE_URL`, `LLM_MODEL`.
4. Replace `REPLACE_WITH_GITHUB_LOGIN` in CODEOWNERS; enable rulesets/scanning.
5. Open one example PR per [docs/example-run.md](docs/example-run.md).
