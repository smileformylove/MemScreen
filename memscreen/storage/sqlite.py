### copyright 2026 jixiangluo    ###
### email:jixiangluo85@gmail.com ###
### rights reserved by author    ###
### time: 2026-01-29             ###
### license: MIT                 ###

import logging
import sqlite3
import threading
import uuid
from typing import Any, Dict, List, Optional
from collections import deque
import time

logger = logging.getLogger(__name__)


class BatchWriter:
    """Batch writer for SQLite operations to improve performance."""

    def __init__(self, db_manager, batch_size=50, flush_interval=1.0):
        """
        Initialize batch writer.

        Args:
            db_manager: SQLiteManager instance
            batch_size: Number of operations to batch before auto-flush
            flush_interval: Maximum time in seconds before auto-flush
        """
        self.db_manager = db_manager
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.queue = deque()
        self.last_flush = time.time()
        self._lock = threading.Lock()

    def add(self, operation, *args, **kwargs):
        """Add operation to batch queue."""
        with self._lock:
            self.queue.append((operation, args, kwargs))
            # Auto-flush if batch size reached
            if len(self.queue) >= self.batch_size:
                self.flush()

    def flush(self):
        """Flush all queued operations to database."""
        if not self.queue:
            return

        with self._lock:
            with self.db_manager._lock:
                try:
                    self.db_manager.connection.execute("BEGIN")
                    cur = self.db_manager.connection.cursor()

                    for operation, args, kwargs in self.queue:
                        if operation == "add_history":
                            cur.execute(
                                """
                                INSERT INTO history (
                                    id, memory_id, old_memory, new_memory, event,
                                    created_at, updated_at, is_deleted, actor_id, role
                                )
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                """,
                                args
                            )

                    self.db_manager.connection.execute("COMMIT")
                    self.queue.clear()
                    self.last_flush = time.time()

                except Exception as e:
                    self.db_manager.connection.execute("ROLLBACK")
                    logger.error(f"Batch flush failed: {e}")
                    raise

    def __del__(self):
        """Ensure pending operations are flushed."""
        self.flush()


