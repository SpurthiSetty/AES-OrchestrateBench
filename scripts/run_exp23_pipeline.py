#!/usr/bin/env python3
"""Run Exp 2/3 end-to-end from one command."""

from _bootstrap import add_src_to_path

add_src_to_path()

from orchestratebench.cli.run_exp23_pipeline import main


if __name__ == "__main__":
    raise SystemExit(main())
