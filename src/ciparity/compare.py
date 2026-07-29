"""Compare pre-commit hooks with CI steps."""

from __future__ import annotations

from pathlib import Path

from .model import Finding, Report, ToolUse
from .precommit import parse_precommit
from .tools import KNOWN_COMMANDS
from .workflows import parse_workflows

# Flags that describe how a tool is run, not what it checks. A difference here is
# expected: pre-commit fixes files, CI only reports.
MODE_FLAGS: frozenset[str] = frozenset(
    {
        "--fix",
        "--no-fix",
        "--check",
        "--diff",
        "--quiet",
        "-q",
        "--verbose",
        "-v",
        "--all-files",
        "-a",
        "--color",
        "--no-color",
        "--force-exclude",
        "--show-fixes",
        "--exit-non-zero-on-fix",
        "--output-format",
        "--no-cache",
        "--cache-dir",
    }
)


def _by_tool(uses: list[ToolUse]) -> dict[str, list[ToolUse]]:
    grouped: dict[str, list[ToolUse]] = {}
    for use in uses:
        grouped.setdefault(use.name, []).append(use)
    return grouped


def _versions(uses: list[ToolUse]) -> set[str]:
    return {u.version for u in uses if u.version}


def _real_flags(uses: list[ToolUse]) -> set[str]:
    flags: set[str] = set()
    for use in uses:
        flags |= {f for f in use.args if f.split("=")[0] not in MODE_FLAGS}
    return flags


# Runners that hide the real commands behind a task definition.
TASK_RUNNERS: frozenset[str] = frozenset({"tox", "nox", "hatch", "make", "just", "invoke"})

# Tools nobody sensibly runs as a pre-commit hook.
CI_ONLY: frozenset[str] = frozenset({"pytest", "coverage", "tox", "nox"})


def _ci_runs_precommit(directory: Path) -> bool:
    for path in sorted(directory.glob("*.y*ml")):
        text = path.read_text(encoding="utf-8")
        if "pre-commit run" in text or "pre-commit/action" in text:
            return True
    return False


def compare(root: Path, ignore: set[str] | None = None) -> Report:
    """Build a parity report for a repository checkout."""
    ignore = {i.strip() for i in (ignore or set()) if i.strip()}
    config = root / ".pre-commit-config.yaml"
    workflow_dir = root / ".github" / "workflows"

    if config.exists():
        pre_uses, pre_python, precommit_ci = parse_precommit(config)
    else:
        pre_uses, pre_python, precommit_ci = [], None, False
    if workflow_dir.is_dir():
        ci_uses, ci_pythons = parse_workflows(workflow_dir)
    else:
        ci_uses, ci_pythons = [], set()

    report = Report(pre_commit_tools=pre_uses, ci_tools=ci_uses)
    if not config.exists() or not workflow_dir.is_dir():
        return report

    pre_groups = _by_tool(pre_uses)
    ci_groups = _by_tool(ci_uses)
    runners = sorted(TASK_RUNNERS & set(ci_groups))

    delegated = precommit_ci or _ci_runs_precommit(workflow_dir)
    if precommit_ci:
        report.notes.append("pre-commit.ci is configured, so hooks run on every pull request.")
    elif _ci_runs_precommit(workflow_dir):
        report.notes.append("A workflow runs pre-commit itself, so hooks cannot go missing in CI.")
    if runners:
        delegated = True
        report.notes.append(
            f"CI calls {', '.join(runners)}, whose steps are defined elsewhere. "
            "Checks hidden inside them are invisible here."
        )
    if pre_uses and not ci_uses:
        delegated = True
        report.notes.append(
            "No recognised tool call was found in any workflow. "
            "This is a blind spot, not a clean bill of health."
        )

    for tool in sorted(set(pre_groups) | set(ci_groups)):
        if tool in ignore or tool not in KNOWN_COMMANDS:
            continue
        in_pre = tool in pre_groups
        in_ci = tool in ci_groups

        if in_pre and not in_ci and not delegated:
            report.findings.append(
                Finding(
                    kind="missing-in-ci",
                    tool=tool,
                    detail="runs in pre-commit but no CI step runs it",
                    pre_commit=pre_groups[tool][0].where(),
                )
            )
            continue
        if in_ci and not in_pre and tool not in CI_ONLY:
            report.findings.append(
                Finding(
                    kind="missing-in-pre-commit",
                    tool=tool,
                    detail="runs in CI but is not a pre-commit hook",
                    ci=ci_groups[tool][0].where(),
                )
            )
            continue
        if not (in_pre and in_ci):
            continue

        pre_versions = _versions(pre_groups[tool])
        ci_versions = _versions(ci_groups[tool])
        if pre_versions and ci_versions and pre_versions != ci_versions:
            report.findings.append(
                Finding(
                    kind="version",
                    tool=tool,
                    detail="pinned to different versions",
                    pre_commit=", ".join(sorted(pre_versions)),
                    ci=", ".join(sorted(ci_versions)),
                )
            )

        pre_flags = _real_flags(pre_groups[tool])
        ci_flags = _real_flags(ci_groups[tool])
        if pre_flags != ci_flags:
            only_pre = sorted(pre_flags - ci_flags)
            only_ci = sorted(ci_flags - pre_flags)
            report.findings.append(
                Finding(
                    kind="args",
                    tool=tool,
                    detail="different arguments",
                    pre_commit=" ".join(only_pre) or "-",
                    ci=" ".join(only_ci) or "-",
                )
            )

    if (
        "python" not in ignore
        and pre_python
        and ci_pythons
        and not any(v.startswith(pre_python) for v in ci_pythons)
    ):
        report.findings.append(
            Finding(
                kind="python",
                tool="python",
                detail="pre-commit pins a python version CI never sets up",
                pre_commit=pre_python,
                ci=", ".join(sorted(ci_pythons)),
            )
        )

    return report
