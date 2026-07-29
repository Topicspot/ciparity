# ciparity

**English** · [Русский](docs/README.ru.md) · [简体中文](docs/README.zh-CN.md) · [Español](docs/README.es.md) · [Português](docs/README.pt-BR.md)

[![PyPI](https://img.shields.io/pypi/v/ciparity?style=flat-square&label=pypi&color=3775A9)](https://pypi.org/project/ciparity/)
[![Python](https://img.shields.io/pypi/pyversions/ciparity?style=flat-square&color=4B8BBE)](https://pypi.org/project/ciparity/)
[![CI](https://github.com/Topicspot/ciparity/actions/workflows/ci.yml/badge.svg)](https://github.com/Topicspot/ciparity/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-MIT-green?style=flat-square)](https://github.com/Topicspot/ciparity/blob/main/LICENSE)

Your pre-commit hooks and your CI are supposed to run the same checks. Over time they stop.
Someone bumps `ruff` in `.pre-commit-config.yaml` and not in the workflow, someone adds
`mypy --strict` to CI only, someone adds a hook that CI never runs. Then the branch is green
locally and red on push, or worse, green everywhere while a check quietly stopped running.

ciparity reads `.pre-commit-config.yaml` and `.github/workflows/*.yml` and prints where they
disagree. Static parsing only: no network, no Docker, no API keys, and it never runs your tools.

```bash
pip install ciparity
ciparity .
```

```
pre-commit hooks: 5   CI steps: 4

ruff    version differs: pinned to different versions
            pre-commit: 0.5.0
            ci:         0.6.2
mypy    arguments differ: different arguments
            pre-commit: -
            ci:         --strict
pytest  not in pre-commit: runs in CI but is not a pre-commit hook
            ci:         ci.yml:test
python  python differs: pre-commit pins a python version CI never sets up
            pre-commit: 3.11
            ci:         3.12

4 difference(s).
```

Exit code is 1 when there are differences, so it works as a check.

## What it looks for

| Check | Example |
| --- | --- |
| Tool in one side only | `vulture` is a hook, no workflow runs it |
| Version drift | hook `rev: v0.5.0` against `pip install ruff==0.6.2` |
| Argument drift | `--strict` passed in CI but not in the hook |
| Python version | `default_language_version: python3.11` while CI sets up only 3.12 |

Versions are read from hook `rev:`, from `pip install tool==x`, `uv tool install`, `pipx install`,
`npm i -g tool@x`, and from the `version:` input of known actions such as `astral-sh/ruff-action`.
Commands are found inside `run:` blocks, including behind `uv run`, `uvx`, `poetry run`, `npx`
and `python -m`.

## Usage

```
ciparity [path] [--json] [--ignore pytest,codespell] [--exit-zero]
```

As a pre-commit hook:

```yaml
repos:
  - repo: https://github.com/Topicspot/ciparity
    rev: v0.1.1
    hooks:
      - id: ciparity
```

## Deliberate non-goals and limits

- Only GitHub Actions in this version. GitLab CI and others are not parsed.
- Only tools it recognises are compared. File hygiene hooks like `trailing-whitespace` are
  ignored on purpose, nobody runs those in CI and reporting them would be noise.
- If a workflow runs `pre-commit run --all-files`, the two sides are parity by definition and
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

## ☕ Support the author

This project is free and MIT-licensed. If it saved you time, you can send a coffee.

**USDT, Tron network (TRC-20) only:**

```
TS9ywGeSyKQxiCszdKCHLR8DRAsnYCosNN
```

<details>
<summary>Другие языки / Other languages</summary>

- **Українська:** проєкт безкоштовний. Якщо він заощадив вам час — можна підтримати автора,
  USDT у мережі Tron (TRC-20), адреса вище.
- **Русский:** проект бесплатный. Если он сэкономил вам время, можно поддержать автора,
  USDT в сети Tron (TRC-20), адрес выше.

</details>
