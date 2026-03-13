from __future__ import annotations

import argparse
from pathlib import Path

from .extractor import extract_demo_brief


def main() -> None:
    parser = argparse.ArgumentParser(prog="readme-to-demo")
    sub = parser.add_subparsers(dest="command", required=True)

    convert_cmd = sub.add_parser("convert", help="Convert a README into a demo-oriented brief")
    convert_cmd.add_argument("input", help="Input markdown file path")
    convert_cmd.add_argument("--output", required=True, help="Output markdown path")

    args = parser.parse_args()

    if args.command == "convert":
        result = extract_demo_brief(args.input)
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(result, encoding="utf-8")
        print(f"Wrote demo brief to: {output_path}")


if __name__ == "__main__":
    main()
