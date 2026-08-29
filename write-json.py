#!/usr/bin/env python3
"""Write stdin to a JSON file, creating parent directories."""

import pathlib
import sys


def main(argv: list[str]) -> int:
    if len(argv) < 1 or len(argv) > 2:
        sys.stderr.write("usage: write-json.py PATH [JSON]\n")
        return 2
    path = pathlib.Path(argv[0])
    if path.suffix != ".json":
        sys.stderr.write("write-json: path must end with .json\n")
        return 2
    data = argv[1] if len(argv) == 2 else sys.stdin.read()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(data)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
