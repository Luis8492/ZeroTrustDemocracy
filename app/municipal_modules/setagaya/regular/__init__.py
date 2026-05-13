"""Setagaya regular session: fetcher + parser."""

from .parsers import SetagayaRegularParser


def __getattr__(name):
    if name == "SetagayaRegularFetcher":
        from .fetchers import SetagayaRegularFetcher
        return SetagayaRegularFetcher
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = ["SetagayaRegularFetcher", "SetagayaRegularParser"]
