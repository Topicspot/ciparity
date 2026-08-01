# ciparity

[English](../README.md) · [Русский](README.ru.md) · [简体中文](README.zh-CN.md) · **Español** · [Português](README.pt-BR.md)

[![PyPI](https://img.shields.io/pypi/v/ciparity?style=flat-square&label=pypi&color=3775A9)](https://pypi.org/project/ciparity/)
[![Python](https://img.shields.io/pypi/pyversions/ciparity?style=flat-square&color=4B8BBE)](https://pypi.org/project/ciparity/)
[![CI](https://github.com/Topicspot/ciparity/actions/workflows/ci.yml/badge.svg)](https://github.com/Topicspot/ciparity/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-MIT-green?style=flat-square)](https://github.com/Topicspot/ciparity/blob/main/LICENSE)

Tus hooks de pre-commit y tu CI deberían ejecutar las mismas comprobaciones. Con el tiempo dejan
de hacerlo: alguien sube la versión de `ruff` en `.pre-commit-config.yaml` y no en el workflow,
alguien añade `mypy --strict` solo en CI, alguien crea un hook que CI nunca ejecuta. El
resultado es una rama verde en local y roja al hacer push o, peor, verde en todas partes
mientras una comprobación dejó de correr en silencio.

ciparity lee `.pre-commit-config.yaml` y tu pipeline, GitHub Actions o GitLab CI, e imprime
dónde no coinciden.
Solo análisis estático: sin red, sin Docker, sin claves de API, y nunca ejecuta tus
herramientas.

```bash
pip install ciparity
ciparity .
```

![ciparity demo](https://raw.githubusercontent.com/Topicspot/ciparity/main/assets/demo.gif)

La grabación se genera desde ejecuciones reales con `scripts/demo_gif.py`, así que no puede
desviarse de la salida real.

El código de salida es 1 cuando hay diferencias, así que sirve como comprobación.

## Qué compara

| Comprobación | Ejemplo |
| --- | --- |
| Herramienta en un solo lado | `vulture` es un hook y ningún workflow lo ejecuta |
| Versiones distintas | hook `rev: v0.5.0` frente a `pip install ruff==0.6.2` |
| Argumentos distintos | `--strict` se pasa en CI pero no en el hook |
| Versión de Python | `default_language_version: python3.11` mientras CI instala solo 3.12 |

## Corrección automática

```bash
ciparity --fix
```

Cambia el `rev:` de `.pre-commit-config.yaml` a la versión que CI ya usa. El archivo se edita
como texto, así que los comentarios, las comillas y el orden de las claves se conservan.
`--fix --dry-run` muestra el diff sin escribir nada. Los workflows nunca se modifican.

## Uso

```text
ciparity [path] [--fix [--dry-run]] [--json] [--ignore pytest,codespell] [--exit-zero]
```

Como hook de pre-commit:

```yaml
repos:
  - repo: https://github.com/Topicspot/ciparity
    rev: v0.3.1
    hooks:
      - id: ciparity
```

En GitHub Actions:

```yaml
- uses: Topicspot/ciparity@v0.3.1
  with:
    path: .
```

## Límites

Analiza GitHub Actions (`.github/workflows/*.yml`) y GitLab CI (`.gitlab-ci.yml`, las versiones
salen del `image:`); `include:` solo se sigue para archivos locales. Solo compara
herramientas reconocidas: los hooks de
higiene de archivos como `trailing-whitespace` se ignoran a propósito, nadie los ejecuta en CI.
Si un workflow lanza `pre-commit run --all-files`, ambos lados coinciden por definición. Las
acciones compuestas y los workflows reutilizables no se siguen.

La documentación completa y la comparación con alternativas están en el
[README en inglés](../README.md).

