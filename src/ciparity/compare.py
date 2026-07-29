"""Compare pre-commit hooks with CI steps."""

from __future__ import annotations

from pathlib import Path

from .ci import collect
from .model import CiFacts, Finding, Fix, PreCommitFacts, Report, ToolUse
from .precommit import parse_precommit
from .tools import KNOWN_COMMANDS

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

# Runners that hide the real commands behind a task definition.
TASK_RUNNERS: frozenset[str] = frozenset({"tox", "nox", "hatch", "make", "just", "invoke"})

# Tools nobody sensibly runs as a pre-commit hook.
CI_ONLY: frozenset[str] = frozenset({"pytest", "coverage", "tox", "nox"})


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


def _build_fix(uses: list[ToolUse], ci_versions: set[str]) -> Fix | None:
    """Describe how to move a hook rev onto the version CI already uses."""
    if len(ci_versions) != 1:
        return None
    target = next(iter(ci_versions))
    revs = {u.raw_rev for u in uses if u.repo and u.raw_rev and u.version}
    repos = {u.repo for u in uses if u.repo and u.raw_rev and u.version}
    if len(revs) != 1 or len(repos) != 1:
        return None
    current = next(iter(revs))
    repo = next(iter(repos))
    assert current is not None and repo is not None
    new = f"v{target}" if current.startswith("v") else target
    if new == current:
        return None
    return Fix(repo=repo, current_rev=current, new_rev=new)


def _merge(facts: list[CiFacts]) -> CiFacts:
    merged = CiFacts(provider=", ".join(f.provider for f in facts))
    for facts_item in facts:
        merged.uses.extend(facts_item.uses)
        merged.pythons |= facts_item.pythons
        merged.nodes |= facts_item.nodes
        merged.runs_precommit = merged.runs_precommit or facts_item.runs_precommit
        merged.precommit_all_files = merged.precommit_all_files and facts_item.precommit_all_files
        merged.notes.extend(facts_item.notes)
    return merged


def _runtime_finding(kind: str, name: str, pinned: str, ci_versions: set[str]) -> Finding | None:
    if not pinned or not ci_versions:
        return None
    if any(v.startswith(pinned) for v in ci_versions):
        return None
    return Finding(
        kind=kind,  # type: ignore[arg-type]
        tool=name,
        detail=f"pre-commit pins a {name} version CI never sets up",
        pre_commit=pinned,
        ci=", ".join(sorted(ci_versions)),
    )


def _tool_findings(
    pre: PreCommitFacts, ci: CiFacts, ignore: set[str], delegated: bool
) -> list[Finding]:
    findings: list[Finding] = []
    pre_groups = _by_tool(pre.uses)
    ci_groups = _by_tool(ci.uses)

    for tool in sorted(set(pre_groups) | set(ci_groups)):
        if tool in ignore or tool not in KNOWN_COMMANDS:
            continue
        in_pre = tool in pre_groups
        in_ci = tool in ci_groups

        if in_pre and not in_ci and not delegated:
            findings.append(
                Finding(
                    kind="missing-in-ci",
                    tool=tool,
                    detail="runs in pre-commit but no CI step runs it",
                    pre_commit=pre_groups[tool][0].where(),
                )
            )
            continue
        if in_ci and not in_pre and tool not in CI_ONLY:
            findings.append(
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
            findings.append(
                Finding(
                    kind="version",
                    tool=tool,
                    detail="pinned to different versions",
                    pre_commit=", ".join(sorted(pre_versions)),
                    ci=", ".join(sorted(ci_versions)),
                    fix=_build_fix(pre_groups[tool], ci_versions),
                )
            )

        pre_flags = _real_flags(pre_groups[tool])
        ci_flags = _real_flags(ci_groups[tool])
        if pre_flags != ci_flags:
            findings.append(
                Finding(
                    kind="args",
                    tool=tool,
                    detail="different arguments",
                    pre_commit=" ".join(sorted(pre_flags - ci_flags)) or "-",
                    ci=" ".join(sorted(ci_flags - pre_flags)) or "-",
                )
            )
    return findings


def compare(root: Path, ignore: set[str] | None = None) -> Report:
    """Build a parity report for a repository checkout."""
    ignore = {i.strip() for i in (ignore or set()) if i.strip()}
    config = root / ".pre-commit-config.yaml"

    pre = parse_precommit(config) if config.exists() else PreCommitFacts()
    provider_facts = collect(root)
    ci = _merge(provider_facts)

    report = Report(
        pre_commit_tools=pre.uses,
        ci_tools=ci.uses,
        providers=[f.provider for f in provider_facts],
    )
    if not config.exists() or not provider_facts:
        return report

    report.notes.extend(ci.notes)
    delegated = pre.uses_precommit_ci or ci.runs_precommit
    if pre.uses_precommit_ci:
        report.notes.append("pre-commit.ci is configured, so hooks run on every pull request.")
    elif ci.runs_precommit:
        report.notes.append("A CI job runs pre-commit itself, so hooks cannot go missing in CI.")

    runners = sorted(TASK_RUNNERS & {u.name for u in ci.uses})
    if runners:
        delegated = True
        report.notes.append(
            f"CI calls {', '.join(runners)}, whose steps are defined elsewhere. "
            "Checks hidden inside them are invisible here."
        )
    if pre.uses and not ci.uses and not delegated:
        delegated = True
        report.notes.append(
            "No recognised tool call was found in any pipeline. "
            "This is a blind spot, not a clean bill of health."
        )
    if any(u.repo and u.raw_rev and not u.version for u in pre.uses):
        report.notes.append(
            "Some hooks are pinned to a commit SHA, so their version cannot be compared."
        )

    report.findings.extend(_tool_findings(pre, ci, ignore, delegated))

    if ci.runs_precommit and not ci.precommit_all_files and "scope" not in ignore:
        report.findings.append(
            Finding(
                kind="scope",
                tool="pre-commit",
                detail="CI runs pre-commit without --all-files, so it only sees changed files",
                ci="pre-commit run",
                pre_commit="-",
            )
        )

    if "python" not in ignore and pre.python:
        finding = _runtime_finding("python", "python", pre.python, ci.pythons)
        if finding:
            report.findings.append(finding)
    if "node" not in ignore and pre.node:
        finding = _runtime_finding("node", "node", pre.node, ci.nodes)
        if finding:
            report.findings.append(finding)

    return report
