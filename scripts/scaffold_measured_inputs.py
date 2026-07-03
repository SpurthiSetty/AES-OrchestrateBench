#!/usr/bin/env python3
"""Create blank measured long-form files for Exp 2/3."""

from _bootstrap import add_src_to_path

add_src_to_path()

from orchestratebench.cli.scaffold_measured_inputs import main


if __name__ == "__main__":
    raise SystemExit(main())
