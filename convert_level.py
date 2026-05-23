# The code is all hand-written, but comments FROM THIS POINT ON are mainly AI generated.

from __future__ import annotations

import argparse
import json
from pathlib import Path


def encode_rle_row(row: str) -> str:
    """Run-length encoding"""
    if not row:
        return row

    encoded_segments: list[str] = []
    run_char = row[0]
    run_length = 1

    for char in row[1:]:
        if char == run_char:
            run_length += 1
            continue

        encoded_segments.append(f"{run_length}{run_char}" if run_length > 1 else run_char)
        run_char = char
        run_length = 1

    encoded_segments.append(f"{run_length}{run_char}" if run_length > 1 else run_char)
    return "".join(encoded_segments)


def decode_rle_row(row: str) -> str:
    """Decode encoded row"""
    if not row or not any(char.isdigit() for char in row):
        return row

    decoded_segments: list[str] = []
    index = 0
    while index < len(row):
        if row[index].isdigit():
            count_start = index
            while index < len(row) and row[index].isdigit():
                index += 1
            if index >= len(row):
                raise ValueError(f"Invalid RLE row: {row!r}")

            run_length = int(row[count_start:index])
            decoded_segments.append(row[index] * run_length)
            index += 1
        else:
            decoded_segments.append(row[index])
            index += 1

    return "".join(decoded_segments)


def decode_level_rows(rows: list[str]) -> list[str]:
    """Decode all rows"""
    return [decode_rle_row(row) for row in rows]


def encode_level_rows(rows: list[str]) -> list[str]:
    """Encode all rows"""
    return [encode_rle_row(row) for row in rows]


def load_level_json(level_name: str | Path) -> list[str]:
    """Load a JSON level if present, or convert the matching world file on demand."""
    levels_dir = Path(__file__).resolve().parent / "levels"
    level_path = Path(level_name)

    # Accept bare names like "lv1" by normalizing them to a JSON filename.
    if not level_path.suffix:
        level_path = level_path.with_suffix(".json")

    # Resolve relative level names against the bundled levels directory.
    if not level_path.is_absolute():
        level_path = levels_dir / level_path

    # Fall back to the world source and convert it if the JSON file has not been created yet.
    if not level_path.exists():
        source_path = level_path.with_suffix(".world")
        if not source_path.exists():
            legacy_path = level_path.with_suffix(".txt")
            source_path = legacy_path if legacy_path.exists() else source_path
        if not source_path.exists():
            raise FileNotFoundError(f"No level data found for {level_path.stem}")

        convert_level_world_to_json(source_path, level_path)

    # The JSON file is expected to contain a list of row strings.
    data = json.loads(level_path.read_text(encoding="utf-8"))
    if not isinstance(data, list) or not all(isinstance(row, str) for row in data):
        raise ValueError(f"Invalid level data in {level_path}")
    return data


def convert_level_world_to_json(input_path: Path, output_path: Path) -> None:
    """Persist a plain-world level layout as JSON rows for the game to consume."""
    lines = decode_level_rows(input_path.read_text(encoding="utf-8").splitlines())
    output_path.write_text(
        json.dumps(lines, indent=2) + "\n",
        encoding="utf-8",
    )


def build_parser() -> argparse.ArgumentParser:
    """Create the command-line interface for the level conversion tool."""
    parser = argparse.ArgumentParser(
        description="Convert a Ferrum level world file into the JSON format used by the game."
    )
    parser.add_argument("input", type=Path, help="Path to the .world level file")
    parser.add_argument(
        "output",
        nargs="?",
        type=Path,
        help="Optional output path. Defaults to the same name with a .json extension.",
    )
    return parser


def main() -> None:
    """Parse CLI arguments and run a one-shot conversion."""
    parser = build_parser()
    args = parser.parse_args()

    # Default the output path to the same stem with a JSON extension.
    input_path: Path = args.input
    output_path: Path = args.output or input_path.with_suffix(".json")

    convert_level_world_to_json(input_path, output_path)
    print(f"Converted {input_path} -> {output_path}")


if __name__ == "__main__":
    main()