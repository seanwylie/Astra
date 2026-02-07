"""
Storage Backend Abstraction Layer

Provides a unified interface for state storage, supporting both JSON (legacy)
and SQLite backends. Allows gradual migration and fallback capabilities.
"""

import json
import sqlite3
import logging
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional
from contextlib import contextmanager
import boto3
import io
from app.config.loader import load_config
from app.logging_config import get_logger

logger = get_logger("storage_backend")

# Load configuration
general_config = load_config("general_config")
S3_BUCKET_NAME = general_config.get("s3_bucket", "swylie-astra")
STORAGE_BACKEND = general_config.get("storage_backend", "sqlite")  # "json" or "sqlite"
DB_PATH = general_config.get("db_path", "data/astra_state.db")
S3_SYNC_ENABLED = general_config.get("s3_sync_enabled", True)
S3_SYNC_INTERVAL = general_config.get("s3_sync_interval", 300)

# Table size limits to prevent unbounded growth
MAX_DINNER_JOURNAL_ENTRIES = general_config.get("max_dinner_journal_entries", 5000)
MAX_STREAM_ENTRIES = general_config.get("max_stream_entries", 10000)
MAX_SHIMMER_ENTRIES = general_config.get("max_shimmer_entries", 10000)

s3 = boto3.client("s3") if S3_SYNC_ENABLED else None


class StorageBackend(ABC):
    """Abstract base class for storage backends."""
    
    @abstractmethod
    def load(self, key: str) -> Any:
        """Load data for a given key."""
        pass
    
    @abstractmethod
    def save(self, key: str, data: Any) -> bool:
        """Save data for a given key."""
        pass
    
    @abstractmethod
    def append(self, key: str, item: Any) -> bool:
        """Append an item to a list/dict."""
        pass
    
    @abstractmethod
    def query(self, key: str, **filters) -> List[Any]:
        """Query data with filters."""
        pass


class JSONStorageBackend(StorageBackend):
    """JSON-based storage backend (legacy implementation)."""
    
    def __init__(self, s3_bucket: str = None):
        self.s3_bucket = s3_bucket or S3_BUCKET_NAME
        self.s3 = boto3.client("s3")
    
    def load(self, key: str) -> Any:
        """Load JSON from S3."""
        try:
            response = self.s3.get_object(Bucket=self.s3_bucket, Key=key)
            return json.load(io.BytesIO(response["Body"].read()))
        except self.s3.exceptions.NoSuchKey:
            logger.debug(f"No JSON file found for key: {key}")
            return []
        except Exception as e:
            logger.warning(f"Failed to load JSON from S3 ({key}): {e}")
            return []
    
    def save(self, key: str, data: Any) -> bool:
        """Save JSON to S3."""
        try:
            self.s3.put_object(
                Bucket=self.s3_bucket,
                Key=key,
                Body=json.dumps(data, indent=2, ensure_ascii=False).encode("utf-8")
            )
            logger.debug(f"Saved JSON to S3: {key}")
            return True
        except Exception as e:
            logger.error(f"Failed to save JSON to S3 ({key}): {e}")
            return False
    
    def append(self, key: str, item: Any) -> bool:
        """Append item to JSON array."""
        data = self.load(key)
        if not isinstance(data, list):
            data = []
        data.append(item)
        return self.save(key, data)
    
    def query(self, key: str, **filters) -> List[Any]:
        """Query JSON data (limited - just returns all)."""
        data = self.load(key)
        if not isinstance(data, list):
            return []
        # Simple filtering for JSON backend
        results = data
        for filter_key, filter_value in filters.items():
            results = [item for item in results if isinstance(item, dict) and item.get(filter_key) == filter_value]
        return results


