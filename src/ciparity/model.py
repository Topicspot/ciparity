"""Shared data types."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

Source = Literal["pre-commit", "ci"]


@dataclass(frozen=True)
class ToolUse:
    """One observed use of a tool, in pre-commit or in a CI workflow."""

    name: str
    version: str | None
    args: tuple[str, ...]
    source: Source
    location: str

    def where(self) -> str:
        return f"{self.location}"


@dataclass
class Finding:
    """A difference worth reporting."""

    kind: Literal["missing-in-ci", "missing-in-pre-commit", "version", "args", "python"]
    tool: str
    detail: str
    pre_commit: str | None = None
    ci: str | None = None

    def as_dict(self) -> dict[str, str | None]:
        return {
            "kind": self.kind,
            "tool": self.tool,
            "detail": self.detail,
            "pre_commit": self.pre_commit,
            "ci": self.ci,
        }


@dataclass
class Report:
    findings: list[Finding] = field(default_factory=list)
    pre_commit_tools: list[ToolUse] = field(default_factory=list)
    ci_tools: list[ToolUse] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.findings
