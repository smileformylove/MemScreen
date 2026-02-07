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
import sqlite3
import uuid
import json
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path

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

        self._init_version_db()
        logger.info(f"MemoryVersionControl initialized (db={self.db_path})")

    def _init_version_db(self):
        """Initialize the version database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create versions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS memory_versions (
                version_id TEXT PRIMARY KEY,
                memory_id TEXT NOT NULL,
                content TEXT,
                metadata TEXT,
                parent_version TEXT,
                change_type TEXT DEFAULT 'add',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (parent_version) REFERENCES memory_versions(version_id),
                FOREIGN KEY (memory_id) REFERENCES memories(id)
            )
        ''')

        # Create indexes for performance
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_memory_id
            ON memory_versions(memory_id)
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_created_at
            ON memory_versions(created_at DESC)
        ''')

        conn.commit()
        conn.close()

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

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute('''
                INSERT INTO memory_versions (
                    version_id, memory_id, content, metadata,
                    parent_version, change_type, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                version_id,
                memory_id,
                content,
                json.dumps(metadata),
                parent_version,
                change_type.lower(),
                datetime.now().isoformat(),
            ))

            conn.commit()
            logger.info(
                f"Created version {version_id[:8]} for memory {memory_id[:8]} "
                f"(type={change_type})"
            )

            return version_id

        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to create version: {e}")
            raise
        finally:
            conn.close()

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
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute('''
                SELECT version_id, memory_id, content, metadata,
                       parent_version, change_type, created_at
                FROM memory_versions
                WHERE version_id = ?
            ''', (version_id,))

            row = cursor.fetchone()
            if not row:
                return None

            return {
                'version_id': row[0],
                'memory_id': row[1],
                'content': row[2],
                'metadata': json.loads(row[3]),
                'parent_version': row[4],
                'change_type': row[5],
                'created_at': row[6],
            }

        finally:
            conn.close()

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
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute('''
                SELECT version_id, memory_id, content, metadata,
                       parent_version, change_type, created_at
                FROM memory_versions
                WHERE memory_id = ?
                ORDER BY created_at DESC
                LIMIT ?
            ''', (memory_id, limit))

            versions = []
            for row in cursor.fetchall():
                versions.append({
                    'version_id': row[0],
                    'memory_id': row[1],
                    'content': row[2],
                    'metadata': json.loads(row[3]),
                    'parent_version': row[4],
                    'change_type': row[5],
                    'created_at': row[6],
                })

            return versions

        finally:
            conn.close()

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
        # Get target version
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
            # Create new version with old content
            new_version_id = self.create_version(
                memory_id=memory_id,
                content=target_version['content'],
                metadata=target_version['metadata'],
                parent_version=version_id,
                change_type="rollback",
            )

            # Update vector store if provided
            if vector_store:
                # TODO: Generate new embedding and update
                logger.info(f"Vector store update not yet implemented")

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
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute('''
                SELECT DISTINCT memory_id FROM memory_versions
            ''')

            return [row[0] for row in cursor.fetchall()]

        finally:
            conn.close()

    def get_stats(self) -> Dict:
        """
        Get version control statistics.

        Returns:
            Dict with stats:
            - total_versions: Total number of versions
            - total_memories: Number of memories with versions
            - avg_versions_per_memory: Average versions per memory
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Total versions
            cursor.execute('SELECT COUNT(*) FROM memory_versions')
            total_versions = cursor.fetchone()[0]

            # Total memories
            cursor.execute('SELECT COUNT(DISTINCT memory_id) FROM memory_versions')
            total_memories = cursor.fetchone()[0]

            # Average versions per memory
            avg = total_versions / total_memories if total_memories > 0 else 0

            return {
                'total_versions': total_versions,
                'total_memories': total_memories,
                'avg_versions_per_memory': round(avg, 2),
            }

        finally:
            conn.close()
