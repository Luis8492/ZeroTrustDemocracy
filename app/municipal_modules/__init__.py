"""Municipality-specific components for fetching and parsing meeting minutes.

This module exposes helper utilities for dynamically discovering parser
implementations.  Municipal-specific code lives under
``app/municipal_modules/<municipality>/parsers`` and each parser subclasses
``BaseMinuteParser``.  The :func:`load_parsers` function walks these packages
and returns a mapping from municipality name to the corresponding parser
class.  This allows other parts of the application to support new
municipalities without hard coding imports.
"""

from __future__ import annotations

import importlib
import inspect
import pkgutil
from pathlib import Path
from typing import Dict, Type

from .base.base_minute_parser import BaseMinuteParser


def load_parsers() -> Dict[str, Type[BaseMinuteParser]]:
    """Discover available minute parser classes.

    The search traverses subpackages of ``app.municipal_modules`` looking for
    a ``parsers`` package.  Any class defined in these modules that subclasses
    :class:`BaseMinuteParser` will be returned.  The key of the returned
    dictionary is the municipality name (the package name).
    """

    parser_classes: Dict[str, Type[BaseMinuteParser]] = {}
    base_path = Path(__file__).resolve().parent

    # Iterate through immediate subpackages (municipalities)
    for finder, name, ispkg in pkgutil.iter_modules([str(base_path)]):
        if not ispkg or name == "base":
            continue

        try:
            parsers_pkg = importlib.import_module(f"{__name__}.{name}.parsers")
        except ModuleNotFoundError:
            # Municipality package without parsers submodule
            continue

        # Inspect each module inside the parsers package
        for _, mod_name, _ in pkgutil.iter_modules(parsers_pkg.__path__):
            module = importlib.import_module(
                f"{__name__}.{name}.parsers.{mod_name}"
            )
            for obj_name, obj in inspect.getmembers(module, inspect.isclass):
                if issubclass(obj, BaseMinuteParser) and obj is not BaseMinuteParser:
                    parser_classes[name] = obj

    return parser_classes


__all__ = ["load_parsers"]

