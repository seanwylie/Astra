#!/usr/bin/env python3
"""
Migration script to convert Astra's JSON state files to SQLite database.

This script:
1. Downloads all JSON files from S3 (or uses local files)
2. Converts each JSON file to SQLite tables
3. Uploads SQLite database to S3
4. Creates backup of original JSON files
5. Verifies data integrity
"""

import sys
import os
import json
import boto3
import argparse
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.interfaces.db_schema import init_database
from app.interfaces.migrations import migrate_json_to_sqlite, migrate_local_json_to_sqlite
from app.interfaces.s3_sync import sync_db_to_s3, backup_database
from app.config.loader import load_config
from app.logging_config import setup_logging, get_logger

setup_logging(level="INFO")
logger = get_logger("migrate_to_sqlite")

general_config = load_config("general_config")
S3_BUCKET_NAME = general_config.get("s3_bucket", "swylie-astra")
DB_PATH = general_config.get("db_path", "data/astra_state.db")
s3 = boto3.client("s3")


# Migration mappings: (s3_key, table_name, description)
MIGRATION_MAPPINGS = [
    ("mind_file.json", "mind_file", "Main memory and knowledge store"),
    ("dinner_journal.json", "dinner_journal", "Ethical topics for dinner"),
    ("emotional_state.json", "emotion_state", "Current emotional intensities"),
    ("stream_of_consciousness.json", "stream_of_consciousness", "Inner thoughts"),
    ("self_model.json", "self_model", "Self-understanding"),
    ("temporal_self.json", "temporal_self", "Temporal landmarks"),
    ("goals.json", "goals", "Active goals"),
    ("parent_relationships_state.json", "parent_relationships", "Parent relationships"),
]

# Local files
LOCAL_MIGRATIONS = [
    ("app/shimmer/shimmer.json", "shimmer", "Shimmer insights"),
]


def backup_json_files():
    """Create backups of all JSON files in S3."""
    logger.info("Creating backups of JSON files in S3...")
    timestamp = __import__("datetime").datetime.now().strftime("%Y%m%d_%H%M%S")
    
    for s3_key, _, _ in MIGRATION_MAPPINGS:
        try:
            backup_key = f"backups/{timestamp}/{s3_key}"
            # Copy object
            copy_source = {"Bucket": S3_BUCKET_NAME, "Key": s3_key}
            try:
                s3.copy_object(CopySource=copy_source, Bucket=S3_BUCKET_NAME, Key=backup_key)
                logger.info(f"Backed up {s3_key} to {backup_key}")
            except s3.exceptions.NoSuchKey:
                logger.warning(f"JSON file not found in S3: {s3_key}, skipping backup")
        except Exception as e:
            logger.error(f"Failed to backup {s3_key}: {e}")
    
    logger.info("JSON file backups completed")


def migrate_all_json_to_sqlite(dry_run=False):
    """Migrate all JSON files to SQLite."""
    logger.info(f"Starting migration to SQLite (dry_run={dry_run})...")
    
    # Initialize database
    logger.info(f"Initializing database at {DB_PATH}")
    init_database(DB_PATH)
    
    success_count = 0
    fail_count = 0
    
    # Migrate S3 JSON files
    for s3_key, table_name, description in MIGRATION_MAPPINGS:
        logger.info(f"Migrating {description} ({s3_key} -> {table_name})...")
        
        if dry_run:
            logger.info(f"  [DRY RUN] Would migrate {s3_key} to {table_name}")
            continue
        
        success = migrate_json_to_sqlite(s3_key, table_name, DB_PATH)
        if success:
            success_count += 1
            logger.info(f"  ✓ Successfully migrated {s3_key}")
        else:
            fail_count += 1
            logger.warning(f"  ✗ Failed to migrate {s3_key}")
    
    # Migrate local JSON files
    for local_path, table_name, description in LOCAL_MIGRATIONS:
        full_path = project_root / local_path
        logger.info(f"Migrating {description} ({local_path} -> {table_name})...")
        
        if dry_run:
            logger.info(f"  [DRY RUN] Would migrate {local_path} to {table_name}")
            continue
        
        success = migrate_local_json_to_sqlite(str(full_path), table_name, DB_PATH)
        if success:
            success_count += 1
            logger.info(f"  ✓ Successfully migrated {local_path}")
        else:
            fail_count += 1
            logger.warning(f"  ✗ Failed to migrate {local_path}")
    
    logger.info(f"Migration completed: {success_count} succeeded, {fail_count} failed")
    return success_count, fail_count


def verify_migration():
    """Verify that migration was successful by checking data counts."""
    logger.info("Verifying migration...")
    
    import sqlite3
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        # Check each table
        tables = ["mind_file", "dinner_journal", "emotion_state", "shimmer"]
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
                count = cursor.fetchone()["count"]
                logger.info(f"  {table}: {count} rows")
            except Exception as e:
                logger.warning(f"  {table}: Error checking - {e}")
        
        logger.info("Verification completed")
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(description="Migrate Astra state from JSON to SQLite")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be migrated without making changes")
    parser.add_argument("--skip-backup", action="store_true", help="Skip creating backups of JSON files")
    parser.add_argument("--skip-verify", action="store_true", help="Skip verification after migration")
    parser.add_argument("--skip-s3-upload", action="store_true", help="Skip uploading SQLite DB to S3")
    
    args = parser.parse_args()
    
    logger.info("=" * 60)
    logger.info("Astra SQLite Migration Script")
    logger.info("=" * 60)
    
    # Create backups
    if not args.skip_backup and not args.dry_run:
        backup_json_files()
    
    # Migrate
    success_count, fail_count = migrate_all_json_to_sqlite(dry_run=args.dry_run)
    
    if args.dry_run:
        logger.info("Dry run completed. No changes made.")
        return
    
    # Verify
    if not args.skip_verify:
        verify_migration()
    
    # Upload to S3
    if not args.skip_s3_upload:
        logger.info("Uploading SQLite database to S3...")
        success = sync_db_to_s3(DB_PATH, "astra_state.db")
        if success:
            logger.info("✓ Database uploaded to S3")
        else:
            logger.warning("✗ Failed to upload database to S3")
    
    # Create local backup
    logger.info("Creating local backup of database...")
    backup_path = backup_database(DB_PATH)
    if backup_path:
        logger.info(f"✓ Local backup created: {backup_path}")
    
    logger.info("=" * 60)
    logger.info("Migration script completed!")
    logger.info(f"Database location: {DB_PATH}")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
