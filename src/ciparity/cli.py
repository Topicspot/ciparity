"""Command line interface."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from . import fix as fixer
from .compare import compare
from .model import Report

KIND_LABEL = {
    "missing-in-ci": "not in CI",
    "missing-in-pre-commit": "not in pre-commit",
    "version": "version differs",
    "args": "arguments differ",
    "python": "python differs",
    "node": "node differs",
    "scope": "narrower in CI",
}


def _text(report: Report, root: Path) -> str:
    if not report.pre_commit_tools and not report.ci_tools:
        return f"No .pre-commit-config.yaml and no CI pipeline found in {root}."
    header = f"pre-commit hooks: {len(report.pre_commit_tools)}   CI steps: {len(report.ci_tools)}"
    if report.providers:
        header += f"   ci: {', '.join(report.providers)}"
    lines = [header, ""]
    if report.ok:
        lines.append("No differences found.")
        lines.extend(f"note: {n}" for n in report.notes)
        return "\n".join(lines)

    width = max(len(f.tool) for f in report.findings)
    for finding in report.findings:
        lines.append(f"{finding.tool.ljust(width)}  {KIND_LABEL[finding.kind]}: {finding.detail}")
        if finding.pre_commit:
            lines.append(f"{' ' * width}    pre-commit: {finding.pre_commit}")
        if finding.ci:
            lines.append(f"{' ' * width}    ci:         {finding.ci}")
        if finding.fix is not None:
            lines.append(
                f"{' ' * width}    fix:        rev {finding.fix.current_rev}"
                f" -> {finding.fix.new_rev}"
            )
    lines.append("")
    lines.extend(f"note: {n}" for n in report.notes)
    fixable = len(report.fixable)
    lines.append(f"{len(report.findings)} difference(s).")
    if fixable:
        lines.append(f"{fixable} can be fixed automatically: ciparity --fix")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ciparity",
        description="Report where pre-commit hooks and CI steps disagree.",
    )
    parser.add_argument("path", nargs="?", default=".", help="repository root (default: .)")
    parser.add_argument("--json", action="store_true", help="machine readable output")
    parser.add_argument(
        "--ignore",
        default="",
        help="comma separated tool names to skip, for example: pytest,codespell",
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="update hook revs in .pre-commit-config.yaml to the versions CI uses",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="with --fix, print the diff and change nothing"
    )
    parser.add_argument(
        "--exit-zero", action="store_true", help="always exit 0, even with findings"
    )
    parser.add_argument("--version", action="version", version=f"ciparity {__version__}")
    return parser


def _run_fix(root: Path, report: Report, dry_run: bool) -> int:
    result = fixer.plan(root, report)
    if not result.applied:
        print("Nothing to fix automatically. Version drift is the only fixable difference.")
        return 0 if report.ok else 1
    print(result.diff, end="")
    if dry_run:
        print(f"\n{len(result.applied)} change(s) not written (--dry-run).")
        return 1
    fixer.apply(root, result)
    for fix in result.applied:
        print(f"\n{fix.repo}: rev {fix.current_rev} -> {fix.new_rev}")
    remaining = len(report.findings) - len(result.applied)
    print(f"\nWrote .pre-commit-config.yaml. {len(result.applied)} fixed, {remaining} left.")
    return 0 if remaining == 0 else 1


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(args.path).resolve()
    if not root.is_dir():
        print(f"ciparity: {root} is not a directory", file=sys.stderr)
        return 2
    if args.dry_run and not args.fix:
        print("ciparity: --dry-run only makes sense with --fix", file=sys.stderr)
        return 2

    report = compare(root, ignore=set(args.ignore.split(",")))

    if args.fix:
        if not (root / ".pre-commit-config.yaml").exists():
            print("ciparity: no .pre-commit-config.yaml to fix", file=sys.stderr)
            return 2
        code = _run_fix(root, report, args.dry_run)
        return 0 if args.exit_zero else code

    if args.json:
        payload = {
            "findings": [f.as_dict() for f in report.findings],
            "pre_commit_tools": sorted({t.name for t in report.pre_commit_tools}),
            "ci_tools": sorted({t.name for t in report.ci_tools}),
            "providers": report.providers,
            "notes": report.notes,
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(_text(report, root))

    if args.exit_zero or report.ok:
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
