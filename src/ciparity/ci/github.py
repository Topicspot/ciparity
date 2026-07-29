"""GitHub Actions provider."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from ..model import CiFacts, ToolUse
from ..tools import ACTION_TOOLS
from ._shell import commands, installed_versions, precommit_invocation, tool_from_tokens


def _versions_for(node: Any, keys: set[str], found: set[str]) -> None:
    """Collect values of setup-action inputs such as `python-version`."""
    if isinstance(node, dict):
        for key, value in node.items():
            if key in keys:
                values = value if isinstance(value, list) else [value]
                for item in values:
                    text = str(item).strip()
                    if text and not text.startswith("${{"):
                        found.add(text)
            else:
                _versions_for(value, keys, found)
    elif isinstance(node, list):
        for item in node:
            _versions_for(item, keys, found)


_PYTHON_KEYS = {"python-version", "python-versions"}
_NODE_KEYS = {"node-version", "node-versions"}


def parse_workflow(path: Path) -> tuple[list[ToolUse], set[str], set[str]]:
    """Return tool uses in one workflow plus the python and node versions it sets up."""
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        return [], set(), set()

    pythons: set[str] = set()
    nodes: set[str] = set()
    _versions_for(data, _PYTHON_KEYS, pythons)
    _versions_for(data, _NODE_KEYS, nodes)

    uses: list[ToolUse] = []
    jobs = data.get("jobs")
    if not isinstance(jobs, dict):
        jobs = {}
    for job_name, job in jobs.items():
        if not isinstance(job, dict):
            continue
        steps = job.get("steps") or []
        script = "\n".join(str(s.get("run", "")) for s in steps if isinstance(s, dict))
        versions = installed_versions(script)
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
            for tokens in commands(run):
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
    return uses, pythons, nodes


class GitHubActions:
    """Reads `.github/workflows/*.yml`."""

    name = "GitHub Actions"

    def workflow_dir(self, root: Path) -> Path:
        return root / ".github" / "workflows"

    def detect(self, root: Path) -> bool:
        directory = self.workflow_dir(root)
        return directory.is_dir() and any(directory.glob("*.y*ml"))

    def parse(self, root: Path) -> CiFacts:
        directory = self.workflow_dir(root)
        facts = CiFacts(provider=self.name)
        text = ""
        for path in sorted(directory.glob("*.y*ml")):
            uses, pythons, nodes = parse_workflow(path)
            facts.uses.extend(uses)
            facts.pythons |= pythons
            facts.nodes |= nodes
            text += path.read_text(encoding="utf-8") + "\n"
        facts.runs_precommit, facts.precommit_all_files = precommit_invocation(
            text, official_action="pre-commit/action" in text
        )
        return facts
