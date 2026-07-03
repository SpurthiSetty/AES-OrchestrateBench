#!/usr/bin/env python3
"""Export publication-friendly markdown and LaTeX from Exp 2/3 summary artifacts."""

from _bootstrap import add_src_to_path

add_src_to_path()

from orchestratebench.cli.export_paper_tables import main


if __name__ == "__main__":
    raise SystemExit(main())