class SQLiteManager:
    """
    Manages SQLite database operations for memory history tracking.

    This class handles the creation, migration, and management of a SQLite database
    that stores the history of memory changes, including old and new memory states,
    events, and metadata.

    Attributes:
        db_path: Path to the SQLite database file
        connection: SQLite connection object
        _lock: Threading lock for thread-safe operations

    Examples:
        >>> manager = SQLiteManager(":memory:")
        >>> manager.add_history("mem_id", "old", "new", "update")
        >>> history = manager.get_history("mem_id")
    """

    def __init__(self, db_path: str = ":memory:", enable_batch_writing=True):
        """
        Initialize the SQLite manager.

        Args:
            db_path: Path to the SQLite database file. Defaults to ":memory:" for an in-memory database.
            enable_batch_writing: Enable batch writing for better performance.
        """
        self.db_path = db_path
        self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
        self._lock = threading.Lock()
        # OPTIMIZATION: Enable WAL mode for better concurrent performance
        self.connection.execute("PRAGMA journal_mode=WAL")
        self.connection.execute("PRAGMA synchronous=NORMAL")
        self.connection.execute("PRAGMA cache_size=10000")
        self.connection.execute("PRAGMA temp_store=MEMORY")
        self._migrate_history_table()
        self._create_history_table()

        # Enable batch writing for improved performance
        self.enable_batch_writing = enable_batch_writing
        if enable_batch_writing:
            self.batch_writer = BatchWriter(self, batch_size=50, flush_interval=1.0)

    def _migrate_history_table(self) -> None:
        """
        If a pre-existing history table had the old group-chat columns,
        rename it, create the new schema, copy the intersecting data, then
        drop the old table.
        """
        with self._lock:
            try:
                # Start a transaction
                self.connection.execute("BEGIN")
                cur = self.connection.cursor()

                cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='history'")
                if cur.fetchone() is None:
                    self.connection.execute("COMMIT")
                    return  # nothing to migrate

                cur.execute("PRAGMA table_info(history)")
                old_cols = {row[1] for row in cur.fetchall()}

                expected_cols = {
                    "id",
                    "memory_id",
                    "old_memory",
                    "new_memory",
                    "event",
                    "created_at",
                    "updated_at",
                    "is_deleted",
                    "actor_id",
                    "role",
                }

                if old_cols == expected_cols:
                    self.connection.execute("COMMIT")
                    return

                logger.info("Migrating history table to new schema (no convo columns).")

                # Clean up any existing history_old table from previous failed migration
                cur.execute("DROP TABLE IF EXISTS history_old")

                # Rename the current history table
                cur.execute("ALTER TABLE history RENAME TO history_old")

                # Create the new history table with updated schema
                cur.execute(
                    """
                    CREATE TABLE history (
                        id           TEXT PRIMARY KEY,
                        memory_id    TEXT,
                        old_memory   TEXT,
                        new_memory   TEXT,
                        event        TEXT,
                        created_at   DATETIME,
                        updated_at   DATETIME,
                        is_deleted   INTEGER,
                        actor_id     TEXT,
                        role         TEXT
                    )
                """
                )

                # Copy data from old table to new table
                intersecting = list(expected_cols & old_cols)
                if intersecting:
                    cols_csv = ", ".join(intersecting)
                    cur.execute(f"INSERT INTO history ({cols_csv}) SELECT {cols_csv} FROM history_old")

                # Drop the old table
                cur.execute("DROP TABLE history_old")

                # Commit the transaction
                self.connection.execute("COMMIT")
                logger.info("History table migration completed successfully.")

            except Exception as e:
                # Rollback the transaction on any error
                self.connection.execute("ROLLBACK")
                logger.error(f"History table migration failed: {e}")
                raise

    def _create_history_table(self) -> None:
        """Create the history table if it doesn't exist."""
        with self._lock:
            try:
                self.connection.execute("BEGIN")
                self.connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS history (
                        id           TEXT PRIMARY KEY,
                        memory_id    TEXT,
                        old_memory   TEXT,
                        new_memory   TEXT,
                        event        TEXT,
                        created_at   DATETIME,
                        updated_at   DATETIME,
                        is_deleted   INTEGER,
                        actor_id     TEXT,
                        role         TEXT
                    )
                """
                )
                self.connection.execute("COMMIT")
            except Exception as e:
                self.connection.execute("ROLLBACK")
                logger.error(f"Failed to create history table: {e}")
                raise

    def add_history(
        self,
        memory_id: str,
        old_memory: Optional[str],
        new_memory: Optional[str],
        event: str,
        *,
        created_at: Optional[str] = None,
        updated_at: Optional[str] = None,
        is_deleted: int = 0,
        actor_id: Optional[str] = None,
        role: Optional[str] = None,
        immediate: bool = False,
    ) -> None:
        """
        Add a history record to the database.

        Args:
            memory_id: ID of the memory being tracked
            old_memory: Previous memory state (can be None)
            new_memory: New memory state (can be None)
            event: Type of event (e.g., "update", "delete")
            created_at: Creation timestamp (optional)
            updated_at: Update timestamp (optional)
            is_deleted: Whether the memory is deleted (0 or 1)
            actor_id: ID of the actor making the change (optional)
            role: Role of the actor (optional)
            immediate: If True, write immediately instead of batching
        """
        # OPTIMIZATION: Use batch writing for better performance
        # Only write immediately if explicitly requested or batch writing disabled
        if self.enable_batch_writing and not immediate:
            self.batch_writer.add(
                "add_history",
                str(uuid.uuid4()),
                memory_id,
                old_memory,
                new_memory,
                event,
                created_at,
                updated_at,
                is_deleted,
                actor_id,
                role,
            )
            return

        # Original synchronous code for immediate writes
        with self._lock:
            try:
                self.connection.execute("BEGIN")
                self.connection.execute(
                    """
                    INSERT INTO history (
                        id, memory_id, old_memory, new_memory, event,
                        created_at, updated_at, is_deleted, actor_id, role
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        str(uuid.uuid4()),
                        memory_id,
                        old_memory,
                        new_memory,
                        event,
                        created_at,
                        updated_at,
                        is_deleted,
                        actor_id,
                        role,
                    ),
                )
                self.connection.execute("COMMIT")
            except Exception as e:
                self.connection.execute("ROLLBACK")
                logger.error(f"Failed to add history record: {e}")
                raise

    def get_history(self, memory_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve all history records for a specific memory.

        Args:
            memory_id: ID of the memory to retrieve history for

        Returns:
            List of dictionaries containing history records, sorted by created_at and updated_at
        """
        with self._lock:
            cur = self.connection.execute(
                """
                SELECT id, memory_id, old_memory, new_memory, event,
                       created_at, updated_at, is_deleted, actor_id, role
                FROM history
                WHERE memory_id = ?
                ORDER BY created_at ASC, DATETIME(updated_at) ASC
            """,
                (memory_id,),
            )
            rows = cur.fetchall()

        return [
            {
                "id": r[0],
                "memory_id": r[1],
                "old_memory": r[2],
                "new_memory": r[3],
                "event": r[4],
                "created_at": r[5],
                "updated_at": r[6],
                "is_deleted": bool(r[7]),
                "actor_id": r[8],
                "role": r[9],
            }
            for r in rows
        ]

    def reset(self) -> None:
        """Drop and recreate the history table."""
        with self._lock:
            try:
                self.connection.execute("BEGIN")
                self.connection.execute("DROP TABLE IF EXISTS history")
                self.connection.execute("COMMIT")
                self._create_history_table()
            except Exception as e:
                self.connection.execute("ROLLBACK")
                logger.error(f"Failed to reset history table: {e}")
                raise

    def close(self) -> None:
        """Close the database connection."""
        # OPTIMIZATION: Flush any pending batch operations before closing
        if self.enable_batch_writing and hasattr(self, 'batch_writer'):
            self.batch_writer.flush()

        if self.connection:
            self.connection.close()
            self.connection = None

    def __del__(self):
        """Destructor that ensures the connection is closed."""
        self.close()
