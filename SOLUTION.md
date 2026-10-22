# Solution: Terraform test agent

A GitHub-native agent that creates or updates mocked `terraform test` files on
the same pull request, verifies them without Azure credentials, and reports
results plus reviewer findings.

## Main technical decisions (and what we gave up)

1. **Two workflows, one trust boundary.** `terraform-ci.yml` is secret-free and
   runs on `pull_request`. `terraform-test-agent.yml` runs on `workflow_run` of
   that CI workflow and always uses the workflow file and skills from the
   **default branch**, so a PR cannot swap the agent or the secret path.
   *Gave up:* a single job with `contents: write` on untrusted PR code; Cursor
   Cloud / Copilot as the CI runner.

2. **Safe output on the same PR.** The assignment forbids a second pull request.
   The model returns JSON only. A deterministic checker accepts paths under
   `modules/<name>/tests/**/*.tftest.hcl` only. `terraform test` runs in an
   environment without `LLM_API_KEY` or `GITHUB_TOKEN`. Only a passing result is
   committed with message `test-agent: update tests`.
   *Gave up:* GitHub Agentic Workflows `create-pull-request` (would open another
   PR); a PAT that re-triggers CI (would loop).

3. **Results visible on the PR.** A `workflow_run` job is not a PR check by
   itself. The agent upserts one sanitized comment and opens a **check run** on
   the head SHA (and on the bot commit SHA after a test push).
   *Gave up:* relying on the Actions tab alone.

4. **Plan-time mocked tests.** Behavior uses `command = plan` with
   `mock_provider "azurerm"`. Mocked `command = apply` failed because azurerm
   validates resource ID formats against random mock IDs. Function-app keeps
   plan tests because `data.external` runs a real script.
   *Gave up:* AVM-style mocked apply and a `tests/unit/` layout rewrite.

5. **Supply-chain gates after the agent path.** Actions are pinned to full SHAs.
   zizmor, Scorecard, CodeQL, dependency-review, Dependabot, TFLint, and Checkov
   (with a committed baseline) are included.
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
3. Follow [SECURITY.md](SECURITY.md) for scanning, rulesets, and CODEOWNERS.
4. Open a pull request that changes Terraform under `modules/`. After
   `terraform-ci` succeeds, `terraform-test-agent` runs, may commit tests, then
   comments and files a check run.

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

1. Untrusted input (diff, PR markdown) is data only — skills are never loaded
   from the PR head.
2. Model output must pass `validate_decision` (schema + path allowlist + HCL
   guards: require `mock_provider "azurerm"`, reject backends and credential
   substrings).
3. Injection evals under `scripts/agent/evals/` prove that a draft editing
   `main.tf` is rejected.
4. `terraform test` is the verifier. Failed drafts are not committed. Retries
   capped at 2.
5. Shell commands are allowlisted (`init -backend=false`, `fmt -check`,
   `validate`, `test`). Shell `terraform apply` is rejected.

## Example run (intended demo)

**Human change** on branch `example/function-app-ftps`: set
`modules/function-app` `site_config.ftps_state` from `AllAllowed` to
`Disabled`.

**Agent decisions:**

- discover → `function-app`
- author → `update_tests` on `modules/function-app/tests/main.tftest.hcl`
  (assertion becomes `Disabled`)
- verify → `terraform test` passes
- report → comment + check run; finding that
  `public_network_access_enabled` still defaults to `true`

**Skills used:** all four listed above.

Until the repository is published and the example PR is opened, this section
describes the designed run. Local branch `example/function-app-ftps` holds the
human edit only.

## What the tests can and cannot show

**Can:** plan-time attribute and count assertions; variable validation failures
(`expect_failures`); naming conventions; presence of identity / network ACL
settings as expressed in configuration.

**Cannot:** prove a real Azure apply; Azure Policy; private DNS resolution;
identity federation in Entra; that `data.external` scripts are safe beyond
running them without secrets; runtime behavior of the Function App.

## Assumptions

- Reviewers accept plan-time mocked tests as the offline contract.
- Same-repo pull requests are the primary collaboration path; forks get CI only.
- An OpenAI-compatible Chat Completions API is available for authoring.
- The publisher creates the public GitHub repository and emails the careers link.

## Limitations

- `GITHUB_TOKEN` pushes do not re-trigger `terraform-ci`; the check run is the
  status on the bot commit.
- Mocked apply is not used (provider ID validation).
- Checkov baseline records known module findings; the agent does not “fix”
  infrastructure.
- harden-runner egress is `audit` until a host allowlist is proven.

## Scale (many modules, teams, repositories)

- Matrix `terraform test` per changed module; cheap classify before any LLM call.
- Share the runner as a reusable workflow or composite action across repos.
- Central CODEOWNERS / org rulesets for `.github/**` and agent scripts.
- Per-team LLM budgets and model allowlists.

## Production delta

- Flip harden-runner to egress `block` with an explicit domain allowlist.
- Optional approval environment before test commits on protected repos.
- Stronger sandbox for `data.external` (no shell from the PR tree).
- Threat-detection step between model output and commit (secret/patch scan).
- Metrics: author success rate, retry count, finding precision.

## Publish checklist

See [SECURITY.md](SECURITY.md). First push should be an unmodified import of the
upstream Terraform tree plus this solution (no assignment file). Then open the
example PR from `example/function-app-ftps`.
