"""SQLite repository for memory version history."""

from __future__ import annotations

import json
import os
import sqlite3
from typing import Any, Dict, List, Optional


class MemoryVersionRepository:
    """Encapsulates SQLite access for memory version history."""

    def __init__(self, db_path: str):
        self.db_path = str(db_path)

    def ensure_schema(self) -> None:
        db_dir = os.path.dirname(self.db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
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
                """
            )
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_memory_id
                ON memory_versions(memory_id)
                """
            )
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_created_at
                ON memory_versions(created_at DESC)
                """
            )
            conn.commit()
        finally:
            conn.close()

    def insert_version(
        self,
        *,
        version_id: str,
        memory_id: str,
        content: str,
        metadata: Dict[str, Any],
        parent_version: Optional[str] = None,
        change_type: str = "update",
        created_at: Optional[str] = None,
    ) -> str:
        self.ensure_schema()

        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        try:
            conn.execute(
                """
                INSERT INTO memory_versions (
                    version_id, memory_id, content, metadata,
                    parent_version, change_type, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    version_id,
                    memory_id,
                    content,
                    json.dumps(metadata, ensure_ascii=False),
                    parent_version,
                    str(change_type or "update").lower(),
                    created_at,
                ),
            )
            conn.commit()
            return version_id
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def get_version(self, version_id: str) -> Optional[Dict[str, Any]]:
        self.ensure_schema()

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            row = conn.execute(
                """
                SELECT version_id, memory_id, content, metadata,
                       parent_version, change_type, created_at
                FROM memory_versions
                WHERE version_id = ?
                """,
                (version_id,),
            ).fetchone()
            if row is None:
                return None
            return self._normalize_row(row)
        finally:
            conn.close()

    def list_versions(self, memory_id: str, *, limit: int = 50) -> List[Dict[str, Any]]:
        self.ensure_schema()

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            rows = conn.execute(
                """
                SELECT version_id, memory_id, content, metadata,
                       parent_version, change_type, created_at
                FROM memory_versions
                WHERE memory_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (memory_id, int(limit)),
            ).fetchall()
            return [self._normalize_row(row) for row in rows]
        finally:
            conn.close()

    def list_memory_ids(self) -> List[str]:
        self.ensure_schema()

        conn = sqlite3.connect(self.db_path)
        try:
            rows = conn.execute("SELECT DISTINCT memory_id FROM memory_versions").fetchall()
            return [str(row[0]) for row in rows]
        finally:
            conn.close()

    def get_stats(self) -> Dict[str, Any]:
        self.ensure_schema()

        conn = sqlite3.connect(self.db_path)
        try:
            total_versions = int(
                (conn.execute("SELECT COUNT(*) FROM memory_versions").fetchone() or [0])[0] or 0
            )
            total_memories = int(
                (conn.execute("SELECT COUNT(DISTINCT memory_id) FROM memory_versions").fetchone() or [0])[0]
                or 0
            )
            avg_versions = total_versions / total_memories if total_memories > 0 else 0.0
            return {
                "total_versions": total_versions,
                "total_memories": total_memories,
                "avg_versions_per_memory": round(avg_versions, 2),
            }
        finally:
            conn.close()

    @staticmethod
    def _normalize_row(row: sqlite3.Row) -> Dict[str, Any]:
        metadata_raw = row["metadata"]
        if metadata_raw:
            try:
                metadata = json.loads(str(metadata_raw))
            except Exception:
                metadata = {}
        else:
            metadata = {}
        return {
            "version_id": str(row["version_id"] or ""),
            "memory_id": str(row["memory_id"] or ""),
            "content": row["content"],
            "metadata": metadata,
            "parent_version": row["parent_version"],
            "change_type": str(row["change_type"] or ""),
            "created_at": row["created_at"],
        }
