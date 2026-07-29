"""Apply fixes to .pre-commit-config.yaml.

The file is edited as text, one `rev:` line at a time, so comments, key order and
formatting survive untouched. CI is treated as the source of truth: it is the
version every contributor and reviewer actually sees.
"""

from __future__ import annotations

import difflib
import re
from dataclasses import dataclass
from pathlib import Path

from .model import Fix, Report

_REPO_LINE = re.compile(r"^\s*-?\s*repo:\s*(?P<value>\S+)\s*(?:#.*)?$")
_REV_LINE = re.compile(r"^(?P<indent>\s*)rev:\s*(?P<quote>['\"]?)(?P<value>[^'\"\s#]+)(?P=quote)")


@dataclass
class FixResult:
    applied: list[Fix]
    skipped: list[Fix]
    diff: str
    new_text: str


def _rewrite(text: str, fixes: list[Fix]) -> tuple[str, list[Fix], list[Fix]]:
    wanted = {fix.repo: fix for fix in fixes}
    applied: list[Fix] = []
    lines = text.splitlines(keepends=True)
    current: str | None = None

    for index, line in enumerate(lines):
        repo_match = _REPO_LINE.match(line.rstrip("\n"))
        if repo_match:
            current = repo_match.group("value").strip("'\"")
            continue
        if current is None or current not in wanted:
            continue
        rev_match = _REV_LINE.match(line.rstrip("\n"))
        if not rev_match:
            continue
        fix = wanted[current]
        if rev_match.group("value") != fix.current_rev:
            continue
        start, end = rev_match.span("value")
        lines[index] = line[:start] + fix.new_rev + line[end:]
        applied.append(fix)
        current = None

    skipped = [f for f in fixes if f not in applied]
    return "".join(lines), applied, skipped


def plan(root: Path, report: Report) -> FixResult:
    """Compute the edited file without writing anything."""
    path = root / ".pre-commit-config.yaml"
    original = path.read_text(encoding="utf-8")
    fixes = [f.fix for f in report.findings if f.fix is not None]
    new_text, applied, skipped = _rewrite(original, fixes)
    diff = "".join(
        difflib.unified_diff(
            original.splitlines(keepends=True),
            new_text.splitlines(keepends=True),
            fromfile=".pre-commit-config.yaml",
            tofile=".pre-commit-config.yaml",
        )
    )
    return FixResult(applied=applied, skipped=skipped, diff=diff, new_text=new_text)


def apply(root: Path, result: FixResult) -> None:
    """Write a computed plan to disk."""
    if not result.applied:
        return
    (root / ".pre-commit-config.yaml").write_text(result.new_text, encoding="utf-8")
