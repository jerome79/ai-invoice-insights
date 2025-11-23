"""Regex Analyzer tool for MCP Server.

This module provides regex-based text analysis for invoice data extraction.
"""

import logging
import re
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class RegexAnalyzer:
    """Regex-based text analyzer for invoice data."""

    def __init__(self):
        """Initialize the regex analyzer."""
        self.logger = logger
        self.patterns = {
            "invoice_number": r"Invoice\s*#?\s*:?\s*(\w+)",
            "date": r"\d{1,2}[/-]\d{1,2}[/-]\d{2,4}",
            "amount": r"\$?\s*\d+[\.,]\d{2}",
            "email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
        }

    def analyze(self, text: str) -> Dict[str, List[str]]:
        """Analyze text using regex patterns.

        Args:
            text: Text to analyze

        Returns:
            Dictionary mapping pattern names to found matches
        """
        results = {}
        for pattern_name, pattern in self.patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            results[pattern_name] = matches
            self.logger.info(f"Found {len(matches)} matches for {pattern_name}")
        return results

    def find_pattern(self, text: str, pattern: str) -> Optional[List[str]]:
        """Find matches for a custom pattern.

        Args:
            text: Text to search
            pattern: Regex pattern to use

        Returns:
            List of matches, or None if pattern is invalid
        """
        try:
            matches = re.findall(pattern, text)
            return matches
        except re.error as e:
            self.logger.error(f"Invalid regex pattern: {e}")
            return None
