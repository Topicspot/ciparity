"""Parse GitHub Actions workflows into tool uses."""

from __future__ import annotations

import re
import shlex
from pathlib import Path
from typing import Any

import yaml

from .model import ToolUse
from .tools import ACTION_TOOLS, KNOWN_COMMANDS, WRAPPERS, canonical

_PIP_INSTALL = re.compile(
    r"\b(?:pip|pip3|uv pip|uv tool|pipx)\s+install\s+(?P<rest>[^\n&|;]+)", re.IGNORECASE
)
_NPM_INSTALL = re.compile(
    r"\b(?:npm\s+(?:i|install)|pnpm\s+add|yarn\s+add)\s+(?P<rest>[^\n&|;]+)", re.IGNORECASE
)
_SPEC = re.compile(r"^(?P<name>[A-Za-z0-9._-]+)(?:==|@)(?P<version>[0-9][^\s,;]*)$")


def _installed_versions(script: str) -> dict[str, str]:
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


def _commands(script: str) -> list[list[str]]:
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


def _tool_from_tokens(tokens: list[str]) -> tuple[str, tuple[str, ...], str | None] | None:
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


def _python_versions(node: Any, found: set[str]) -> None:
    if isinstance(node, dict):
        for key, value in node.items():
            if key in {"python-version", "python-versions"}:
                values = value if isinstance(value, list) else [value]
                for item in values:
                    text = str(item).strip()
                    if text and not text.startswith("${{"):
                        found.add(text)
            else:
                _python_versions(value, found)
    elif isinstance(node, list):
        for item in node:
            _python_versions(item, found)


def parse_workflow(path: Path) -> tuple[list[ToolUse], set[str]]:
    """Return tool uses in one workflow file plus the python versions it sets up."""
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        return [], set()

    pythons: set[str] = set()
    _python_versions(data, pythons)

    uses: list[ToolUse] = []
    jobs = data.get("jobs")
    if not isinstance(jobs, dict):
        jobs = {}
    for job_name, job in jobs.items():
        if not isinstance(job, dict):
            continue
        steps = job.get("steps") or []
        script = "\n".join(str(s.get("run", "")) for s in steps if isinstance(s, dict))
        versions = _installed_versions(script)
        for step in steps:
            if not isinstance(step, dict):
                continue
            location = f"{path.name}:{job_name}"
            action = str(step.get("uses", "")).split("@")[0]
            if action in ACTION_TOOLS:
                raw_with = step.get("with")
                with_block: dict[str, Any] = raw_with if isinstance(raw_with, dict) else {}
                raw_version = str(with_block.get("version", "")).strip() or None
                uses.append(
                    ToolUse(
                        name=ACTION_TOOLS[action],
                        version=raw_version.lstrip("v") if raw_version else None,
                        args=(),
                        source="ci",
                        location=location,
                    )
                )
                continue
            run = step.get("run")
            if not isinstance(run, str):
                continue
            for tokens in _commands(run):
                parsed = _tool_from_tokens(tokens)
                if parsed is None:
                    continue
                name, flags, inline_version = parsed
                uses.append(
                    ToolUse(
                        name=name,
                        version=inline_version or versions.get(name),
                        args=flags,
                        source="ci",
                        location=location,
                    )
                )
    return uses, pythons


def parse_workflows(directory: Path) -> tuple[list[ToolUse], set[str]]:
    uses: list[ToolUse] = []
    pythons: set[str] = set()
    for path in sorted(directory.glob("*.y*ml")):
        found, versions = parse_workflow(path)
        uses.extend(found)
        pythons |= versions
    return uses, pythons
