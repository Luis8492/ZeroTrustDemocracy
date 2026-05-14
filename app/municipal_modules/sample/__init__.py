"""Reference 'sample' municipality used to demonstrate the plugin contract.

This is a synthetic assembly with fabricated members and topics. It exists so
that OSS users (and CI) can exercise the fetch → analyze → export pipeline
end-to-end without needing real meeting minute data or Playwright. A real
assembly plugin looks the same but with a Playwright-driven fetcher; see the
private operations repo or ``docs/FORK_GUIDE.md`` for that variant.
"""

from .regular import SampleParser, SampleFetcher

PARSERS = {SampleParser.FETCHER_NAME: SampleParser}
FETCHERS = {SampleFetcher.FETCHER_NAME: SampleFetcher}

__all__ = ["PARSERS", "FETCHERS", "SampleParser", "SampleFetcher"]
