# ciparity

[English](../README.md) · **Русский** · [简体中文](README.zh-CN.md) · [Español](README.es.md) · [Português](README.pt-BR.md)

[![PyPI](https://img.shields.io/pypi/v/ciparity?style=flat-square&label=pypi&color=3775A9)](https://pypi.org/project/ciparity/)
[![Python](https://img.shields.io/pypi/pyversions/ciparity?style=flat-square&color=4B8BBE)](https://pypi.org/project/ciparity/)
[![CI](https://github.com/Topicspot/ciparity/actions/workflows/ci.yml/badge.svg)](https://github.com/Topicspot/ciparity/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-MIT-green?style=flat-square)](https://github.com/Topicspot/ciparity/blob/main/LICENSE)

Пре-коммит-хуки и CI должны запускать одни и те же проверки. Со временем они расходятся: кто-то
поднял версию `ruff` в `.pre-commit-config.yaml` и забыл про workflow, кто-то добавил
`mypy --strict` только в CI, кто-то завёл хук, который CI никогда не запускает. В итоге ветка
зелёная локально и красная после пуша — или, что хуже, зелёная везде, пока одна проверка тихо
перестала работать.

ciparity читает `.pre-commit-config.yaml` и ваш пайплайн — GitHub Actions или GitLab CI — и
показывает, где они расходятся. Только статический разбор: без сети, без Docker, без ключей, и он никогда не
запускает ваши инструменты.

```bash
pip install ciparity
ciparity .
```

```
pre-commit hooks: 5   CI steps: 4   ci: GitHub Actions

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

Код возврата 1, если расхождения есть, поэтому команду можно ставить как проверку.

## Что сравнивается

| Проверка | Пример |
| --- | --- |
| Инструмент только с одной стороны | `vulture` есть в хуках, ни один workflow его не запускает |
| Разные версии | хук `rev: v0.5.0` против `pip install ruff==0.6.2` |
| Разные аргументы | `--strict` передаётся в CI, но не в хуке |
| Версия Python | `default_language_version: python3.11`, а CI ставит только 3.12 |

## Автопочинка

```bash
ciparity --fix
```

Правит `rev:` в `.pre-commit-config.yaml` на версию, которую уже использует CI. Файл
редактируется как текст, поэтому комментарии, кавычки и порядок ключей остаются на месте.
`--fix --dry-run` показывает дифф и ничего не пишет. Workflow-файлы инструмент не трогает.

## Использование

```
ciparity [path] [--fix [--dry-run]] [--json] [--ignore pytest,codespell] [--exit-zero]
```

Как пре-коммит-хук:

```yaml
repos:
  - repo: https://github.com/Topicspot/ciparity
    rev: v0.3.0
    hooks:
      - id: ciparity
```

## Ограничения

Разбираются GitHub Actions (`.github/workflows/*.yml`) и GitLab CI (`.gitlab-ci.yml`, версии
рантайма берутся из `image:`); `include:` раскрывается только для локальных файлов, остальные
честно отмечаются как слепая зона. Сравниваются только известные инструменты: хуки гигиены
файлов вроде `trailing-whitespace` намеренно игнорируются, в CI их никто не гоняет. Если задача
CI запускает `pre-commit run --all-files`, стороны считаются согласованными. Составные действия
и переиспользуемые workflow не раскрываются. `--fix` правит только
`.pre-commit-config.yaml`.

Полная документация и сравнение с альтернативами — в [английском README](../README.md).

