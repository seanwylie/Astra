"""
Migration utilities for converting between JSON and SQLite storage formats.
"""

import json
import sqlite3
import logging
import boto3
import io
from pathlib import Path
from typing import Any, Dict, List
from app.config.loader import load_config
from app.logging_config import get_logger
from app.interfaces.db_schema import init_database

logger = get_logger("migrations")

general_config = load_config("general_config")
S3_BUCKET_NAME = general_config.get("s3_bucket", "swylie-astra")
s3 = boto3.client("s3")


def migrate_json_to_sqlite(json_key: str, table_name: str, db_path: str) -> bool:
    """
    Migrate a JSON file from S3 to SQLite table.
    
    Args:
        json_key: S3 key for the JSON file
        table_name: Target SQLite table name
        db_path: Path to SQLite database
    
    Returns:
        True if migration successful, False otherwise
    """
    try:
        # Ensure database exists
        init_database(db_path)
        
        # Load JSON from S3
        logger.info(f"Loading JSON from S3: {json_key}")
        try:
            response = s3.get_object(Bucket=S3_BUCKET_NAME, Key=json_key)
            json_data = json.load(io.BytesIO(response["Body"].read()))
        except s3.exceptions.NoSuchKey:
            logger.warning(f"JSON file not found in S3: {json_key}, skipping migration")
            return False
        
        # Connect to SQLite
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        try:
            if table_name == "mind_file":
                # Special handling for mind_file
                cursor.execute("DELETE FROM mind_file")
                if isinstance(json_data, dict):
                    for key, value in json_data.items():
                        cursor.execute(
                            "INSERT INTO mind_file (key, value, updated_at) VALUES (?, ?, datetime('now'))",
                            (key, json.dumps(value, ensure_ascii=False))
                        )
            
            elif table_name == "dinner_journal":
                cursor.execute("DELETE FROM dinner_journal")
                if isinstance(json_data, list):
                    for entry in json_data:
                        cursor.execute("""
                            INSERT INTO dinner_journal 
                            (timestamp, type, content, status, user_response, user_timestamp,
                             gpt_response, gpt_timestamp, created_at, updated_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
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
                        ))
            
            elif table_name == "emotion_state":
                cursor.execute("DELETE FROM emotion_state")
                if isinstance(json_data, dict):
                    for emotion_name, emotion_data in json_data.items():
                        cursor.execute("""
                            INSERT INTO emotion_state (emotion_name, intensity, last_updated)
                            VALUES (?, ?, ?)
                        """, (
                            emotion_name,
                            emotion_data.get("intensity", 0.0) if isinstance(emotion_data, dict) else 0.0,
                            emotion_data.get("last_updated", "now") if isinstance(emotion_data, dict) else "now"
                        ))
            
            elif table_name == "shimmer":
                # Handle local shimmer.json file
                if isinstance(json_data, dict) and "shimmers" in json_data:
                    shimmer_list = json_data["shimmers"]
                elif isinstance(json_data, list):
                    shimmer_list = json_data
                else:
                    shimmer_list = []
                
                cursor.execute("DELETE FROM shimmer")
                for shimmer in shimmer_list:
                    cursor.execute("""
                        INSERT INTO shimmer (author, quote, context, tags, timestamp)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        shimmer.get("author"),
                        shimmer.get("quote"),
                        shimmer.get("context"),
                        json.dumps(shimmer.get("tags", [])),
                        shimmer.get("timestamp")
                    ))
            
            conn.commit()
            logger.info(f"Successfully migrated {json_key} to {table_name} table")
            return True
            
        except Exception as e:
            logger.error(f"Error migrating {json_key} to {table_name}: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
            
    except Exception as e:
        logger.error(f"Migration failed for {json_key}: {e}")
        return False


def migrate_sqlite_to_json(db_path: str, table_name: str, json_key: str) -> bool:
    """
    Migrate SQLite table back to JSON format (for rollback).
    
    Args:
        db_path: Path to SQLite database
        table_name: Source SQLite table name
        json_key: Target S3 key for JSON file
    
    Returns:
        True if migration successful, False otherwise
    """
    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            if table_name == "mind_file":
                cursor.execute("SELECT key, value FROM mind_file")
                rows = cursor.fetchall()
                result = {}
                for row in rows:
                    result[row["key"]] = json.loads(row["value"])
            
            elif table_name == "dinner_journal":
                cursor.execute("""
                    SELECT timestamp, type, content, status, user_response, 
                           user_timestamp, gpt_response, gpt_timestamp,
                           created_at, updated_at
                    FROM dinner_journal
                    ORDER BY created_at DESC
                """)
                rows = cursor.fetchall()
                result = [dict(row) for row in rows]
            
            elif table_name == "emotion_state":
                cursor.execute("SELECT emotion_name, intensity, last_updated FROM emotion_state")
                rows = cursor.fetchall()
                result = {}
                for row in rows:
                    result[row["emotion_name"]] = {
                        "intensity": row["intensity"],
                        "last_updated": row["last_updated"]
                    }
            
            elif table_name == "shimmer":
                cursor.execute("SELECT author, quote, context, tags, timestamp FROM shimmer ORDER BY timestamp DESC")
                rows = cursor.fetchall()
                result = {"shimmers": [dict(row) for row in rows]}
            
            else:
                cursor.execute(f"SELECT * FROM {table_name}")
                rows = cursor.fetchall()
                result = [dict(row) for row in rows]
            
            # Save to S3
            json_str = json.dumps(result, indent=2, ensure_ascii=False)
            s3.put_object(
                Bucket=S3_BUCKET_NAME,
                Key=json_key,
                Body=json_str.encode("utf-8")
            )
            
            logger.info(f"Successfully migrated {table_name} to {json_key}")
            return True
            
        except Exception as e:
            logger.error(f"Error migrating {table_name} to {json_key}: {e}")
            return False
        finally:
            conn.close()
            
    except Exception as e:
        logger.error(f"Rollback migration failed for {table_name}: {e}")
        return False


def migrate_local_json_to_sqlite(json_path: str, table_name: str, db_path: str) -> bool:
    """
    Migrate a local JSON file to SQLite table.
    
    Args:
        json_path: Path to local JSON file
        table_name: Target SQLite table name
        db_path: Path to SQLite database
    
    Returns:
        True if migration successful, False otherwise
    """
    try:
        json_file = Path(json_path)
        if not json_file.exists():
            logger.warning(f"JSON file not found: {json_path}, skipping migration")
            return False
        
        with open(json_file, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        
        # Ensure database exists
        init_database(db_path)
        
        # Connect to SQLite
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        try:
            if table_name == "shimmer":
                if isinstance(json_data, dict) and "shimmers" in json_data:
                    shimmer_list = json_data["shimmers"]
                elif isinstance(json_data, list):
                    shimmer_list = json_data
                else:
                    shimmer_list = []
                
                cursor.execute("DELETE FROM shimmer")
                for shimmer in shimmer_list:
                    cursor.execute("""
                        INSERT INTO shimmer (author, quote, context, tags, timestamp)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        shimmer.get("author"),
                        shimmer.get("quote"),
                        shimmer.get("context"),
                        json.dumps(shimmer.get("tags", [])),
                        shimmer.get("timestamp")
                    ))
            
            conn.commit()
            logger.info(f"Successfully migrated local {json_path} to {table_name} table")
            return True
            
        except Exception as e:
            logger.error(f"Error migrating {json_path} to {table_name}: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
            
    except Exception as e:
        logger.error(f"Local migration failed for {json_path}: {e}")
        return False
