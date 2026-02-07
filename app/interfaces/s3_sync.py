"""
S3 Sync utilities for SQLite database files.

Handles syncing SQLite database files to/from S3 for backup and portability.
"""

import boto3
import logging
import shutil
from pathlib import Path
from datetime import datetime
from app.config.loader import load_config
from app.logging_config import get_logger

logger = get_logger("s3_sync")

general_config = load_config("general_config")
S3_BUCKET_NAME = general_config.get("s3_bucket", "swylie-astra")
S3_SYNC_ENABLED = general_config.get("s3_sync_enabled", True)

s3 = boto3.client("s3") if S3_SYNC_ENABLED else None


def sync_db_to_s3(db_path: str, s3_key: str = None) -> bool:
    """
    Upload SQLite database file to S3.
    
    Args:
        db_path: Path to local SQLite database file
        s3_key: S3 key (defaults to database filename)
    
    Returns:
        True if sync successful, False otherwise
    """
    if not S3_SYNC_ENABLED or not s3:
        logger.debug("S3 sync disabled, skipping upload")
        return False
    
    try:
        db_file = Path(db_path)
        if not db_file.exists():
            logger.warning(f"Database file not found: {db_path}")
            return False
        
        if s3_key is None:
            s3_key = db_file.name
        
        logger.info(f"Syncing database to S3: {s3_key}")
        
        # Upload main database file
        with open(db_file, 'rb') as f:
            s3.put_object(
                Bucket=S3_BUCKET_NAME,
                Key=s3_key,
                Body=f
            )
        
        # Also upload WAL and SHM files if they exist
        wal_file = db_file.with_suffix('.db-wal')
        shm_file = db_file.with_suffix('.db-shm')
        
        if wal_file.exists():
            with open(wal_file, 'rb') as f:
                s3.put_object(
                    Bucket=S3_BUCKET_NAME,
                    Key=f"{s3_key}-wal",
                    Body=f
                )
        
        if shm_file.exists():
            with open(shm_file, 'rb') as f:
                s3.put_object(
                    Bucket=S3_BUCKET_NAME,
                    Key=f"{s3_key}-shm",
                    Body=f
                )
        
        logger.info(f"Successfully synced database to S3: {s3_key}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to sync database to S3: {e}")
        return False


def sync_s3_to_db(s3_key: str, db_path: str) -> bool:
    """
    Download SQLite database file from S3.
    
    Args:
        s3_key: S3 key for the database file
        db_path: Local path to save the database
    
    Returns:
        True if sync successful, False otherwise
    """
    if not S3_SYNC_ENABLED or not s3:
        logger.debug("S3 sync disabled, skipping download")
        return False
    
    try:
        db_file = Path(db_path)
        db_file.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Syncing database from S3: {s3_key}")
        
        # Download main database file
        try:
            response = s3.get_object(Bucket=S3_BUCKET_NAME, Key=s3_key)
            with open(db_file, 'wb') as f:
                f.write(response['Body'].read())
        except s3.exceptions.NoSuchKey:
            logger.warning(f"Database not found in S3: {s3_key}")
            return False
        
        # Also download WAL and SHM files if they exist
        wal_key = f"{s3_key}-wal"
        shm_key = f"{s3_key}-shm"
        
        try:
            response = s3.get_object(Bucket=S3_BUCKET_NAME, Key=wal_key)
            wal_file = db_file.with_suffix('.db-wal')
            with open(wal_file, 'wb') as f:
                f.write(response['Body'].read())
        except s3.exceptions.NoSuchKey:
            pass  # WAL file is optional
        
        try:
            response = s3.get_object(Bucket=S3_BUCKET_NAME, Key=shm_key)
            shm_file = db_file.with_suffix('.db-shm')
            with open(shm_file, 'wb') as f:
                f.write(response['Body'].read())
        except s3.exceptions.NoSuchKey:
            pass  # SHM file is optional
        
        logger.info(f"Successfully synced database from S3: {s3_key}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to sync database from S3: {e}")
        return False


def backup_database(db_path: str) -> str:
    """
    Create a timestamped backup of the database file.
    
    Args:
        db_path: Path to database file
    
    Returns:
        Path to backup file, or empty string if backup failed
    """
    try:
        db_file = Path(db_path)
        if not db_file.exists():
            logger.warning(f"Database file not found for backup: {db_path}")
            return ""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = db_file.parent / f"{db_file.stem}_backup_{timestamp}{db_file.suffix}"
        
        shutil.copy2(db_file, backup_path)
        
        logger.info(f"Created database backup: {backup_path}")
        return str(backup_path)
        
    except Exception as e:
        logger.error(f"Failed to create database backup: {e}")
        return ""


def ensure_db_from_s3(db_path: str, s3_key: str = None) -> bool:
    """
    Ensure database exists locally, downloading from S3 if needed.
    
    Args:
        db_path: Local path to database
        s3_key: S3 key (defaults to database filename)
    
    Returns:
        True if database exists locally (either was there or downloaded)
    """
    db_file = Path(db_path)
    
    if db_file.exists():
        logger.debug(f"Database already exists locally: {db_path}")
        return True
    
    if s3_key is None:
        s3_key = db_file.name
    
    logger.info(f"Database not found locally, attempting to download from S3: {s3_key}")
    return sync_s3_to_db(s3_key, db_path)
