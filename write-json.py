#!/usr/bin/env python3
"""Atomically write JSON file(s), creating parent directories."""

from __future__ import annotations

import os
import pathlib
import sys
import tempfile

# Keep argv + disk payloads bounded (ARG_MAX and agent DoS).
MAX_BYTES = 1_500_000


def atomic_write(path: pathlib.Path, data: str) -> None:
    encoded = data.encode("utf-8")
    if len(encoded) > MAX_BYTES:
        raise ValueError(f"payload exceeds {MAX_BYTES} bytes")
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=str(path.parent),
    )
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_name, path)
    except Exception:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


def main(argv: list[str]) -> int:
    if len(argv) < 1:
        sys.stderr.write("usage: write-json.py PATH [JSON] [PATH JSON ...]\n")
        return 2

    # Single path: optional JSON arg, else stdin.
    if len(argv) == 1:
        path = pathlib.Path(argv[0])
        if path.suffix != ".json":
            sys.stderr.write("write-json: path must end with .json\n")
            return 2
        data = sys.stdin.read()
        try:
            atomic_write(path, data)
        except ValueError as exc:
            sys.stderr.write(f"write-json: {exc}\n")
            return 2
        except OSError as exc:
            sys.stderr.write(f"write-json: {exc}\n")
            return 1
        return 0

    if len(argv) == 2:
        path = pathlib.Path(argv[0])
        if path.suffix != ".json":
            sys.stderr.write("write-json: path must end with .json\n")
            return 2
        try:
            atomic_write(path, argv[1])
        except ValueError as exc:
            sys.stderr.write(f"write-json: {exc}\n")
            return 2
        except OSError as exc:
            sys.stderr.write(f"write-json: {exc}\n")
            return 1
        return 0

    # Batch: PATH JSON PATH JSON ...
    if len(argv) % 2 != 0:
        sys.stderr.write("usage: write-json.py PATH JSON [PATH JSON ...]\n")
        return 2
    for i in range(0, len(argv), 2):
        path = pathlib.Path(argv[i])
        if path.suffix != ".json":
            sys.stderr.write(f"write-json: path must end with .json: {path}\n")
            return 2
        try:
            atomic_write(path, argv[i + 1])
        except ValueError as exc:
            sys.stderr.write(f"write-json: {exc}\n")
            return 2
        except OSError as exc:
            sys.stderr.write(f"write-json: {exc}\n")
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
