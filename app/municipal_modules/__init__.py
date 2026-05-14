"""Municipality-specific components for fetching and parsing meeting minutes.

This module discovers parser/fetcher implementations at runtime. A municipality
package (e.g. ``sample``) may expose a ``PARSERS`` dict mapping
``fetcher_name`` to parser class — this is the preferred form when a single
municipality has multiple session types. Older modules with a single parser
under ``parsers/`` are still supported via fallback discovery.

Plugins can live in two places:

1. **Bundled** — subpackages of ``app.municipal_modules`` (e.g. the ``sample``
   reference impl shipped with the framework).
2. **External** — directories listed in the ``MUNICIPAL_MODULES_PATH``
   environment variable (OS-native path separator, ``;`` on Windows / ``:`` on
   POSIX). Each listed directory's immediate subpackages are imported as
   *top-level* packages, so a private operations repo can keep its municipality
   plugin out of the public framework tree.

``load_parsers()`` returns a flat ``{fetcher_name: parser_class}`` mapping,
which is what the analyzer needs (the ``minutes`` table records the fetcher
name per row). ``load_parsers_by_municipality()`` returns the grouped form
when callers need to know which municipality owns a fetcher.
"""

from __future__ import annotations

import importlib
import inspect
import os
import pkgutil
import sys
from pathlib import Path
from types import ModuleType
from typing import Dict, Iterator, Tuple, Type

from .base.base_minute_parser import BaseMinuteParser
from utils.logger import get_logger

logger = get_logger(__name__)


def _external_plugin_dirs() -> list[Path]:
    raw = os.getenv("MUNICIPAL_MODULES_PATH")
    if not raw:
        return []
    dirs: list[Path] = []
    for chunk in raw.split(os.pathsep):
        chunk = chunk.strip()
        if not chunk:
            continue
        path = Path(chunk).expanduser()
        if not path.exists():
            logger.warning("MUNICIPAL_MODULES_PATH entry does not exist: %s", path)
            continue
        dirs.append(path.resolve())
    return dirs


def _iter_municipality_packages() -> Iterator[Tuple[str, ModuleType]]:
    """Yield ``(municipality_name, package_module)`` for every discoverable plugin.

    Bundled plugins are imported as ``app.municipal_modules.<name>``. External
    plugins (via ``MUNICIPAL_MODULES_PATH``) are imported as top-level
    ``<name>`` after their containing directory is prepended to ``sys.path``.
    Duplicate names: bundled wins over external, first external wins over later.
    """
    seen: set[str] = set()
    bundled_path = Path(__file__).resolve().parent
    for _finder, name, ispkg in pkgutil.iter_modules([str(bundled_path)]):
        if not ispkg or name == "base":
            continue
        try:
            module = importlib.import_module(f"{__name__}.{name}")
        except Exception as exc:  # pragma: no cover - import failures
            logger.warning("Failed to import bundled municipality %s: %s", name, exc)
            continue
        seen.add(name)
        yield name, module

    for ext_dir in _external_plugin_dirs():
        ext_str = str(ext_dir)
        if ext_str not in sys.path:
            sys.path.insert(0, ext_str)
        for _finder, name, ispkg in pkgutil.iter_modules([ext_str]):
            if not ispkg or name == "base":
                continue
            if name in seen:
                logger.warning(
                    "External municipality %s in %s shadowed by bundled module; skipping",
                    name,
                    ext_dir,
                )
                continue
            try:
                module = importlib.import_module(name)
            except Exception as exc:  # pragma: no cover - import failures
                logger.warning(
                    "Failed to import external municipality %s from %s: %s",
                    name,
                    ext_dir,
                    exc,
                )
                continue
            seen.add(name)
            yield name, module


def load_parsers_by_municipality() -> Dict[str, Dict[str, Type[BaseMinuteParser]]]:
    """Return ``{municipality: {fetcher_name: parser_class}}``."""
    result: Dict[str, Dict[str, Type[BaseMinuteParser]]] = {}
    for name, module in _iter_municipality_packages():
        explicit = getattr(module, "PARSERS", None)
        if isinstance(explicit, dict) and explicit:
            result[name] = dict(explicit)
            continue

        # Fallback: scan <package>.parsers for BaseMinuteParser subclasses.
        parsers_module_name = f"{module.__name__}.parsers"
        try:
            parsers_pkg = importlib.import_module(parsers_module_name)
        except ModuleNotFoundError:
            continue
        except Exception as exc:  # pragma: no cover
            logger.warning(
                "Failed to import parsers package for %s: %s", name, exc
            )
            continue

        discovered: Dict[str, Type[BaseMinuteParser]] = {}
        for _, mod_name, _ in pkgutil.iter_modules(parsers_pkg.__path__):
            try:
                mod = importlib.import_module(f"{parsers_module_name}.{mod_name}")
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
    for name, module in _iter_municipality_packages():
        fetchers = getattr(module, "FETCHERS", None)
        if isinstance(fetchers, dict) and fetchers:
            result[name] = dict(fetchers)
    return result


__all__ = [
    "load_parsers",
    "load_parsers_by_municipality",
    "load_fetchers_by_municipality",
]
