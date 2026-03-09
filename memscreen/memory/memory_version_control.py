### copyright 2026 jixiangluo    ###
### email:jixiangluo85@gmail.com ###
### rights reserved by author    ###
### time: 2026-02-06             ###
### license: MIT                 ###

"""
Memory version control system for tracking changes and enabling rollbacks.

This module provides git-like version control for memories, allowing:
- Tracking all changes to memories
- Viewing version history
- Rolling back to previous versions
"""

import logging
import uuid
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path

from memscreen.storage import MemoryVersionRepository

logger = logging.getLogger(__name__)

__all__ = [
    "MemoryVersionControl",
]


class MemoryVersionControl:
    """
    Version control system for memories.

    Tracks all changes (ADD, UPDATE, DELETE, MERGE) with full history,
    enabling rollback to any previous version.

    Example:
        ```python
        vc = MemoryVersionControl(db_path="~/.memscreen/versions.db")

        # Create a new version
        version_id = vc.create_version(
            memory_id="mem123",
            content="User's screen showed code",
            metadata={"category": "fact"}
        )

        # View history
        history = vc.get_version_history("mem123")

        # Rollback
        success = vc.rollback_to_version("mem123", version_id)
        ```
    """

    def __init__(self, db_path: str):
        """
        Initialize the version control system.

        Args:
            db_path: Path to SQLite database
        """
        self.db_path = Path(db_path).expanduser()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.repo = MemoryVersionRepository(str(self.db_path))

        self._init_version_db()
        logger.info(f"MemoryVersionControl initialized (db={self.db_path})")

    def _init_version_db(self):
        """Initialize the version database."""
        self.repo.ensure_schema()

    def create_version(
        self,
        memory_id: str,
        content: str,
        metadata: Dict,
        parent_version: Optional[str] = None,
        change_type: str = "update",
    ) -> str:
        """
        Create a new version of a memory.

        Args:
            memory_id: Memory ID
            content: Memory content
            metadata: Memory metadata
            parent_version: Parent version ID (for version chain)
            change_type: Type of change ('add', 'update', 'delete', 'merge')

        Returns:
            New version ID
        """
        version_id = str(uuid.uuid4())

        try:
            self.repo.insert_version(
                version_id=version_id,
                memory_id=memory_id,
                content=content,
                metadata=metadata,
                parent_version=parent_version,
                change_type=change_type,
                created_at=datetime.now().isoformat(),
            )
            logger.info(
                f"Created version {version_id[:8]} for memory {memory_id[:8]} "
                f"(type={change_type})"
            )
            return version_id
        except Exception as e:
            logger.error(f"Failed to create version: {e}")
            raise

    def get_version(self, version_id: str) -> Optional[Dict]:
        """
        Get a specific version.

        Args:
            version_id: Version ID

        Returns:
            Version dict with keys:
            - version_id: str
            - memory_id: str
            - content: str
            - metadata: dict
            - parent_version: str
            - change_type: str
            - created_at: str
        """
        return self.repo.get_version(version_id)

    def get_version_history(
        self,
        memory_id: str,
        limit: int = 50,
    ) -> List[Dict]:
        """
        Get version history for a memory.

        Args:
            memory_id: Memory ID
            limit: Maximum number of versions to return

        Returns:
            List of version dicts (newest first)
        """
        return self.repo.list_versions(memory_id, limit=limit)

    def get_latest_version(self, memory_id: str) -> Optional[Dict]:
        """
        Get the latest version of a memory.

        Args:
            memory_id: Memory ID

        Returns:
            Latest version dict or None
        """
        history = self.get_version_history(memory_id, limit=1)
        return history[0] if history else None

    def rollback_to_version(
        self,
        memory_id: str,
        version_id: str,
        vector_store=None,
    ) -> bool:
        """
        Rollback a memory to a specific version.

        This creates a NEW version with the old content, preserving history.

        Args:
            memory_id: Memory to rollback
            version_id: Target version to rollback to
            vector_store: Optional vector store to update

        Returns:
            True if successful, False otherwise
        """
        target_version = self.get_version(version_id)
        if not target_version:
            logger.error(f"Version {version_id[:8]} not found")
            return False

        if target_version['memory_id'] != memory_id:
            logger.error(
                f"Version {version_id[:8]} belongs to different memory"
            )
            return False

        try:
            new_version_id = self.create_version(
                memory_id=memory_id,
                content=target_version['content'],
                metadata=target_version['metadata'],
                parent_version=version_id,
                change_type="rollback",
            )

            if vector_store:
                logger.info("Vector store update not yet implemented")

            logger.info(
                f"Rolled back {memory_id[:8]} to version {version_id[:8]}, "
                f"new version {new_version_id[:8]}"
            )
            return True
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            return False

    def get_all_memories(self) -> List[str]:
        """
        Get list of all memory IDs that have versions.

        Returns:
            List of memory IDs
        """
        return self.repo.list_memory_ids()

    def get_stats(self) -> Dict:
        """
        Get version control statistics.

        Returns:
            Dict with stats:
            - total_versions: Total number of versions
            - total_memories: Number of memories with versions
            - avg_versions_per_memory: Average versions per memory
        """
        return self.repo.get_stats()
