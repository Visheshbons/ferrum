from __future__ import annotations

import argparse
import json
from pathlib import Path


def convert_level_text_to_json(input_path: Path, output_path: Path) -> None:
    lines = input_path.read_text(encoding="utf-8").splitlines()
    output_path.write_text(
        json.dumps(lines, indent=2) + "\n",
        encoding="utf-8",
    )


def build_parser() -> argparse.ArgumentParser:
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
    parser = build_parser()
    args = parser.parse_args()

    input_path: Path = args.input
    output_path: Path = args.output or input_path.with_suffix(".json")

    convert_level_text_to_json(input_path, output_path)
    print(f"Converted {input_path} -> {output_path}")


if __name__ == "__main__":
    main()