"""GitLab CI provider.

A `.gitlab-ci.yml` is a flat mapping: every top-level key that is not reserved
and does not start with a dot is a job, and a job runs shell commands listed in
`before_script`, `script` and `after_script`. Runtime versions come from the
image a job runs in, `python:3.12-slim` and friends.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

from ..model import CiFacts, ToolUse
from ._shell import commands, installed_versions, precommit_invocation, tool_from_tokens

CONFIG_NAMES = (".gitlab-ci.yml", ".gitlab-ci.yaml")

# Top-level keys that configure the pipeline instead of defining a job.
RESERVED = frozenset(
    {
        "default",
        "include",
        "stages",
        "variables",
        "workflow",
        "image",
        "services",
        "before_script",
        "after_script",
        "cache",
        "pages",
    }
)

_SCRIPT_KEYS = ("before_script", "script", "after_script")
_IMAGE = re.compile(r"^(?P<name>[a-z0-9./_-]+):(?P<tag>[A-Za-z0-9._-]+)$")


def _flatten(value: Any) -> list[str]:
    """Script keys accept a string, a list, or a list of lists."""
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        out: list[str] = []
        for item in value:
            out.extend(_flatten(item))
        return out
    return []


def _image_name(value: Any) -> str | None:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, dict):
        name = value.get("name")
        if isinstance(name, str):
            return name.strip()
    return None


def _runtime_version(image: str | None, runtime: str) -> str | None:
    """Read `3.12` out of `python:3.12-slim`, ignoring digests and registries."""
    if not image or "$" in image:
        return None
    match = _IMAGE.match(image.split("@")[0])
    if not match:
        return None
    if match.group("name").rsplit("/", 1)[-1] != runtime:
        return None
    version = match.group("tag").split("-")[0]
    return version if version[:1].isdigit() else None


def _jobs(data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    jobs: dict[str, dict[str, Any]] = {}
    for name, body in data.items():
        if name in RESERVED or name.startswith(".") or not isinstance(body, dict):
            continue
        if not any(key in body for key in _SCRIPT_KEYS):
            continue
        jobs[name] = body
    return jobs


def _local_includes(data: dict[str, Any], root: Path) -> tuple[list[Path], bool]:
    """Return local included files, plus whether an unreachable include exists."""
    raw = data.get("include")
    if raw is None:
        return [], False
    items = raw if isinstance(raw, list) else [raw]
    paths: list[Path] = []
    external = False
    for item in items:
        if isinstance(item, str):
            local: str | None = item
        elif isinstance(item, dict):
            value = item.get("local")
            local = value if isinstance(value, str) else None
            external = external or local is None
        else:
            external = True
            continue
        if local is None:
            continue
        candidate = root / local.lstrip("/")
        if candidate.is_file():
            paths.append(candidate)
        else:
            external = True
    return paths, external


def parse_config(path: Path, root: Path) -> tuple[list[ToolUse], set[str], set[str], str, bool]:
    """Return tool uses, python versions, node versions, script text, and blind spots."""
    loaded = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(loaded, dict):
        return [], set(), set(), "", False
    data: dict[str, Any] = loaded

    includes, external = _local_includes(data, root)
    for included in includes:
        extra = yaml.safe_load(included.read_text(encoding="utf-8")) or {}
        if isinstance(extra, dict):
            for key, value in extra.items():
                data.setdefault(key, value)

    raw_default = data.get("default")
    default: dict[str, Any] = raw_default if isinstance(raw_default, dict) else {}
    default_image = _image_name(default.get("image") or data.get("image"))
    default_script = _flatten(default.get("before_script")) + _flatten(data.get("before_script"))

    uses: list[ToolUse] = []
    pythons: set[str] = set()
    nodes: set[str] = set()
    all_text: list[str] = []

    for job_name, job in _jobs(data).items():
        image = _image_name(job.get("image")) or default_image
        python = _runtime_version(image, "python")
        node = _runtime_version(image, "node")
        if python:
            pythons.add(python)
        if node:
            nodes.add(node)

        lines = list(default_script)
        for key in _SCRIPT_KEYS:
            lines.extend(_flatten(job.get(key)))
        script = "\n".join(lines)
        all_text.append(script)
        versions = installed_versions(script)
        location = f"{path.name}:{job_name}"
        for tokens in commands(script):
            parsed = tool_from_tokens(tokens)
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
    return uses, pythons, nodes, "\n".join(all_text), external


class GitLabCI:
    """Reads `.gitlab-ci.yml` in the repository root."""

    name = "GitLab CI"

    def config_path(self, root: Path) -> Path | None:
        for filename in CONFIG_NAMES:
            candidate = root / filename
            if candidate.is_file():
                return candidate
        return None

    def detect(self, root: Path) -> bool:
        return self.config_path(root) is not None

    def parse(self, root: Path) -> CiFacts:
        path = self.config_path(root)
        facts = CiFacts(provider=self.name)
        if path is None:
            return facts
        uses, pythons, nodes, text, external = parse_config(path, root)
        facts.uses.extend(uses)
        facts.pythons |= pythons
        facts.nodes |= nodes
        facts.runs_precommit, facts.precommit_all_files = precommit_invocation(text)
        if external:
            facts.notes.append(
                f"{path.name} pulls in includes ciparity cannot read, "
                "so jobs defined there are invisible."
            )
        return facts
