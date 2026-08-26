# Changelog

## Unreleased

- The quality gate is now declared on both sides: `vulture`, `pip-audit`, `markdownlint-cli2`,
  `gitleaks` and `lychee` run in CI and are listed in `.pre-commit-config.yaml`, so
  `ciparity .` on this repository has something real to compare instead of five hooks CI
  never runs.
- `scripts/pip_audit.sh` exports the dev dependencies and audits them, shared by the hook and
  `scripts/check.sh`.

## 0.3.1 - 2026-08-01

- New GitHub Action: `uses: Topicspot/ciparity@v0.3.1` runs the published package as a step in an
  existing workflow, so the job fails when hooks and CI drift apart.
- README shows a terminal recording generated from real runs by `scripts/demo_gif.py` instead of
  hand-typed output blocks.
- `scripts/check.sh` runs the full local quality gate, `CONTRIBUTING.md` documents it.
- Package description now mentions GitLab CI, which has been supported since 0.3.0.

## 0.3.0 - 2026-07-29

- GitLab CI is parsed: jobs in `.gitlab-ci.yml`, commands from `before_script`, `script` and
  `after_script`, tool versions from the shell, python and node versions from the job `image:`.
  Local `include:` files are read; includes ciparity cannot reach are reported as a blind spot
  instead of being ignored.
- Both providers are compared at once when a repository has both, and a version that two
  pipelines disagree about is reported but never auto-fixed.
- Shell parsing moved to `ciparity.ci._shell`, so a provider only describes where its scripts
  live.
- Text output names the CI systems it found.

## 0.2.0 - 2026-07-29

- `ciparity --fix` rewrites hook revs in `.pre-commit-config.yaml` to the version CI already
  uses. The file is edited as text, so comments, quotes and key order survive. `--dry-run`
  prints the diff and writes nothing. Workflows are never rewritten.
- New check: CI runs `pre-commit run` without `--all-files`, so hooks only see changed files.
- New check: node version drift between `default_language_version` and `actions/setup-node`.
- Parsing moved behind a provider interface (`ciparity.ci`), so a second CI system is a new
  module rather than a rewrite. GitHub Actions is still the only provider.
- Findings now say whether they are fixable, in text output and in `--json`.

## 0.1.1 - 2026-07-29

- The package version is now read from installed metadata instead of being duplicated in
  `__init__.py`, and a test fails if it drifts from pyproject.toml.
- Added README translations (Русский, 简体中文, Español, Português) with a language switcher
  and a badge row.

## 0.1.0 - 2026-07-29

First release.

- Compares `.pre-commit-config.yaml` with `.github/workflows/*.yml`.
- Reports tools present on one side only, version drift, argument drift and python
  version drift.
- Understands `pip install`, `uv tool install`, `pipx install`, `npm i -g`, `npx tool@version`
  and the `version:` input of common actions.
- Suppresses findings when CI runs pre-commit itself, when pre-commit.ci is configured, or
  when CI delegates to a task runner, and says so in a note.
- `--json`, `--ignore`, `--exit-zero`, exit code 1 on findings.
