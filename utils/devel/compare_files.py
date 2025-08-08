#!/usr/bin/env python

# Copyright (C) 2025 Roberto Rossini <roberros@uio.no>
#
# SPDX-License-Identifier: MIT


import argparse
import pathlib
import sys


def make_cli() -> argparse.ArgumentParser:
    cli = argparse.ArgumentParser()

    cli.add_argument(
        "files",
        nargs=2,
        type=pathlib.Path,
        help="Path to two files to be compared.",
    )

    return cli


def main() -> int:
    args = make_cli().parse_args()

    f1, f2 = args.files

    if f1.resolve() == f2.resolve():
        print("files are identical!", file=sys.stderr)
        return 0

    size1 = f1.stat().st_size
    size2 = f2.stat().st_size

    if size1 != size2:
        print(f"file {f1} and {f2} have different sizes: expected {size1}, found {size2}", file=sys.stderr)
        return 1

    if f1.read_text() != f2.read_text():
        print(f"file {f1} and {f2} have different content", file=sys.stderr)
        return 1

    print("files are identical!", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
