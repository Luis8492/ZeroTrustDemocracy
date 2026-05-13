"""Setagaya assembly module.

This package aggregates two session types under one municipality:
- committee (委員会): SetagayaCommitteeFetcher / SetagayaCommitteeParser
- regular   (定例会): SetagayaRegularFetcher / SetagayaRegularParser

`PARSERS` and `FETCHERS` map fetcher name -> class, used by the analyzer
and fetch CLI to select the right component per row of the `minutes` table.

Fetcher classes depend on Playwright which may not be installed in every
environment (e.g. analysis-only setups).  They are imported lazily so that
``PARSERS`` is always available without Playwright.
"""

from .committee import SetagayaCommitteeParser
from .regular import SetagayaRegularParser

PARSERS = {
    SetagayaCommitteeParser.FETCHER_NAME: SetagayaCommitteeParser,
    SetagayaRegularParser.FETCHER_NAME: SetagayaRegularParser,
}


def _load_fetchers():
    from .committee import SetagayaCommitteeFetcher
    from .regular import SetagayaRegularFetcher
    return {
        SetagayaCommitteeFetcher.FETCHER_NAME: SetagayaCommitteeFetcher,
        SetagayaRegularFetcher.FETCHER_NAME: SetagayaRegularFetcher,
    }


# FETCHERS is built lazily via __getattr__ so importing this package
# never requires Playwright.
def __getattr__(name):
    if name == "FETCHERS":
        fetchers = _load_fetchers()
        globals()["FETCHERS"] = fetchers
        return fetchers
    if name in ("SetagayaCommitteeFetcher", "SetagayaRegularFetcher"):
        fetchers = _load_fetchers()
        globals()["FETCHERS"] = fetchers
        return fetchers.get(name) or getattr(
            __import__(f"{__name__}.committee", fromlist=[name])
            if "Committee" in name
            else __import__(f"{__name__}.regular", fromlist=[name]),
            name,
        )
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "PARSERS",
    "FETCHERS",
    "SetagayaCommitteeFetcher",
    "SetagayaCommitteeParser",
    "SetagayaRegularFetcher",
    "SetagayaRegularParser",
]
