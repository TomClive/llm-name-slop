"""CLI for the LLM name-slop project.

Usage:
  python run.py sample [--dry-run] [--smoke-test] [--yes]
                       [--models m1 m2 ...] [--n N]
  python run.py analyze
"""

import argparse

import config


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    ps = sub.add_parser("sample", help="collect completions")
    ps.add_argument("--dry-run", action="store_true",
                    help="print the prompts, make no API calls")
    ps.add_argument("--smoke-test", action="store_true",
                    help="3 samples on the first model only")
    ps.add_argument("--yes", action="store_true",
                    help="skip the over-cap confirmation prompt")
    ps.add_argument("--models", nargs="+", default=None,
                    help="override model list")
    ps.add_argument("--n", type=int, default=None,
                    help="samples per model (default from config)")
    ps.add_argument("--variant", default="default",
                    choices=list(config.PROMPT_VARIANTS),
                    help="prompt variant; non-default writes to samples_<variant>/")

    sub.add_parser("analyze", help="extract names, compute lift, write outputs")

    args = p.parse_args()

    if args.cmd == "sample":
        import sample
        models = args.models or config.MODELS
        n = args.n or config.SAMPLES_PER_MODEL
        if args.smoke_test:
            models, n = models[:1], 3
        sample.run(models, n, dry_run=args.dry_run, assume_yes=args.yes,
                   variant=args.variant)
    elif args.cmd == "analyze":
        import analyze
        analyze.analyze()


if __name__ == "__main__":
    main()
