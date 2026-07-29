"""The CLI version must match the version declared in pyproject.toml."""

import pathlib
import re

import ciparity


def test_version_matches_pyproject() -> None:
    pyproject = pathlib.Path(__file__).resolve().parents[1] / "pyproject.toml"
    match = re.search(r'^version = "([^"]+)"', pyproject.read_text(), re.MULTILINE)
    assert match is not None
    assert ciparity.__version__ == match.group(1)
