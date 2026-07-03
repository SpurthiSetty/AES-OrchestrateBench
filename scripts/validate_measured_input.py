#!/usr/bin/env python3
"""Validate collaborative measured Exp 2/3 inputs before running the analyzers."""

from _bootstrap import add_src_to_path

add_src_to_path()

from orchestratebench.cli.validate_measured_input import main


if __name__ == "__main__":
    raise SystemExit(main())
