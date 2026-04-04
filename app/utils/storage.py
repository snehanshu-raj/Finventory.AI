"""Local file storage abstraction (swap for S3 later)."""

import os
import uuid
import logging
from pathlib import Path

from app.config import settings

logger = logging.getLogger(__name__)


class LocalStorage:
    """Save and retrieve files from the local filesystem."""

    def __init__(self, base_dir: str | None = None):
        self.base_dir = Path(base_dir or settings.upload_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    async def save(self, filename: str, content: bytes) -> str:
        """Save file content and return the storage path."""
        ext = Path(filename).suffix
        unique_name = f"{uuid.uuid4().hex}{ext}"
        file_path = self.base_dir / unique_name
        file_path.write_bytes(content)
        logger.info("Saved file: %s (%d bytes)", file_path, len(content))
        return str(file_path)

    async def read(self, storage_path: str) -> bytes:
        """Read file content from storage path."""
        path = Path(storage_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {storage_path}")
        return path.read_bytes()

    async def delete(self, storage_path: str) -> None:
        """Delete a file from storage."""
        path = Path(storage_path)
        if path.exists():
            path.unlink()
            logger.info("Deleted file: %s", storage_path)


storage = LocalStorage()
