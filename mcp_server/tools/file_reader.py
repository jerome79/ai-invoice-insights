"""File Reader tool for MCP Server.

This module provides file reading capabilities for various file formats.
"""

import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class FileReader:
    """File reader utility class."""

    def __init__(self):
        """Initialize the file reader."""
        self.logger = logger

    def read_file(self, file_path: str) -> Optional[str]:
        """Read content from a file.

        Args:
            file_path: Path to the file to read

        Returns:
            File content as string, or None if reading fails
        """
        try:
            path = Path(file_path)
            if not path.exists():
                self.logger.error(f"File not found: {file_path}")
                return None

            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            self.logger.info(f"Successfully read file: {file_path}")
            return content
        except Exception as e:
            self.logger.error(f"Error reading file {file_path}: {e}")
            return None
