"""Municipality-specific components for fetching and parsing meeting minutes.

This module discovers parser/fetcher implementations at runtime.  A
municipality package (e.g. ``setagaya``) may expose a ``PARSERS`` dict mapping
``fetcher_name`` to parser class — this is the preferred form when a single
municipality has multiple session types.  Older modules with a single parser
under ``parsers/`` are still supported via fallback discovery.

``load_parsers()`` returns a flat ``{fetcher_name: parser_class}`` mapping,
which is what the analyzer needs (the ``minutes`` table records the fetcher
name per row).  ``load_parsers_by_municipality()`` returns the grouped form
when callers need to know which municipality owns a fetcher.
"""

from __future__ import annotations

import importlib
import inspect
import pkgutil
from pathlib import Path
from typing import Dict, Type

from .base.base_minute_parser import BaseMinuteParser
from utils.logger import get_logger

logger = get_logger(__name__)


def _iter_municipality_packages():
    base_path = Path(__file__).resolve().parent
    for _finder, name, ispkg in pkgutil.iter_modules([str(base_path)]):
        if ispkg and name != "base":
            yield name


def load_parsers_by_municipality() -> Dict[str, Dict[str, Type[BaseMinuteParser]]]:
    """Return ``{municipality: {fetcher_name: parser_class}}``."""
    result: Dict[str, Dict[str, Type[BaseMinuteParser]]] = {}
    for name in _iter_municipality_packages():
        try:
            module = importlib.import_module(f"{__name__}.{name}")
        except Exception as exc:  # pragma: no cover - import failures
            logger.warning("Failed to import municipality %s: %s", name, exc)
            continue

        # Preferred: explicit PARSERS dict exported from the package.
        explicit = getattr(module, "PARSERS", None)
        if isinstance(explicit, dict) and explicit:
            result[name] = dict(explicit)
            continue

        # Fallback: scan <municipality>/parsers/* for BaseMinuteParser subclasses.
        try:
            parsers_pkg = importlib.import_module(f"{__name__}.{name}.parsers")
        except ModuleNotFoundError:
            continue
        except Exception as exc:  # pragma: no cover
            logger.warning("Failed to import parsers package for %s: %s", name, exc)
            continue

        discovered: Dict[str, Type[BaseMinuteParser]] = {}
        for _, mod_name, _ in pkgutil.iter_modules(parsers_pkg.__path__):
            try:
                mod = importlib.import_module(f"{__name__}.{name}.parsers.{mod_name}")
            except Exception as exc:  # pragma: no cover
                logger.warning(
                    "Failed to import parser module %s for %s: %s", mod_name, name, exc
                )
                continue
            for _, obj in inspect.getmembers(mod, inspect.isclass):
                if issubclass(obj, BaseMinuteParser) and obj is not BaseMinuteParser:
                    fetcher_name = getattr(obj, "FETCHER_NAME", None) or name
                    discovered[fetcher_name] = obj
        if discovered:
            result[name] = discovered
    return result


def load_parsers() -> Dict[str, Type[BaseMinuteParser]]:
    """Return a flat ``{fetcher_name: parser_class}`` mapping across all municipalities."""
    flat: Dict[str, Type[BaseMinuteParser]] = {}
    for parsers in load_parsers_by_municipality().values():
        flat.update(parsers)
    return flat


def load_fetchers_by_municipality() -> Dict[str, Dict[str, Type]]:
    """Return ``{municipality: {fetcher_name: fetcher_class}}``.

    Mirrors ``load_parsers_by_municipality`` but for fetcher classes (which
    cannot be inspected via the parser-only base class). Each municipality
    package must export a ``FETCHERS`` dict to participate.
    """
    result: Dict[str, Dict[str, Type]] = {}
    for name in _iter_municipality_packages():
        try:
            module = importlib.import_module(f"{__name__}.{name}")
        except Exception as exc:  # pragma: no cover
            logger.warning("Failed to import municipality %s: %s", name, exc)
            continue
        fetchers = getattr(module, "FETCHERS", None)
        if isinstance(fetchers, dict) and fetchers:
            result[name] = dict(fetchers)
    return result


__all__ = [
    "load_parsers",
    "load_parsers_by_municipality",
    "load_fetchers_by_municipality",
]

