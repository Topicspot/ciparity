# ciparity

[English](../README.md) · [Русский](README.ru.md) · **简体中文** · [Español](README.es.md) · [Português](README.pt-BR.md)

[![PyPI](https://img.shields.io/pypi/v/ciparity?style=flat-square&label=pypi&color=3775A9)](https://pypi.org/project/ciparity/)
[![Python](https://img.shields.io/pypi/pyversions/ciparity?style=flat-square&color=4B8BBE)](https://pypi.org/project/ciparity/)
[![CI](https://github.com/Topicspot/ciparity/actions/workflows/ci.yml/badge.svg)](https://github.com/Topicspot/ciparity/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-MIT-green?style=flat-square)](https://github.com/Topicspot/ciparity/blob/main/LICENSE)

pre-commit 钩子和 CI 本该运行相同的检查，但它们会慢慢分叉：有人在
`.pre-commit-config.yaml` 里升级了 `ruff` 却没有改 workflow，有人只在 CI 里加了
`mypy --strict`，有人加了 CI 从不运行的钩子。结果是本地绿、推送后红，更糟的是到处都绿，而某项
检查已经悄悄停止运行。

ciparity 读取 `.pre-commit-config.yaml` 和 `.github/workflows/*.yml`，指出两边不一致的地方。
只做静态解析：不联网、不需要 Docker、不需要密钥，也从不执行你的工具。

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

存在差异时退出码为 1，因此它可以直接当作一项检查使用。

## 对比的内容

| 检查 | 示例 |
| --- | --- |
| 只存在于一侧的工具 | `vulture` 是钩子，但没有任何 workflow 运行它 |
| 版本漂移 | 钩子 `rev: v0.5.0` 对上 `pip install ruff==0.6.2` |
| 参数漂移 | CI 传了 `--strict`，钩子没有 |
| Python 版本 | `default_language_version: python3.11`，而 CI 只安装 3.12 |

## 用法

```
ciparity [path] [--json] [--ignore pytest,codespell] [--exit-zero]
```

作为 pre-commit 钩子：

```yaml
repos:
  - repo: https://github.com/Topicspot/ciparity
    rev: v0.1.1
    hooks:
      - id: ciparity
```

## 局限

当前版本只解析 GitHub Actions。只比较可识别的工具：`trailing-whitespace` 这类文件整洁钩子被
刻意忽略，因为没人在 CI 里跑它们。如果 workflow 执行 `pre-commit run --all-files`，两边按定义
一致。复合动作和可复用 workflow 不会被展开。

完整文档与同类工具对比见[英文 README](../README.md)。

