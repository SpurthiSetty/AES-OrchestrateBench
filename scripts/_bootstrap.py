"""Helpers for running repository script wrappers from a fresh clone."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"


def add_src_to_path() -> None:
    """Make the local package importable for direct ``python scripts/*.py`` usage."""
    src = str(SRC)
    if src not in sys.path:
        sys.path.insert(0, src)
