"""
Command-line interface.

Usage:
    sci-for-ai run     --query "..." [--provider mock|anthropic|gemini|openai|recorded]
    sci-for-ai compare --query "..." [--provider ...] [--record-to FILE.json]

To record a real run for later replay (no API key needed at replay time):
    sci-for-ai compare --provider openai --model gpt-4o-mini \\
        --query "..." --record-to my-run.json

Then anyone can replay it:
    sci-for-ai compare --provider recorded --fixture my-run.json --query "..."

Run `sci-for-ai --help` for full options.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from .pipeline import compare_prompt_sets, run_pipeline
from .prompts import BASELINE, OPTIMIZED, PROMPT_SETS
from .providers import build_provider
from .report import format_comparison, format_pipeline


def _add_common(p: argparse.ArgumentParser) -> None:
    p.add_argument("--query", required=True, help="Natural-language query to analyse")
    p.add_argument("--provider", default="mock",
                   choices=["mock", "anthropic", "gemini", "openai", "recorded"],
                   help="LLM provider (default: mock — no network)")
    p.add_argument("--model", default=None,
                   help="Model id override; provider-specific default if omitted")
    p.add_argument("--region", default="us-central1",
                   help="Region for carbon-intensity lookup (default: us-central1)")
    p.add_argument("--max-output-tokens", type=int, default=1024,
                   help="Per-call cap on output tokens (default: 1024)")
    p.add_argument("--fixture", default=None,
                   help="Path to recorded JSON fixture (required when --provider=recorded)")
    p.add_argument("--record-to", default=None, metavar="FILE.json",
                   help="Save the full run as a JSON fixture for later replay. "
                        "Use with a real provider; the file can then be replayed "
                        "with --provider recorded --fixture FILE.json.")
    p.add_argument("--scale-users", type=int, default=10_000, metavar="N",
                   help="Project per-request impact to N requests/day (default: 10,000). "
                        "Set to 0 to skip the scale projection.")
    p.add_argument("--json", action="store_true",
                   help="Emit JSON instead of the formatted report")
    p.add_argument("--verbose", "-v", action="store_true",
                   help="Enable info-level logging")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sci-for-ai",
        description="Measure Software Carbon Intensity of LLM inference pipelines.",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    run_p = sub.add_parser("run", help="Run a single pipeline")
    _add_common(run_p)
    run_p.add_argument("--prompts", default="baseline", choices=list(PROMPT_SETS),
                       help="Which prompt set to use (default: baseline)")

    cmp_p = sub.add_parser("compare", help="Compare baseline vs optimized prompts")
    _add_common(cmp_p)

    return parser


def _make_provider(args: argparse.Namespace):
    kwargs = {"region": args.region}
    if args.model:
        kwargs["model_id"] = args.model
    if args.provider == "recorded":
        if not args.fixture:
            raise ValueError("--fixture FILE.json is required when --provider=recorded")
        kwargs["fixture_path"] = args.fixture
        # Region/model are inferred from the fixture if not overridden
        if not args.model:
            kwargs.pop("model_id", None)
    return build_provider(args.provider, **kwargs)


def _save_fixture(result_dict: dict, path: str) -> None:
    """Write a comparison or pipeline result as JSON, with a small header."""
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w") as f:
        json.dump(result_dict, f, indent=2, default=str)
    print(f"\nRecorded run saved to {output_path}", file=sys.stderr)
    print(f"Replay with: sci-for-ai compare --provider recorded "
          f"--fixture {output_path} --query \"...\"", file=sys.stderr)


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    # Validate flag combinations
    if args.record_to and args.provider == "recorded":
        print("error: --record-to cannot be used with --provider=recorded "
              "(that would replay a fixture and overwrite itself)", file=sys.stderr)
        return 2

    try:
        provider = _make_provider(args)
    except (ImportError, ValueError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    # Warn about a subtle inconsistency: if the user overrides --model on
    # a recorded fixture, energy stays as recorded but cost uses the
    # override's pricing. Useful for "what would this cost on gpt-5.5?"
    # but worth flagging so the user knows the energy figure is from the
    # original model, not the override.
    if (args.provider == "recorded"
            and getattr(provider, "_model_overridden", False)):
        recorded = getattr(provider, "_recorded_model", "unknown")
        print(
            f"\nNote: replaying fixture recorded with '{recorded}' but pricing "
            f"this run as '{args.model}'. Energy/emissions are the recorded "
            f"values from '{recorded}'; only USD cost uses '{args.model}' "
            f"pricing. Useful for cost projection across model tiers.\n",
            file=sys.stderr,
        )

    if args.cmd == "run":
        result = run_pipeline(
            provider, PROMPT_SETS[args.prompts], args.query,
            max_output_tokens=args.max_output_tokens,
        )
        if args.record_to:
            _save_fixture(result.to_dict(), args.record_to)
        if args.json:
            print(json.dumps(result.to_dict(), indent=2, default=str))
        else:
            print(format_pipeline(result))
            print()
            print("--- Report ---")
            print(result.report)
        return 0

    if args.cmd == "compare":
        result = compare_prompt_sets(
            provider, BASELINE, OPTIMIZED, args.query,
            max_output_tokens=args.max_output_tokens,
        )
        if args.record_to:
            _save_fixture(result.to_dict(), args.record_to)
        if args.json:
            print(json.dumps(result.to_dict(), indent=2, default=str))
        else:
            from .report import format_report_preview, format_scale
            from .scale import project_comparison

            print(format_comparison(result))

            if args.scale_users > 0:
                projection = project_comparison(
                    result.baseline.totals,
                    result.optimized.totals,
                    requests_per_day=args.scale_users,
                )
                print(format_scale(projection))

            print(format_report_preview(result, fixture_path=args.record_to or args.fixture))
        return 0

    return 1  # unreachable


if __name__ == "__main__":
    raise SystemExit(main())
