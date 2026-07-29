# ciparity

[English](../README.md) · [Русский](README.ru.md) · [简体中文](README.zh-CN.md) · [Español](README.es.md) · **Português**

[![PyPI](https://img.shields.io/pypi/v/ciparity?style=flat-square&label=pypi&color=3775A9)](https://pypi.org/project/ciparity/)
[![Python](https://img.shields.io/pypi/pyversions/ciparity?style=flat-square&color=4B8BBE)](https://pypi.org/project/ciparity/)
[![CI](https://github.com/Topicspot/ciparity/actions/workflows/ci.yml/badge.svg)](https://github.com/Topicspot/ciparity/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-MIT-green?style=flat-square)](https://github.com/Topicspot/ciparity/blob/main/LICENSE)

Seus hooks de pre-commit e seu CI deveriam rodar as mesmas verificações. Com o tempo eles se
separam: alguém atualiza o `ruff` no `.pre-commit-config.yaml` e esquece o workflow, alguém
adiciona `mypy --strict` só no CI, alguém cria um hook que o CI nunca executa. O resultado é uma
branch verde no local e vermelha no push ou, pior, verde em todo lugar enquanto uma verificação
parou de rodar em silêncio.

ciparity lê `.pre-commit-config.yaml` e `.github/workflows/*.yml` e mostra onde os dois
divergem. Apenas análise estática: sem rede, sem Docker, sem chaves de API, e ele nunca executa
suas ferramentas.

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

3 difference(s).
```

O código de saída é 1 quando há diferenças, então dá para usar como verificação.

## O que é comparado

| Verificação | Exemplo |
| --- | --- |
| Ferramenta em apenas um lado | `vulture` é hook e nenhum workflow o executa |
| Versões diferentes | hook `rev: v0.5.0` contra `pip install ruff==0.6.2` |
| Argumentos diferentes | `--strict` passado no CI mas não no hook |
| Versão do Python | `default_language_version: python3.11` enquanto o CI instala só 3.12 |

## Uso

```
ciparity [path] [--json] [--ignore pytest,codespell] [--exit-zero]
```

Como hook de pre-commit:

```yaml
repos:
  - repo: https://github.com/Topicspot/ciparity
    rev: v0.1.1
    hooks:
      - id: ciparity
```

## Limites

Esta versão analisa apenas GitHub Actions. Só compara ferramentas reconhecidas: hooks de higiene
de arquivos como `trailing-whitespace` são ignorados de propósito, ninguém os roda no CI. Se um
workflow executa `pre-commit run --all-files`, os dois lados são equivalentes por definição.
Actions compostas e workflows reutilizáveis não são seguidos.

A documentação completa e a comparação com alternativas estão no
[README em inglês](../README.md).

