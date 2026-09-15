#!/usr/bin/env python3
"""Merge and sort time-of-day quote buckets without changing quote order."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

TIME_KEY = re.compile(r"^(?:[01][0-9]|2[0-3]):[0-5][0-9]$")
DEFAULT_FILE = Path(__file__).parents[1] / "time_of_day_quotes_with_bold.json"


def merge_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    """Preserve append-only edits by merging duplicate array-valued keys."""
    result: dict[str, object] = {}
    for key, value in pairs:
        if key not in result:
            result[key] = value
            continue
        if isinstance(result[key], list) and isinstance(value, list):
            result[key].extend(value)
            continue
        raise ValueError(f"duplicate JSON key cannot be merged: {key}")
    return result


def format_file(path: Path) -> tuple[str, str]:
    original = path.read_text(encoding="utf-8")
    try:
        data = json.loads(original, object_pairs_hook=merge_duplicate_keys)
    except json.JSONDecodeError as error:
        raise ValueError(f"{path}: invalid JSON: {error}") from error

    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected a top-level JSON object")

    invalid_keys = [key for key in data if not isinstance(key, str) or not TIME_KEY.fullmatch(key)]
    if invalid_keys:
        raise ValueError(f"{path}: invalid time key(s): {', '.join(map(str, invalid_keys))}")

    formatted_data = {key: data[key] for key in sorted(data)}
    formatted = json.dumps(formatted_data, ensure_ascii=False, indent=2) + "\n"
    return original, formatted


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file", type=Path, default=DEFAULT_FILE)
    parser.add_argument("--check", action="store_true", help="fail instead of modifying the file")
    args = parser.parse_args()

    try:
        original, formatted = format_file(args.file)
    except (OSError, ValueError) as error:
        print(error, file=sys.stderr)
        return 1

    if original == formatted:
        print(f"{args.file}: already formatted")
        return 0

    if args.check:
        print(f"{args.file}: needs formatting; run python3 {Path(__file__).resolve()}", file=sys.stderr)
        return 1

    args.file.write_text(formatted, encoding="utf-8")
    print(f"formatted {args.file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
