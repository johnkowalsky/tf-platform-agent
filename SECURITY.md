# Security

## Reporting a vulnerability

Please open a private GitHub security advisory on this repository, or email the
maintainer listed on the public repository page. Do not open a public issue for
credential leaks or remote-code risks in the agent workflows.

## What this repository does not do

- It never creates Azure resources in CI.
- The LLM API key is a GitHub Actions secret used only by the authoring step of
  `terraform-test-agent`. Verification runs without that key and without
  `GITHUB_TOKEN` in the Terraform process environment.
- Pull requests cannot replace the agent workflow: that workflow is triggered by
  `workflow_run` and always uses the copy on the default branch.

## Publish-time checklist

Enable on the public repository:

1. Secret scanning and push protection
2. Dependabot alerts
3. Private vulnerability reporting
4. Replace `REPLACE_WITH_GITHUB_LOGIN` in `.github/CODEOWNERS`
5. Default-branch ruleset: require a pull request, one approval, code-owner
   review for `.github/**` and `scripts/agent/**`, dismiss stale reviews, block
   force pushes
6. Repository secret `LLM_API_KEY` (and optional vars `LLM_BASE_URL`, `LLM_MODEL`)
7. Ensure Actions are not allowed to approve pull requests
