"""Command-line interface for readme-to-demo."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .extractor import analyze, render_brief, render_checklist
from .sources import SourceError, describe_source, read_source

_SOURCE_HELP = "README source: local path, http(s) URL, or GitHub owner/repo shorthand"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="readme-to-demo",
        description="Turn a raw README into a cleaner, demo-oriented project brief.",
    )
    parser.add_argument("--version", action="version", version=f"readme-to-demo {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    convert_cmd = sub.add_parser("convert", help="Convert a README into a demo-oriented brief")
    convert_cmd.add_argument("input", help=_SOURCE_HELP)
    convert_cmd.add_argument(
        "--output",
        "-o",
        help="Output markdown path (prints to stdout when omitted)",
    )

    check_cmd = sub.add_parser("check", help="Score a README's launch readiness")
    check_cmd.add_argument("input", help=_SOURCE_HELP)
    check_cmd.add_argument("--json", action="store_true", help="Emit machine-readable JSON")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        text = read_source(args.input)
    except (SourceError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    base_dir, label = describe_source(args.input)
    analysis = analyze(text, base_dir=base_dir, source_label=label)

    if args.command == "convert":
        brief = render_brief(analysis)
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(brief, encoding="utf-8")
            print(f"Wrote demo brief to: {output_path}")
        else:
            print(brief)
        return 0

    if args.command == "check":
        print(render_checklist(analysis, as_json=args.json))
        done, total = analysis.score
        return 0 if done == total else 2

    parser.error(f"unknown command: {args.command}")  # pragma: no cover - argparse guards this
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
