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

ciparity reads `.pre-commit-config.yaml` and your CI pipeline and prints where they disagree,
then fixes the version drift for you. Static parsing only: no network, no Docker, no API keys,
and it never runs your tools.

```bash
pip install ciparity
ciparity .
```

```
pre-commit hooks: 5   CI steps: 4

mypy     arguments differ: different arguments
           pre-commit: -
           ci:         --strict
ruff     version differs: pinned to different versions
           pre-commit: 0.5.0
           ci:         0.6.2
           fix:        rev v0.5.0 -> v0.6.2
vulture  not in pre-commit: runs in CI but is not a pre-commit hook
           ci:         ci.yml:test
python   python differs: pre-commit pins a python version CI never sets up
           pre-commit: 3.11
           ci:         3.12

4 difference(s).
1 can be fixed automatically: ciparity --fix
```

```console
$ ciparity --fix
--- .pre-commit-config.yaml
+++ .pre-commit-config.yaml
@@ -2,7 +2,7 @@
   python: python3.11
 repos:
   - repo: https://github.com/astral-sh/ruff-pre-commit
-    rev: v0.5.0
+    rev: v0.6.2
     hooks:
       - id: ruff
         args: [--fix]

https://github.com/astral-sh/ruff-pre-commit: rev v0.5.0 -> v0.6.2

Wrote .pre-commit-config.yaml. 1 fixed, 3 left.
```

`--fix` edits `.pre-commit-config.yaml` as text, so comments, quotes and key order survive. It
moves hooks onto the version CI already uses, because CI is the version every reviewer sees.
Use `--fix --dry-run` to see the diff and write nothing.

Exit code is 1 when there are differences, so it works as a check.

## What it looks for

| Check | Example |
| --- | --- |
| Tool in one side only | `vulture` is a hook, no workflow runs it |
| Version drift | hook `rev: v0.5.0` against `pip install ruff==0.6.2`, fixable |
| Argument drift | `--strict` passed in CI but not in the hook |
| Python version | `default_language_version: python3.11` while CI sets up only 3.12 |
| Node version | `default_language_version: node 20.11.0` while CI sets up 22 |
| Narrower in CI | CI runs `pre-commit run` without `--all-files`, so it only sees the diff |

Versions are read from hook `rev:`, from `pip install tool==x`, `uv tool install`, `pipx install`,
`npm i -g tool@x`, and from the `version:` input of known actions such as `astral-sh/ruff-action`.
Commands are found inside `run:` blocks, including behind `uv run`, `uvx`, `poetry run`, `npx`
and `python -m`.

## Usage

```
ciparity [path] [--fix [--dry-run]] [--json] [--ignore pytest,codespell] [--exit-zero]
```

As a pre-commit hook:

```yaml
repos:
  - repo: https://github.com/Topicspot/ciparity
    rev: v0.2.0
    hooks:
      - id: ciparity
```

## Deliberate non-goals and limits

- Only GitHub Actions is parsed today. The parser layer is provider based, GitLab CI is next.
- `--fix` only edits `.pre-commit-config.yaml`. It never rewrites your workflows.
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
