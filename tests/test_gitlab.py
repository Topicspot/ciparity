from __future__ import annotations

from pathlib import Path

from ciparity.ci.gitlab import GitLabCI, _runtime_version
from ciparity.compare import compare

FIXTURES = Path(__file__).parent / "fixtures"


def kinds(root: Path) -> dict[str, str]:
    return {f.tool: f.kind for f in compare(root).findings}


def test_gitlab_pipeline_is_compared_like_a_workflow() -> None:
    report = compare(FIXTURES / "gitlab")
    found = {f.tool: f.kind for f in report.findings}
    assert report.providers == ["GitLab CI"]
    assert found["ruff"] == "version"
    assert found["mypy"] == "args"
    assert found["vulture"] == "missing-in-pre-commit"
    assert found["python"] == "python"


def test_version_drift_in_gitlab_is_fixable() -> None:
    report = compare(FIXTURES / "gitlab")
    fixable = report.fixable
    assert [f.tool for f in fixable] == ["ruff"]
    assert fixable[0].fix is not None
    assert fixable[0].fix.new_rev == "v0.6.2"


def test_job_location_names_the_job() -> None:
    report = compare(FIXTURES / "gitlab")
    locations = {use.location for use in report.ci_tools}
    assert locations == {".gitlab-ci.yml:lint", ".gitlab-ci.yml:test"}


def test_default_before_script_pins_versions_for_every_job() -> None:
    facts = GitLabCI().parse(FIXTURES / "gitlab")
    versions = {use.name: use.version for use in facts.uses}
    assert versions["ruff"] == "0.6.2"
    assert versions["mypy"] == "1.10.0"


def test_hidden_template_is_not_a_job() -> None:
    facts = GitLabCI().parse(FIXTURES / "gitlab")
    assert all(":.lint_template" not in use.location for use in facts.uses)


def test_gitlab_running_pre_commit_is_parity() -> None:
    report = compare(FIXTURES / "gitlab_clean")
    assert report.ok, [f.as_dict() for f in report.findings]


def test_local_include_is_read_and_remote_include_is_admitted() -> None:
    report = compare(FIXTURES / "gitlab_include")
    tools = {use.name for use in report.ci_tools}
    assert "ruff" in tools  # defined in ci/lint.yml
    assert any("includes ciparity cannot read" in note for note in report.notes)


def test_image_tags_that_are_not_runtimes_are_ignored() -> None:
    assert _runtime_version("python:3.12-slim", "python") == "3.12"
    assert _runtime_version("registry.example.com/library/node:22-alpine", "node") == "22"
    assert _runtime_version("python:latest", "python") is None
    assert _runtime_version("golang:1.22", "python") is None
    assert _runtime_version("$IMAGE", "python") is None


def test_two_providers_are_merged_and_conflicts_are_not_auto_fixed() -> None:
    report = compare(FIXTURES / "dual")
    assert report.providers == ["GitHub Actions", "GitLab CI"]
    finding = next(f for f in report.findings if f.tool == "ruff")
    assert finding.kind == "version"
    assert finding.ci == "0.5.9, 0.6.2"
    assert finding.fix is None  # the two pipelines disagree with each other
