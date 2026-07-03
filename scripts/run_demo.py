#!/usr/bin/env python3
"""Demo: compare FixedPolicy vs HeuristicPolicy on 20 tasks."""

from _bootstrap import add_src_to_path

add_src_to_path()

from orchestratebench.cli.run_demo import main


if __name__ == "__main__":
    raise SystemExit(main())
