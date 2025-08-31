"""Base classes for parsing municipal meeting minutes."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class BaseMinuteParser(ABC):
    """Abstract base class for municipal meeting minute parsers."""

    @abstractmethod
    def extract_meeting_data(self, text: str) -> Dict[str, Any]:
        """Extract meeting metadata such as date and name."""
        raise NotImplementedError

    @abstractmethod
    def extract_topic_section(self, text: str) -> List[str]:
        """Split raw text into per-topic sections."""
        raise NotImplementedError

    @abstractmethod
    def extract_speeches(self, topic_text: str) -> List[Dict[str, Any]]:
        """Extract individual speeches from a topic section."""
        raise NotImplementedError

    @abstractmethod
    def extract_QAs(self, minute: Dict[str, Any]) -> List[Any]:
        """Extract Q&A sequences from a minute structure."""
        raise NotImplementedError
