"""Canonical tool names and how to recognise them."""

from __future__ import annotations

# Hook ids that mean the same tool. Anything not listed keeps its own id.
HOOK_ALIASES: dict[str, str] = {
    "ruff-check": "ruff",
    "ruff-format": "ruff-format",
    "mypy": "mypy",
    "black": "black",
    "isort": "isort",
    "flake8": "flake8",
    "pyupgrade": "pyupgrade",
    "bandit": "bandit",
    "codespell": "codespell",
    "gitleaks": "gitleaks",
    "detect-secrets": "detect-secrets",
    "markdownlint": "markdownlint",
    "markdownlint-cli2": "markdownlint",
    "prettier": "prettier",
    "eslint": "eslint",
    "shellcheck": "shellcheck",
    "shfmt": "shfmt",
    "yamllint": "yamllint",
    "vulture": "vulture",
    "pytest": "pytest",
    "nbstripout": "nbstripout",
}

# Repo-level hints, used when a hook id is a generic name like "run".
REPO_HINTS: dict[str, str] = {
    "astral-sh/ruff-pre-commit": "ruff",
    "psf/black": "black",
    "pre-commit/mirrors-mypy": "mypy",
    "pycqa/isort": "isort",
    "pycqa/flake8": "flake8",
    "pycqa/bandit": "bandit",
    "gitleaks/gitleaks": "gitleaks",
    "igorshubovych/markdownlint-cli": "markdownlint",
    "pre-commit/mirrors-prettier": "prettier",
    "pre-commit/mirrors-eslint": "eslint",
    "adrienverge/yamllint": "yamllint",
    "jendrikseipp/vulture": "vulture",
}

# GitHub Actions that run a tool instead of a shell command.
ACTION_TOOLS: dict[str, str] = {
    "astral-sh/ruff-action": "ruff",
    "psf/black": "black",
    "gitleaks/gitleaks-action": "gitleaks",
    "reviewdog/action-eslint": "eslint",
    "avto-dev/markdown-lint": "markdownlint",
    "pypa/gh-action-pip-audit": "pip-audit",
    "tsuyoshicho/action-mypy": "mypy",
    "lycheeverse/lychee-action": "lychee",
}

# Commands worth tracking when they show up in a `run:` block.
KNOWN_COMMANDS: frozenset[str] = frozenset(
    {
        "ruff",
        "mypy",
        "black",
        "isort",
        "flake8",
        "pytest",
        "pyupgrade",
        "bandit",
        "codespell",
        "gitleaks",
        "detect-secrets",
        "markdownlint",
        "markdownlint-cli2",
        "prettier",
        "eslint",
        "tsc",
        "knip",
        "shellcheck",
        "shfmt",
        "yamllint",
        "vulture",
        "pip-audit",
        "lychee",
        "coverage",
        "tox",
        "nox",
    }
)

# Wrappers that are skipped so the real command is found.
WRAPPERS: frozenset[str] = frozenset(
    {"uv", "uvx", "run", "poetry", "pipx", "npx", "pdm", "hatch", "rye", "sudo", "time"}
)


def canonical(name: str) -> str:
    """Map an observed name to the canonical tool name."""
    name = name.strip().lower()
    if name in HOOK_ALIASES:
        return HOOK_ALIASES[name]
    if name == "markdownlint-cli2":
        return "markdownlint"
    return name


def from_repo(repo: str) -> str | None:
    """Canonical tool for a pre-commit repo URL, if we know it."""
    slug = repo.lower().removeprefix("https://github.com/").removesuffix(".git")
    return REPO_HINTS.get(slug)
