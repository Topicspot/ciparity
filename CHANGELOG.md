# Changelog

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
