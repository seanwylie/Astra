"""
SQLite Database Schema for Astra State Storage

Defines all tables and indexes for storing Astra's state in SQLite.
"""

import sqlite3
import logging
from pathlib import Path
from app.logging_config import get_logger

logger = get_logger("db_schema")


def init_database(db_path: str):
    """Initialize the SQLite database with all required tables and indexes."""
    db_file = Path(db_path)
    db_file.parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    try:
        # Enable foreign keys and WAL mode for better concurrency
        cursor.execute("PRAGMA foreign_keys = ON")
        cursor.execute("PRAGMA journal_mode = WAL")
        
        # mind_file table (key-value store for mind data)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mind_file (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE NOT NULL,
                value TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_mind_file_key ON mind_file(key)")
        
        # dinner_journal table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dinner_journal (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT UNIQUE NOT NULL,
                type TEXT,
                content TEXT,
                status TEXT DEFAULT 'unresolved',
                user_response TEXT,
                user_timestamp TEXT,
                gpt_response TEXT,
                gpt_timestamp TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_dinner_journal_status ON dinner_journal(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_dinner_journal_timestamp ON dinner_journal(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_dinner_journal_created ON dinner_journal(created_at)")
        
        # emotion_state table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS emotion_state (
                emotion_name TEXT PRIMARY KEY,
                intensity REAL DEFAULT 0.0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # stream_of_consciousness table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stream_of_consciousness (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                thought_type TEXT,
                content TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_stream_timestamp ON stream_of_consciousness(timestamp)")
        
        # goals table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                goal_text TEXT NOT NULL,
                status TEXT DEFAULT 'active',
                progress REAL DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_goals_status ON goals(status)")
        
        # self_model table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS self_model (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                snapshot_type TEXT,
                data TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_self_model_type ON self_model(snapshot_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_self_model_timestamp ON self_model(timestamp)")
        
        # temporal_self table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS temporal_self (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                landmark_type TEXT,
                key TEXT,
                value TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_temporal_self_type ON temporal_self(landmark_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_temporal_self_key ON temporal_self(key)")
        
        # parent_relationships table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS parent_relationships (
                parent_id TEXT PRIMARY KEY,
                trust_level REAL DEFAULT 0.5,
                data TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # shimmer table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS shimmer (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                author TEXT NOT NULL,
                quote TEXT NOT NULL,
                context TEXT,
                tags TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_shimmer_author ON shimmer(author)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_shimmer_timestamp ON shimmer(timestamp)")
        
        conn.commit()
        logger.info(f"Database schema initialized: {db_path}")
        
    except Exception as e:
        logger.error(f"Failed to initialize database schema: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


def get_schema_version(db_path: str) -> int:
    """Get the current schema version."""
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    try:
        cursor.execute("PRAGMA user_version")
        version = cursor.fetchone()[0]
        return version
    except Exception:
        return 0
    finally:
        conn.close()


def set_schema_version(db_path: str, version: int):
    """Set the schema version."""
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    try:
        cursor.execute(f"PRAGMA user_version = {version}")
        conn.commit()
    finally:
        conn.close()
