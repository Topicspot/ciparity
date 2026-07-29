from __future__ import annotations

import shutil
from pathlib import Path

from ciparity.cli import main
from ciparity.compare import compare
from ciparity.fix import plan

FIXTURES = Path(__file__).parent / "fixtures"


def _copy(tmp_path: Path, name: str) -> Path:
    target = tmp_path / name
    shutil.copytree(FIXTURES / name, target)
    return target


def test_fix_rewrites_the_rev_to_the_ci_version(tmp_path: Path) -> None:
    root = _copy(tmp_path, "drift")
    assert main([str(root), "--fix"]) == 1  # other differences remain

    text = (root / ".pre-commit-config.yaml").read_text(encoding="utf-8")
    assert "rev: v0.6.2" in text
    assert "rev: v0.5.0" not in text
    assert compare(root).findings  # argument drift is not auto-fixable


def test_fix_keeps_comments_and_key_order(tmp_path: Path) -> None:
    root = _copy(tmp_path, "drift")
    config = root / ".pre-commit-config.yaml"
    config.write_text(
        "repos:\n"
        "  # linting, keep in step with CI\n"
        "  - repo: https://github.com/astral-sh/ruff-pre-commit\n"
        "    rev: v0.5.0  # bumped by hand\n"
        "    hooks:\n"
        "      - id: ruff\n",
        encoding="utf-8",
    )
    main([str(root), "--fix"])

    text = config.read_text(encoding="utf-8")
    assert "# linting, keep in step with CI" in text
    assert "rev: v0.6.2  # bumped by hand" in text


def test_dry_run_writes_nothing(tmp_path: Path) -> None:
    root = _copy(tmp_path, "drift")
    before = (root / ".pre-commit-config.yaml").read_text(encoding="utf-8")
    assert main([str(root), "--fix", "--dry-run"]) == 1
    assert (root / ".pre-commit-config.yaml").read_text(encoding="utf-8") == before


def test_plan_reports_the_diff(tmp_path: Path) -> None:
    root = _copy(tmp_path, "drift")
    result = plan(root, compare(root))
    assert "-    rev: v0.5.0" in result.diff
    assert "+    rev: v0.6.2" in result.diff
    assert len(result.applied) == 1
    assert not result.skipped


def test_clean_repo_has_nothing_to_fix(tmp_path: Path) -> None:
    root = _copy(tmp_path, "clean")
    assert main([str(root), "--fix"]) == 0


def test_dry_run_without_fix_is_an_error(tmp_path: Path) -> None:
    assert main([str(FIXTURES / "clean"), "--dry-run"]) == 2
