"""Parse .pre-commit-config.yaml into tool uses."""

from __future__ import annotations

import re
import shlex
from pathlib import Path
from typing import Any

import yaml

from .model import PreCommitFacts, ToolUse
from .tools import canonical, from_repo


def _flags(args: Any) -> tuple[str, ...]:
    if not isinstance(args, list):
        return ()
    out = []
    for a in args:
        text = str(a)
        for token in shlex.split(text) if " " in text else [text]:
            if token.startswith("-"):
                out.append(token)
    return tuple(sorted(set(out)))


_VERSION_LIKE = re.compile(r"^v?\d[\w.+-]*$")
_SHA_LIKE = re.compile(r"^[0-9a-f]{7,40}$")


def _clean_rev(rev: Any) -> str | None:
    """Return a comparable version, or None for SHAs and moving refs."""
    if rev is None:
        return None
    text = str(rev).strip()
    if not text or text in {"HEAD", "master", "main"}:
        return None
    if _SHA_LIKE.match(text) or not _VERSION_LIKE.match(text):
        # Frozen revs are commit SHAs. The readable version only lives in a YAML
        # comment, which the parser does not keep, so there is nothing to compare.
        return None
    return text.lstrip("v")


def parse_precommit(path: Path) -> PreCommitFacts:
    """Read .pre-commit-config.yaml into facts the comparison can use."""
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        return PreCommitFacts()

    facts = PreCommitFacts(uses_precommit_ci=isinstance(data.get("ci"), dict))
    defaults = data.get("default_language_version")
    if isinstance(defaults, dict):
        if defaults.get("python"):
            facts.python = str(defaults["python"]).removeprefix("python")
        if defaults.get("node"):
            facts.node = str(defaults["node"]).lstrip("v")

    for repo_block in data.get("repos") or []:
        if not isinstance(repo_block, dict):
            continue
        repo = str(repo_block.get("repo", ""))
        raw_rev = repo_block.get("rev")
        rev = _clean_rev(raw_rev)
        repo_tool = from_repo(repo)
        for hook in repo_block.get("hooks") or []:
            if not isinstance(hook, dict):
                continue
            hook_id = str(hook.get("id", "")).strip()
            if not hook_id:
                continue
            name = canonical(hook_id)
            if repo_tool and name not in {repo_tool, f"{repo_tool}-format"}:
                name = repo_tool
            local = repo == "local"
            facts.uses.append(
                ToolUse(
                    name=name,
                    version=None if local else rev,
                    args=_flags(hook.get("args")),
                    source="pre-commit",
                    location=f"{path.name}:{hook_id}",
                    repo=None if local else repo,
                    raw_rev=None if raw_rev is None else str(raw_rev).strip(),
                )
            )
    return facts
