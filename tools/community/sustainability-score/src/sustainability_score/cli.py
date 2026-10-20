"""Command-line entrypoint: `sustainability-score <repo> [--json out.json] [--md out.md]`."""
from __future__ import annotations

import argparse
import sys

from .scanner import scan
from .report import to_json, to_markdown


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        prog="sustainability-score",
        description="Static sustainability score for a code repository, grounded "
                    "in the GSF Software Carbon Intensity (SCI) specification.")
    ap.add_argument("repo", help="Path to the repository to scan")
    ap.add_argument("--json", metavar="FILE", help="Write JSON report to FILE")
    ap.add_argument("--md", metavar="FILE", help="Write Markdown report to FILE")
    ap.add_argument("--quiet", action="store_true", help="Suppress stdout summary")
    args = ap.parse_args(argv)

    result = scan(args.repo)

    if args.json:
        with open(args.json, "w") as fh:
            fh.write(to_json(result))
    if args.md:
        with open(args.md, "w") as fh:
            fh.write(to_markdown(result))

    if not args.quiet:
        if not args.json and not args.md:
            print(to_markdown(result))
        else:
            print(f"Sustainability score: {result.composite_score}/100 "
                  f"(Grade {result.grade}), Tier {result.overall_tier}, "
                  f"{result.meta['total_findings']} findings across "
                  f"{len(result.meta['pillars_applicable'])} applicable pillars.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
