import argparse
import sys
from pathlib import Path

# Ensure repository root is importable when running as a script
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.municipal_modules import load_fetchers_by_municipality

FETCHERS_BY_MUNICIPALITY = load_fetchers_by_municipality()


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch minutes for a municipality")
    parser.add_argument("--municipality", required=True, help="target municipality")
    parser.add_argument(
        "--fetcher",
        default=None,
        help="optional FETCHER_NAME to run only one session (e.g. SetagayaCommitteeFetcher). "
        "If omitted, every fetcher registered for the municipality runs in order.",
    )
    args = parser.parse_args()

    fetchers = FETCHERS_BY_MUNICIPALITY.get(args.municipality)
    if not fetchers:
        raise ValueError(f"Unknown municipality: {args.municipality}")

    if args.fetcher is not None:
        if args.fetcher not in fetchers:
            raise ValueError(
                f"Unknown fetcher '{args.fetcher}' for {args.municipality}. "
                f"Available: {sorted(fetchers)}"
            )
        selected = {args.fetcher: fetchers[args.fetcher]}
    else:
        selected = fetchers

    needs_playwright = any(
        getattr(cls, "REQUIRES_PLAYWRIGHT", True) for cls in selected.values()
    )

    if needs_playwright:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as playwright:
            for fetcher_cls in selected.values():
                pw = playwright if getattr(fetcher_cls, "REQUIRES_PLAYWRIGHT", True) else None
                fetcher_cls(pw, args.municipality).run()
    else:
        for fetcher_cls in selected.values():
            fetcher_cls(None, args.municipality).run()


if __name__ == "__main__":
    main()

