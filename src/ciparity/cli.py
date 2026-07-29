"""Command line interface."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .compare import compare
from .model import Report

KIND_LABEL = {
    "missing-in-ci": "not in CI",
    "missing-in-pre-commit": "not in pre-commit",
    "version": "version differs",
    "args": "arguments differ",
    "python": "python differs",
}


def _text(report: Report, root: Path) -> str:
    if not report.pre_commit_tools and not report.ci_tools:
        return f"No .pre-commit-config.yaml and no workflows found in {root}."
    lines = [
        f"pre-commit hooks: {len(report.pre_commit_tools)}   CI steps: {len(report.ci_tools)}",
        "",
    ]
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
    lines.append("")
    lines.extend(f"note: {n}" for n in report.notes)
    lines.append(f"{len(report.findings)} difference(s).")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ciparity",
        description="Report where pre-commit hooks and GitHub Actions steps disagree.",
    )
    parser.add_argument("path", nargs="?", default=".", help="repository root (default: .)")
    parser.add_argument("--json", action="store_true", help="machine readable output")
    parser.add_argument(
        "--ignore",
        default="",
        help="comma separated tool names to skip, for example: pytest,codespell",
    )
    parser.add_argument(
        "--exit-zero", action="store_true", help="always exit 0, even with findings"
    )
    parser.add_argument("--version", action="version", version=f"ciparity {__version__}")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(args.path).resolve()
    if not root.is_dir():
        print(f"ciparity: {root} is not a directory", file=sys.stderr)
        return 2

    report = compare(root, ignore=set(args.ignore.split(",")))
    if args.json:
        payload = {
            "findings": [f.as_dict() for f in report.findings],
            "pre_commit_tools": sorted({t.name for t in report.pre_commit_tools}),
            "ci_tools": sorted({t.name for t in report.ci_tools}),
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
