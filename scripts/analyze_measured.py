#!/usr/bin/env python3
"""Recompute every measured number reported in PAPER.md from committed CSVs."""

from _bootstrap import add_src_to_path

add_src_to_path()

from orchestratebench.cli.analyze_measured import main


if __name__ == "__main__":
    raise SystemExit(main())
