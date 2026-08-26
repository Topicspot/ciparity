# ciparity

**English** · [Русский](docs/README.ru.md) · [简体中文](docs/README.zh-CN.md) · [Español](docs/README.es.md) · [Português](docs/README.pt-BR.md)

[![PyPI](https://img.shields.io/pypi/v/ciparity?style=flat-square&label=pypi&color=3775A9)](https://pypi.org/project/ciparity/)
[![Python](https://img.shields.io/pypi/pyversions/ciparity?style=flat-square&color=4B8BBE)](https://pypi.org/project/ciparity/)
[![CI](https://github.com/Topicspot/ciparity/actions/workflows/ci.yml/badge.svg)](https://github.com/Topicspot/ciparity/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-MIT-green?style=flat-square)](https://github.com/Topicspot/ciparity/blob/main/LICENSE)

Your hooks passed. CI failed anyway. The two configs drifted apart: someone bumped `ruff` in
`.pre-commit-config.yaml` and not in the workflow, someone added `mypy --strict` to CI only,
someone added a hook CI never runs. The worse case is quieter: both sides green while a check
stopped running months ago.

ciparity reads `.pre-commit-config.yaml` and your CI pipeline, GitHub Actions or GitLab CI, and
prints where they disagree, then fixes the version drift for you. Static parsing only: no
network, no Docker, no API keys, and it never runs your tools.

```bash
pip install ciparity
ciparity .
```

![ciparity demo](https://raw.githubusercontent.com/Topicspot/ciparity/main/assets/demo.gif)

The recording above is generated from real runs by `scripts/demo_gif.py`, so it cannot drift
away from what the tool actually prints.

`--fix` edits `.pre-commit-config.yaml` as text, so comments, quotes and key order survive. It
moves hooks onto the version CI already uses, because CI is the version every reviewer sees.
Use `--fix --dry-run` to see the diff and write nothing.

Exit code is 1 when there are differences, so it works as a check.

## What it looks for

| Check | Example |
| --- | --- |
| Tool in one side only | `vulture` is a hook, no CI job runs it |
| Version drift | hook `rev: v0.5.0` against `pip install ruff==0.6.2`, fixable |
| Argument drift | `--strict` passed in CI but not in the hook |
| Python version | `default_language_version: python3.11` while CI sets up only 3.12 |
| Node version | `default_language_version: node 20.11.0` while CI sets up 22 |
| Narrower in CI | CI runs `pre-commit run` without `--all-files`, so it only sees the diff |

Versions are read from hook `rev:`, from `pip install tool==x`, `uv tool install`, `pipx install`,
`npm i -g tool@x`, and from the `version:` input of known actions such as `astral-sh/ruff-action`.
Commands are found in workflow `run:` blocks and in GitLab `script:` blocks, including behind
`uv run`, `uvx`, `poetry run`, `npx` and `python -m`.

## Supported CI

| Provider | Read from | Runtime versions from |
| --- | --- | --- |
| GitHub Actions | `.github/workflows/*.yml` | `setup-python`, `setup-node` |
| GitLab CI | `.gitlab-ci.yml`, plus `include: local:` files | the job `image:`, `python:3.12-slim` |

Both are parsed when both exist, and a repository that pins different versions in different
pipelines gets reported instead of silently fixed.

## Usage

```text
ciparity [path] [--fix [--dry-run]] [--json] [--ignore pytest,codespell] [--exit-zero]
```

As a pre-commit hook:

```yaml
repos:
  - repo: https://github.com/Topicspot/ciparity
    rev: v0.3.1
    hooks:
      - id: ciparity
```

In GitHub Actions, as a step in the workflow you already have:

```yaml
- uses: Topicspot/ciparity@v0.3.1
  with:
    path: .
    args: --ignore codespell
```

The action installs the published package and runs it, so the job fails when the two sides drift
apart. `version:` pins a release; leaving it empty installs the latest one.

## Deliberate non-goals and limits

- Only GitHub Actions and GitLab CI are parsed. Other systems are a new module in
  `ciparity/ci/`, and pull requests are welcome.
- `--fix` only edits `.pre-commit-config.yaml`. It never rewrites your pipelines.
- GitLab `include:` is followed for local files only. Remote and template includes are reported
  as a blind spot rather than ignored quietly.
- Only tools it recognises are compared. File hygiene hooks like `trailing-whitespace` are
  ignored on purpose, nobody runs those in CI and reporting them would be noise.
- If a CI job runs `pre-commit run --all-files`, the two sides are parity by definition and
  "missing in CI" findings are suppressed.
- Composite actions and reusable workflows are not followed, so tools that only run inside them
  are invisible.
- Flags such as `--fix` or `--all-files` are treated as mode flags and never reported.

## Alternatives

- [pre-commit.ci](https://pre-commit.ci) runs your hooks as a service, which removes the drift
  instead of reporting it. If you can use it, use it.
- [act](https://github.com/nektos/act) runs workflows locally, so you can see what CI does. It
  answers a different question and is much heavier.
- [zizmor](https://github.com/woodruffw/zizmor) and
  [actionlint](https://github.com/rhysd/actionlint) lint the workflow files themselves. They do
  not know your pre-commit config.

## License

MIT
