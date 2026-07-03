#!/usr/bin/env python3
"""Run Experiment 3 — cascade radius vs. pipeline depth and injection stage."""

from _bootstrap import add_src_to_path

add_src_to_path()

from orchestratebench.cli.run_exp3 import main


if __name__ == "__main__":
    raise SystemExit(main())
