#!/usr/bin/env python3
"""Reproduce Experiment 1 — the routing-policy comparison."""

from _bootstrap import add_src_to_path

add_src_to_path()

from orchestratebench.cli.reproduce_exp1 import main


if __name__ == "__main__":
    raise SystemExit(main())
