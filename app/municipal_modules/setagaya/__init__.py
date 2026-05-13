"""Setagaya assembly module.

This package aggregates two session types under one municipality:
- committee (委員会): SetagayaCommitteeFetcher / SetagayaCommitteeParser
- regular   (定例会): SetagayaRegularFetcher / SetagayaRegularParser

`PARSERS` and `FETCHERS` map fetcher name -> class, used by the analyzer
and fetch CLI to select the right component per row of the `minutes` table.
"""

from .committee import SetagayaCommitteeFetcher, SetagayaCommitteeParser
from .regular import SetagayaRegularFetcher, SetagayaRegularParser

PARSERS = {
    SetagayaCommitteeParser.FETCHER_NAME: SetagayaCommitteeParser,
    SetagayaRegularParser.FETCHER_NAME: SetagayaRegularParser,
}

FETCHERS = {
    SetagayaCommitteeFetcher.FETCHER_NAME: SetagayaCommitteeFetcher,
    SetagayaRegularFetcher.FETCHER_NAME: SetagayaRegularFetcher,
}

__all__ = [
    "PARSERS",
    "FETCHERS",
    "SetagayaCommitteeFetcher",
    "SetagayaCommitteeParser",
    "SetagayaRegularFetcher",
    "SetagayaRegularParser",
]
