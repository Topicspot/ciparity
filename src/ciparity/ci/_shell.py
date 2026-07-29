"""Shell parsing shared by every provider.

CI systems differ in how they describe a pipeline, but they all end up running
shell commands, so version pinning and tool invocation are parsed once here.
"""

from __future__ import annotations

import re
import shlex

from ..tools import KNOWN_COMMANDS, WRAPPERS, canonical

_PIP_INSTALL = re.compile(
    r"\b(?:pip|pip3|uv pip|uv tool|pipx)\s+install\s+(?P<rest>[^\n&|;]+)", re.IGNORECASE
)
_NPM_INSTALL = re.compile(
    r"\b(?:npm\s+(?:i|install)|pnpm\s+add|yarn\s+add)\s+(?P<rest>[^\n&|;]+)", re.IGNORECASE
)
_SPEC = re.compile(r"^(?P<name>[A-Za-z0-9._-]+)(?:==|@)(?P<version>[0-9][^\s,;]*)$")


def installed_versions(script: str) -> dict[str, str]:
    found: dict[str, str] = {}
    for pattern in (_PIP_INSTALL, _NPM_INSTALL):
        for match in pattern.finditer(script):
            for token in match.group("rest").split():
                token = token.strip("'\"")
                if token.startswith("-"):
                    continue
                spec = _SPEC.match(token)
                if spec:
                    found[canonical(spec.group("name"))] = spec.group("version").lstrip("v")
    return found


def commands(script: str) -> list[list[str]]:
    out: list[list[str]] = []
    for raw_line in script.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        for part in re.split(r"&&|\|\||;|\|", line):
            try:
                tokens = shlex.split(part.strip())
            except ValueError:
                continue
            if tokens:
                out.append(tokens)
    return out


def tool_from_tokens(tokens: list[str]) -> tuple[str, tuple[str, ...], str | None] | None:
    index = 0
    while index < len(tokens) and tokens[index] in WRAPPERS:
        index += 1
    rest = tokens[index:]
    if not rest:
        return None
    if rest[0] in {"python", "python3"} and len(rest) > 2 and rest[1] == "-m":
        rest = rest[2:]
    head = rest[0]
    inline_version: str | None = None
    if "@" in head:
        # npx prettier@3.9.0, uvx ruff@0.6.2
        head, _, spec = head.partition("@")
        inline_version = spec.lstrip("v") or None
    name = canonical(head)
    if name not in KNOWN_COMMANDS:
        return None
    flags = tuple(sorted({t for t in rest[1:] if t.startswith("-")}))
    return name, flags, inline_version


_PRECOMMIT_RUN = re.compile(r"pre-commit\s+run\b(?P<rest>[^\n]*)")


def precommit_invocation(text: str, *, official_action: bool = False) -> tuple[bool, bool]:
    """Return whether the text runs pre-commit, and whether it covers every file."""
    if official_action:
        # The official GitHub action runs `pre-commit run --all-files` by default.
        return True, True
    runs = _PRECOMMIT_RUN.findall(text)
    if not runs:
        return False, True
    all_files = any("--all-files" in rest or "-a " in f" {rest} " for rest in runs)
    return True, all_files
