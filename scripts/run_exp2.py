#!/usr/bin/env python3
"""Run Experiment 2 — failure injection and per-mode recovery, across policies."""

from _bootstrap import add_src_to_path

add_src_to_path()

from orchestratebench.cli.run_exp2 import main


if __name__ == "__main__":
    raise SystemExit(main())