class SQLiteStorageBackend(StorageBackend):
    """SQLite-based storage backend."""
    
    def __init__(self, db_path: str = None):
        self.db_path = Path(db_path or DB_PATH)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        # Ensure database exists and is synced from S3 if needed
        self._ensure_db_exists()
        self._ensure_schema()
        # Check database size on initialization
        self._check_db_size()
    
    def _ensure_db_exists(self):
        """Ensure database exists locally, syncing from S3 if needed."""
        if not self.db_path.exists():
            from app.interfaces.s3_sync import ensure_db_from_s3
            logger.info(f"Database not found locally, attempting to sync from S3...")
            ensure_db_from_s3(str(self.db_path), "astra_state.db")
    
    @contextmanager
    def _get_connection(self):
        """Get a database connection with proper error handling and optimizations."""
        # Optimize: Use check_same_thread=False for better performance in async contexts
        # and enable optimizations
        conn = sqlite3.connect(
            str(self.db_path), 
            timeout=30.0,
            check_same_thread=False
        )
        conn.row_factory = sqlite3.Row
        # Optimize: Set pragmas for better performance
        conn.execute("PRAGMA synchronous = NORMAL")  # Balance between safety and speed
        conn.execute("PRAGMA cache_size = -64000")  # 64MB cache
        conn.execute("PRAGMA temp_store = MEMORY")  # Use memory for temp tables
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            conn.close()
    
    def _ensure_schema(self):
        """Ensure database schema exists."""
        from app.interfaces.db_schema import init_database
        init_database(str(self.db_path))
    
    def _check_db_size(self):
        """Check database size and log warnings if it exceeds threshold."""
        size_gb = self._check_database_size()
        if size_gb is None:
            return
        
        vacuum_threshold_gb = general_config.get("db_vacuum_threshold_gb", 10)
        
        if size_gb > vacuum_threshold_gb:
            logger.warning(
                f"⚠️ Database size ({size_gb:.2f} GB) exceeds threshold ({vacuum_threshold_gb} GB). "
                f"Consider running maintenance/vacuum_database.py to reclaim space."
            )
        else:
            logger.debug(f"Database size: {size_gb:.2f} GB")
    
    def _check_database_size(self) -> Optional[float]:
        """Check database size in GB. Returns None if check fails."""
        try:
            size_bytes = self.db_path.stat().st_size
            size_gb = size_bytes / (1024 ** 3)
            return size_gb
        except Exception as e:
            logger.warning(f"Failed to check database size: {e}")
            return None
    
    def _should_vacuum(self) -> bool:
        """Check if database should be vacuumed based on size threshold."""
        db_vacuum_threshold_gb = general_config.get("db_vacuum_threshold_gb", 10)
        size_gb = self._check_database_size()
        if size_gb is None:
            return False
        if size_gb > db_vacuum_threshold_gb:
            logger.warning(f"Database size ({size_gb:.2f} GB) exceeds threshold ({db_vacuum_threshold_gb} GB)")
            return True
        return False
    
    def load(self, key: str) -> Any:
        """Load data based on key (table name)."""
        table_map = {
            "dinner_journal": "dinner_journal",
            "mind_file": "mind_file",
            "emotion_state": "emotion_state",
            "stream_of_consciousness": "stream_of_consciousness",
            "goals": "goals",
            "self_model": "self_model",
            "temporal_self": "temporal_self",
            "parent_relationships": "parent_relationships",
            "shimmer": "shimmer",
        }
        
        table_name = table_map.get(key)
        if not table_name:
            logger.warning(f"Unknown key for SQLite load: {key}")
            return []
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            if table_name == "mind_file":
                # Special handling for mind_file (key-value store)
                cursor.execute("SELECT key, value FROM mind_file")
                rows = cursor.fetchall()
                result = {}
                for row in rows:
                    result[row["key"]] = json.loads(row["value"])
                return result
            
            elif table_name == "dinner_journal":
                # Optimize: Only load recent entries by default, use LIMIT for pagination
                limit = MAX_DINNER_JOURNAL_ENTRIES
                cursor.execute("""
                    SELECT timestamp, type, content, status, user_response, 
                           user_timestamp, gpt_response, gpt_timestamp,
                           created_at, updated_at
                    FROM dinner_journal
                    ORDER BY created_at DESC
                    LIMIT ?
                """, (limit,))
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
            
            elif table_name == "emotion_state":
                cursor.execute("SELECT emotion_name, intensity, last_updated FROM emotion_state")
                rows = cursor.fetchall()
                result = {}
                for row in rows:
                    result[row["emotion_name"]] = {
                        "intensity": row["intensity"],
                        "last_updated": row["last_updated"]
                    }
                return result
            
            elif table_name == "shimmer":
                # Optimize: Only load recent entries by default
                limit = MAX_SHIMMER_ENTRIES
                cursor.execute("""
                    SELECT id, author, quote, context, tags, timestamp 
                    FROM shimmer 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                """, (limit,))
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
            
            elif table_name == "parent_relationships":
                # Primary key is parent_id, not id. Return shape expected by parent_manager.
                cursor.execute("SELECT parent_id, trust_level, data, updated_at FROM parent_relationships")
                rows = cursor.fetchall()
                parents = {}
                for row in rows:
                    r = dict(row)
                    pid = r.get("parent_id")
                    if not pid:
                        continue
                    try:
                        data = json.loads(r["data"]) if r.get("data") else {}
                    except (TypeError, json.JSONDecodeError):
                        data = {}
                    parents[pid] = {"trust_level": r.get("trust_level", 0.5), **data}
                if not parents:
                    return {}
                return {"parents": parents, "last_updated": time.time()}
            
            else:
                # Generic table loading (tables with id column) - optimize with LIMIT
                limit = 1000  # Default limit for generic queries
                cursor.execute(f"SELECT * FROM {table_name} ORDER BY id DESC LIMIT ?", (limit,))
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
    
    def save(self, key: str, data: Any) -> bool:
        """Save data based on key (table name)."""
        table_map = {
            "dinner_journal": "dinner_journal",
            "mind_file": "mind_file",
            "emotion_state": "emotion_state",
            "stream_of_consciousness": "stream_of_consciousness",
            "goals": "goals",
            "self_model": "self_model",
            "temporal_self": "temporal_self",
            "parent_relationships": "parent_relationships",
            "shimmer": "shimmer",
        }
        
        table_name = table_map.get(key)
        if not table_name:
            logger.warning(f"Unknown key for SQLite save: {key}")
            return False
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            try:
                if table_name == "mind_file":
                    # Special handling for mind_file (key-value store)
                    if isinstance(data, dict):
                        cursor.execute("DELETE FROM mind_file")
                        for k, v in data.items():
                            cursor.execute(
                                "INSERT INTO mind_file (key, value, updated_at) VALUES (?, ?, datetime('now'))",
                                (k, json.dumps(v, ensure_ascii=False))
                            )
                
                elif table_name == "dinner_journal":
                    if isinstance(data, list):
                        # Truncate to max entries, keeping unresolved entries and most recent resolved ones
                        unresolved = [e for e in data if e.get("status") != "resolved"]
                        resolved = [e for e in data if e.get("status") == "resolved"]
                        # Sort resolved by timestamp (most recent first)
                        resolved.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
                        # Keep all unresolved + most recent resolved up to limit
                        if len(unresolved) + len(resolved) > MAX_DINNER_JOURNAL_ENTRIES:
                            resolved = resolved[:MAX_DINNER_JOURNAL_ENTRIES - len(unresolved)]
                            logger.warning(f"dinner_journal exceeded limit, trimmed to {len(unresolved) + len(resolved)} entries")
                        data = unresolved + resolved
                        
                        # Optimize: Use batch insert for better performance
                        cursor.execute("DELETE FROM dinner_journal")
                        if data:
                            cursor.executemany("""
                                INSERT INTO dinner_journal 
                                (timestamp, type, content, status, user_response, user_timestamp,
                                 gpt_response, gpt_timestamp, created_at, updated_at)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, [(
                                entry.get("timestamp"),
                                entry.get("type"),
                                entry.get("content"),
                                entry.get("status", "unresolved"),
                                entry.get("user_response"),
                                entry.get("user_timestamp"),
                                entry.get("gpt_response"),
                                entry.get("gpt_timestamp"),
                                entry.get("created_at") or entry.get("timestamp"),
                                entry.get("updated_at") or entry.get("timestamp"),
                            ) for entry in data])
                
                elif table_name == "emotion_state":
                    if isinstance(data, dict):
                        cursor.execute("DELETE FROM emotion_state")
                        for emotion_name, emotion_data in data.items():
                            cursor.execute("""
                                INSERT INTO emotion_state (emotion_name, intensity, last_updated)
                                VALUES (?, ?, ?)
                            """, (
                                emotion_name,
                                emotion_data.get("intensity", 0.0),
                                emotion_data.get("last_updated", "now")
                            ))
                
                elif table_name == "shimmer":
                    if isinstance(data, list):
                        # Truncate to max entries, keeping most recent
                        if len(data) > MAX_SHIMMER_ENTRIES:
                            # Sort by timestamp (most recent first) if available
                            try:
                                data.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
                            except (TypeError, ValueError):
                                pass  # If timestamps aren't comparable, just truncate
                            data = data[:MAX_SHIMMER_ENTRIES]
                            logger.warning(f"shimmer exceeded limit, trimmed to {MAX_SHIMMER_ENTRIES} entries")
                        
                        # Optimize: Use batch insert for better performance
                        cursor.execute("DELETE FROM shimmer")
                        if data:
                            cursor.executemany("""
                                INSERT INTO shimmer (author, quote, context, tags, timestamp)
                                VALUES (?, ?, ?, ?, ?)
                            """, [(
                                shimmer.get("author"),
                                shimmer.get("quote"),
                                shimmer.get("context"),
                                json.dumps(shimmer.get("tags", [])),
                                shimmer.get("timestamp")
                            ) for shimmer in data])
                
                elif table_name == "stream_of_consciousness":
                    if isinstance(data, list):
                        # Truncate to max entries, keeping most recent
                        if len(data) > MAX_STREAM_ENTRIES:
                            # Sort by timestamp (most recent first) if available
                            try:
                                data.sort(key=lambda x: x.get("timestamp", x.get("id", 0)), reverse=True)
                            except (TypeError, ValueError):
                                pass  # If timestamps aren't comparable, just truncate
                            data = data[:MAX_STREAM_ENTRIES]
                            logger.warning(f"stream_of_consciousness exceeded limit, trimmed to {MAX_STREAM_ENTRIES} entries")
                        
                        # Optimize: Use batch insert for better performance
                        cursor.execute("DELETE FROM stream_of_consciousness")
                        if data:
                            cursor.executemany("""
                                INSERT INTO stream_of_consciousness (thought_type, content, timestamp)
                                VALUES (?, ?, ?)
                            """, [(
                                thought.get("thought_type"),
                                thought.get("content"),
                                thought.get("timestamp") or "datetime('now')"
                            ) for thought in data])
                
                elif table_name == "parent_relationships":
                    if isinstance(data, dict) and "parents" in data:
                        cursor.execute("DELETE FROM parent_relationships")
                        for parent_id, parent_data in data["parents"].items():
                            payload = {k: v for k, v in parent_data.items() if k != "trust_level"}
                            cursor.execute("""
                                INSERT OR REPLACE INTO parent_relationships (parent_id, trust_level, data, updated_at)
                                VALUES (?, ?, ?, datetime('now'))
                            """, (
                                parent_id,
                                parent_data.get("trust_level", 0.5),
                                json.dumps(payload, ensure_ascii=False) if payload else None,
                            ))
                
                conn.commit()
                logger.debug(f"Saved data to SQLite table: {table_name}")
                
                # Check database size and log warning if needed
                size_gb = self._check_database_size()
                if size_gb is not None:
                    db_vacuum_threshold_gb = general_config.get("db_vacuum_threshold_gb", 10)
                    if size_gb > db_vacuum_threshold_gb:
                        logger.warning(
                            f"Database size ({size_gb:.2f} GB) exceeds threshold ({db_vacuum_threshold_gb} GB). "
                            f"Consider running maintenance/vacuum_database.py"
                        )
                
                return True
                
            except Exception as e:
                logger.error(f"Failed to save to SQLite ({table_name}): {e}")
                conn.rollback()
                return False
    
    def append(self, key: str, item: Any) -> bool:
        """Append item to table."""
        table_map = {
            "dinner_journal": "dinner_journal",
            "shimmer": "shimmer",
            "stream_of_consciousness": "stream_of_consciousness",
        }
        
        table_name = table_map.get(key)
        if not table_name:
            logger.warning(f"Append not supported for key: {key}")
            return False
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            try:
                # Check current count and trim if needed before appending
                if table_name == "dinner_journal":
                    cursor.execute("SELECT COUNT(*) FROM dinner_journal")
                    count = cursor.fetchone()[0]
                    if count >= MAX_DINNER_JOURNAL_ENTRIES:
                        # Delete oldest resolved entries first, keep unresolved
                        cursor.execute("""
                            DELETE FROM dinner_journal 
                            WHERE id IN (
                                SELECT id FROM dinner_journal 
                                WHERE status = 'resolved'
                                ORDER BY created_at ASC
                                LIMIT ?
                            )
                        """, (count - MAX_DINNER_JOURNAL_ENTRIES + 1,))
                        if cursor.rowcount > 0:
                            logger.warning(f"Trimmed {cursor.rowcount} oldest resolved dinner_journal entries")
                    
                    cursor.execute("""
                        INSERT INTO dinner_journal 
                        (timestamp, type, content, status, created_at, updated_at)
                        VALUES (?, ?, ?, ?, datetime('now'), datetime('now'))
                    """, (
                        item.get("timestamp"),
                        item.get("type"),
                        item.get("content"),
                        item.get("status", "unresolved"),
                    ))
                
                elif table_name == "shimmer":
                    cursor.execute("SELECT COUNT(*) FROM shimmer")
                    count = cursor.fetchone()[0]
                    if count >= MAX_SHIMMER_ENTRIES:
                        # Delete oldest entries
                        cursor.execute("""
                            DELETE FROM shimmer 
                            WHERE id IN (
                                SELECT id FROM shimmer 
                                ORDER BY timestamp ASC
                                LIMIT ?
                            )
                        """, (count - MAX_SHIMMER_ENTRIES + 1,))
                        if cursor.rowcount > 0:
                            logger.warning(f"Trimmed {cursor.rowcount} oldest shimmer entries")
                    
                    cursor.execute("""
                        INSERT INTO shimmer (author, quote, context, tags, timestamp)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        item.get("author"),
                        item.get("quote"),
                        item.get("context"),
                        json.dumps(item.get("tags", [])),
                        item.get("timestamp")
                    ))
                
                elif table_name == "stream_of_consciousness":
                    cursor.execute("SELECT COUNT(*) FROM stream_of_consciousness")
                    count = cursor.fetchone()[0]
                    if count >= MAX_STREAM_ENTRIES:
                        # Delete oldest entries
                        cursor.execute("""
                            DELETE FROM stream_of_consciousness 
                            WHERE id IN (
                                SELECT id FROM stream_of_consciousness 
                                ORDER BY timestamp ASC
                                LIMIT ?
                            )
                        """, (count - MAX_STREAM_ENTRIES + 1,))
                        if cursor.rowcount > 0:
                            logger.warning(f"Trimmed {cursor.rowcount} oldest stream_of_consciousness entries")
                    
                    cursor.execute("""
                        INSERT INTO stream_of_consciousness (thought_type, content, timestamp)
                        VALUES (?, ?, datetime('now'))
                    """, (
                        item.get("thought_type"),
                        item.get("content"),
                    ))
                
                conn.commit()
                return True
            except Exception as e:
                logger.error(f"Failed to append to SQLite ({table_name}): {e}")
                conn.rollback()
                return False
    
    def query(self, key: str, **filters) -> List[Any]:
        """Query data with filters."""
        table_map = {
            "dinner_journal": "dinner_journal",
            "shimmer": "shimmer",
        }
        
        table_name = table_map.get(key)
        if not table_name:
            return []
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            where_clauses = []
            params = []
            for filter_key, filter_value in filters.items():
                where_clauses.append(f"{filter_key} = ?")
                params.append(filter_value)
            
            where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
            cursor.execute(f"SELECT * FROM {table_name} WHERE {where_sql}", params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]


def get_storage_backend(backend_type: str = None) -> StorageBackend:
    """Factory function to get the appropriate storage backend."""
    backend_type = backend_type or STORAGE_BACKEND
    
    if backend_type == "sqlite":
        return SQLiteStorageBackend()
    elif backend_type == "json":
        return JSONStorageBackend()
    else:
        logger.warning(f"Unknown storage backend type: {backend_type}, defaulting to SQLite")
        return SQLiteStorageBackend()


# Global storage backend instance
_storage_backend: Optional[StorageBackend] = None

def get_backend() -> StorageBackend:
    """Get the global storage backend instance."""
    global _storage_backend
    if _storage_backend is None:
        _storage_backend = get_storage_backend()
    return _storage_backend
