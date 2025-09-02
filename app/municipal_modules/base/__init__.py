"""Base classes for municipal modules."""

from .BaseMinuteFetcher import BaseMinuteFetcher
from .base_minute_parser import BaseMinuteParser

__all__ = ["BaseMinuteFetcher", "BaseMinuteParser"]
