# The code is all hand-written, but comments FROM THIS POINT ON are mainly AI generated.

from __future__ import annotations

import argparse
import json
from pathlib import Path


def load_level_json(level_name: str | Path) -> list[str]:
    """Load a JSON level if present, or convert the matching text file on demand."""
    levels_dir = Path(__file__).resolve().parent / "levels"
    level_path = Path(level_name)

    # Accept bare names like "lv1" by normalizing them to a JSON filename.
    if not level_path.suffix:
        level_path = level_path.with_suffix(".json")

    # Resolve relative level names against the bundled levels directory.
    if not level_path.is_absolute():
        level_path = levels_dir / level_path

    # Fall back to the text source and convert it if the JSON file has not been created yet.
    if not level_path.exists():
        source_path = level_path.with_suffix(".txt")
        if not source_path.exists():
            raise FileNotFoundError(f"No level data found for {level_path.stem}")

        convert_level_text_to_json(source_path, level_path)

    # The JSON file is expected to contain a list of row strings.
    data = json.loads(level_path.read_text(encoding="utf-8"))
    if not isinstance(data, list) or not all(isinstance(row, str) for row in data):
        raise ValueError(f"Invalid level data in {level_path}")
    return data


def convert_level_text_to_json(input_path: Path, output_path: Path) -> None:
    """Persist a plain-text level layout as JSON rows for the game to consume."""
    lines = input_path.read_text(encoding="utf-8").splitlines()
    output_path.write_text(
        json.dumps(lines, indent=2) + "\n",
        encoding="utf-8",
    )


def build_parser() -> argparse.ArgumentParser:
    """Create the command-line interface for the level conversion tool."""
    parser = argparse.ArgumentParser(
        description="Convert a Ferrum level text file into the JSON format used by the game."
    )
    parser.add_argument("input", type=Path, help="Path to the .txt level file")
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

    convert_level_text_to_json(input_path, output_path)
    print(f"Converted {input_path} -> {output_path}")


if __name__ == "__main__":
    main()