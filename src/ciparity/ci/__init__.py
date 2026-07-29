"""CI providers.

Every provider turns pipeline files into the same shape, a `CiFacts`, so the
comparison code never has to know which CI system a repository uses. Adding a
provider means writing one `detect`/`parse` pair and listing it in `PROVIDERS`.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from ..model import CiFacts
from . import github


class Provider(Protocol):
    name: str

    def detect(self, root: Path) -> bool: ...

    def parse(self, root: Path) -> CiFacts: ...


PROVIDERS: tuple[Provider, ...] = (github.GitHubActions(),)


def collect(root: Path) -> list[CiFacts]:
    """Parse every CI provider present in the checkout."""
    return [p.parse(root) for p in PROVIDERS if p.detect(root)]


__all__ = ["PROVIDERS", "CiFacts", "Provider", "collect"]
