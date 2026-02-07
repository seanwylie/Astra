"""
SQLite to JSON Export for Optional Files

Exports SQLite-only optional files to JSON format and backs them up to S3.
This ensures optional files (self_model, parent_relationships, etc.) are backed up
even if they're only stored in SQLite.
"""

import json
import sqlite3
import boto3
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from app.config.loader import load_config
from app.logging_config import get_logger

logger = get_logger("sqlite_json_export")

general_config = load_config("general_config")
S3_BUCKET_NAME = general_config.get("s3_bucket", "swylie-astra")
DB_PATH = general_config.get("db_path", "data/astra_state.db")
s3 = boto3.client("s3")


def export_self_model_to_json(db_path: str) -> Optional[Dict[str, Any]]:
    """
    Export self_model table from SQLite to self_model.json format.
    
    Returns:
        Dict in self_model.json format, or None if export failed
    """
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Load all self_model entries
        cursor.execute("SELECT snapshot_type, data, timestamp FROM self_model ORDER BY timestamp DESC")
        rows = cursor.fetchall()
        
        if not rows:
            logger.debug("No self_model entries found in SQLite")
            conn.close()
            return None
        
        # Parse JSON data and organize by type
        current_model = None
        historical_snapshots = []
        changes = []
        surprise_log = []
        
        for row in rows:
            try:
                data = json.loads(row["data"]) if row["data"] else {}
                entry = {**data, "timestamp": row["timestamp"]}
                
                snapshot_type = row["snapshot_type"]
                if snapshot_type == "current":
                    current_model = entry
                elif snapshot_type == "historical":
                    historical_snapshots.append(entry)
                elif snapshot_type == "change":
                    changes.append(entry)
                elif snapshot_type == "surprise":
                    surprise_log.append(entry)
            except (json.JSONDecodeError, TypeError) as e:
                logger.warning(f"Failed to parse self_model entry: {e}")
                continue
        
        # Keep only recent entries (matching limits from SelfModel)
        historical_snapshots = historical_snapshots[:50]
        changes = changes[:100]
        surprise_log = surprise_log[:50]
        
        result = {
            "current_model": current_model,
            "historical_snapshots": historical_snapshots,
            "changes": changes,
            "surprise_log": surprise_log,
            "last_updated": historical_snapshots[0]["timestamp"] if historical_snapshots else None
        }
        
        conn.close()
        logger.debug(f"Exported {len(historical_snapshots)} snapshots, {len(changes)} changes, {len(surprise_log)} surprises")
        return result
        
    except Exception as e:
        logger.error(f"Failed to export self_model from SQLite: {e}")
        return None


def export_parent_relationships_to_json(db_path: str) -> Optional[Dict[str, Any]]:
    """
    Export parent_relationships table from SQLite to JSON format.
    
    Returns:
        Dict in parent_relationships format, or None if export failed
    """
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT parent_id, trust_level, data, updated_at FROM parent_relationships")
        rows = cursor.fetchall()
        
        if not rows:
            logger.debug("No parent_relationships found in SQLite")
            conn.close()
            return None
        
        parents = {}
        for row in rows:
            pid = row["parent_id"]
            if not pid:
                continue
            
            try:
                data = json.loads(row["data"]) if row["data"] else {}
            except (json.JSONDecodeError, TypeError):
                data = {}
            
            parents[pid] = {
                "trust_level": row["trust_level"],
                **data
            }
        
        result = {
            "parents": parents,
            "last_updated": rows[0]["updated_at"] if rows else None
        }
        
        conn.close()
        logger.debug(f"Exported {len(parents)} parent relationships")
        return result
        
    except Exception as e:
        logger.error(f"Failed to export parent_relationships from SQLite: {e}")
        return None


def export_optional_files_to_s3(db_path: Optional[str] = None) -> Dict[str, bool]:
    """
    Export all optional SQLite tables to JSON and upload to S3.
    
    Args:
        db_path: Path to SQLite database (defaults to config value)
    
    Returns:
        Dict mapping file names to success status
    """
    if db_path is None:
        db_path = DB_PATH
    
    results = {}
    
    # Export self_model if it exists in SQLite
    self_model_data = export_self_model_to_json(db_path)
    if self_model_data:
        try:
            s3.put_object(
                Bucket=S3_BUCKET_NAME,
                Key="self_model.json",
                Body=json.dumps(self_model_data, indent=2).encode("utf-8")
            )
            results["self_model.json"] = True
            logger.info("✅ Exported self_model.json to S3")
        except Exception as e:
            logger.error(f"Failed to upload self_model.json to S3: {e}")
            results["self_model.json"] = False
    else:
        results["self_model.json"] = False
    
    # Export parent_relationships if it exists in SQLite
    parent_data = export_parent_relationships_to_json(db_path)
    if parent_data:
        try:
            s3.put_object(
                Bucket=S3_BUCKET_NAME,
                Key="parent_relationships.json",
                Body=json.dumps(parent_data, indent=2).encode("utf-8")
            )
            results["parent_relationships.json"] = True
            logger.info("✅ Exported parent_relationships.json to S3")
        except Exception as e:
            logger.error(f"Failed to upload parent_relationships.json to S3: {e}")
            results["parent_relationships.json"] = False
    else:
        results["parent_relationships.json"] = False
    
    return results
