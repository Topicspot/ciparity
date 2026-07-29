from __future__ import annotations

from pathlib import Path

from ciparity.cli import main
from ciparity.compare import compare

FIXTURES = Path(__file__).parent / "fixtures"


def kinds(root: Path) -> dict[str, str]:
    return {f.tool: f.kind for f in compare(root).findings}


def test_drift_repo_reports_every_difference() -> None:
    found = kinds(FIXTURES / "drift")
    assert found["ruff"] == "version"
    assert found["mypy"] == "args"
    assert found["vulture"] == "missing-in-pre-commit"
    assert "pytest" not in found  # test runners are never hooks
    assert found["python"] == "python"


def test_hygiene_hooks_are_not_reported() -> None:
    report = compare(FIXTURES / "drift")
    reported = {f.tool for f in report.findings}
    assert "trailing-whitespace" not in reported
    assert "end-of-file-fixer" not in reported


def test_matching_repo_is_clean() -> None:
    report = compare(FIXTURES / "clean")
    assert report.ok, [f.as_dict() for f in report.findings]


def test_ci_running_pre_commit_is_parity() -> None:
    report = compare(FIXTURES / "delegated")
    assert report.ok, [f.as_dict() for f in report.findings]


def test_missing_config_is_not_an_error(tmp_path: Path) -> None:
    report = compare(tmp_path)
    assert report.ok
    assert report.pre_commit_tools == []


def test_cli_exit_codes(capsys: object) -> None:
    assert main([str(FIXTURES / "clean")]) == 0
    assert main([str(FIXTURES / "drift")]) == 1
    assert main([str(FIXTURES / "drift"), "--exit-zero"]) == 0
    assert main([str(FIXTURES / "drift"), "--json"]) == 1
    assert main([str(FIXTURES / "drift"), "--ignore", "ruff,mypy,vulture,python"]) == 0


def test_task_runner_in_ci_suppresses_missing_and_explains(tmp_path: Path) -> None:
    (tmp_path / ".pre-commit-config.yaml").write_text(
        "repos:\n"
        "  - repo: https://github.com/astral-sh/ruff-pre-commit\n"
        "    rev: v0.6.2\n"
        "    hooks:\n"
        "      - id: ruff\n"
    )
    workflows = tmp_path / ".github" / "workflows"
    workflows.mkdir(parents=True)
    (workflows / "ci.yml").write_text("jobs:\n  test:\n    steps:\n      - run: tox run\n")
    report = compare(tmp_path)
    assert report.ok
    assert any("tox" in note for note in report.notes)


def test_frozen_sha_rev_is_not_compared_as_a_version(tmp_path: Path) -> None:
    (tmp_path / ".pre-commit-config.yaml").write_text(
        "repos:\n"
        "  - repo: https://github.com/astral-sh/ruff-pre-commit\n"
        "    rev: 5e2fb545eba1ea9dc051f6f962d52fe8f76a9794\n"
        "    hooks:\n"
        "      - id: ruff-check\n"
    )
    workflows = tmp_path / ".github" / "workflows"
    workflows.mkdir(parents=True)
    (workflows / "ci.yml").write_text(
        "jobs:\n  lint:\n    steps:\n"
        "      - run: pip install ruff==0.6.2\n      - run: ruff check .\n"
    )
    assert compare(tmp_path).ok


def test_precommit_ci_block_is_treated_as_parity(tmp_path: Path) -> None:
    (tmp_path / ".pre-commit-config.yaml").write_text(
        "ci:\n  autofix_prs: true\n"
        "repos:\n"
        "  - repo: https://github.com/astral-sh/ruff-pre-commit\n"
        "    rev: v0.6.2\n"
        "    hooks:\n"
        "      - id: ruff\n"
    )
    workflows = tmp_path / ".github" / "workflows"
    workflows.mkdir(parents=True)
    (workflows / "ci.yml").write_text("jobs:\n  t:\n    steps:\n      - run: echo hi\n")
    report = compare(tmp_path)
    assert report.ok
    assert any("pre-commit.ci" in note for note in report.notes)


def test_ci_running_pre_commit_on_changed_files_only_is_reported() -> None:
    report = compare(FIXTURES / "scoped")
    assert [f.kind for f in report.findings] == ["scope"]


def test_node_version_drift_is_reported() -> None:
    report = compare(FIXTURES / "node")
    assert [(f.tool, f.kind) for f in report.findings] == [("node", "node")]


def test_version_findings_carry_a_fix() -> None:
    report = compare(FIXTURES / "drift")
    version = next(f for f in report.findings if f.kind == "version")
    assert version.fix is not None
    assert version.fix.current_rev == "v0.5.0"
    assert version.fix.new_rev == "v0.6.2"
    assert [f.kind for f in report.fixable] == ["version"]


def test_providers_are_listed() -> None:
    assert compare(FIXTURES / "clean").providers == ["GitHub Actions"]
