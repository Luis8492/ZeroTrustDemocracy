"""Setagaya committee session: fetcher + parser."""

from .parsers import SetagayaCommitteeParser


def __getattr__(name):
    if name == "SetagayaCommitteeFetcher":
        from .fetchers import SetagayaCommitteeFetcher
        return SetagayaCommitteeFetcher
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = ["SetagayaCommitteeFetcher", "SetagayaCommitteeParser"]
