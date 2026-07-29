"""Shared data types."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

Source = Literal["pre-commit", "ci"]

FindingKind = Literal[
    "missing-in-ci",
    "missing-in-pre-commit",
    "version",
    "args",
    "python",
    "node",
    "scope",
]


@dataclass(frozen=True)
class ToolUse:
    """One observed use of a tool, in pre-commit or in a CI pipeline."""

    name: str
    version: str | None
    args: tuple[str, ...]
    source: Source
    location: str
    # Only set for pre-commit hooks, and only when the rev is a readable version.
    repo: str | None = None
    raw_rev: str | None = None

    def where(self) -> str:
        return self.location


@dataclass
class Fix:
    """A change ciparity knows how to apply to .pre-commit-config.yaml."""

    repo: str
    current_rev: str
    new_rev: str


@dataclass
class Finding:
    """A difference worth reporting."""

    kind: FindingKind
    tool: str
    detail: str
    pre_commit: str | None = None
    ci: str | None = None
    fix: Fix | None = None

    def as_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "kind": self.kind,
            "tool": self.tool,
            "detail": self.detail,
            "pre_commit": self.pre_commit,
            "ci": self.ci,
            "fixable": self.fix is not None,
        }
        if self.fix is not None:
            payload["fix"] = {
                "repo": self.fix.repo,
                "from": self.fix.current_rev,
                "to": self.fix.new_rev,
            }
        return payload


@dataclass
class CiFacts:
    """What one CI provider says about a repository."""

    provider: str
    uses: list[ToolUse] = field(default_factory=list)
    pythons: set[str] = field(default_factory=set)
    nodes: set[str] = field(default_factory=set)
    runs_precommit: bool = False
    precommit_all_files: bool = True


@dataclass
class PreCommitFacts:
    """What .pre-commit-config.yaml says."""

    uses: list[ToolUse] = field(default_factory=list)
    python: str | None = None
    node: str | None = None
    uses_precommit_ci: bool = False


@dataclass
class Report:
    findings: list[Finding] = field(default_factory=list)
    pre_commit_tools: list[ToolUse] = field(default_factory=list)
    ci_tools: list[ToolUse] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    providers: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.findings

    @property
    def fixable(self) -> list[Finding]:
        return [f for f in self.findings if f.fix is not None]
