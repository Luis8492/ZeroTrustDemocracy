"""Base classes for parsing municipal meeting minutes."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseMinuteParser(ABC):
    """Abstract base class for municipal meeting minute parsers."""

    @abstractmethod
    def convert(self, text: str) -> Dict[str, Any]:
        """Convert raw minute text into structured data."""
        raise NotImplementedError
