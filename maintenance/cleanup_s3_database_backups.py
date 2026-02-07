#!/usr/bin/env python3
"""
Cleanup S3 Database Backups

Deletes giant database backup files from S3 that are no longer needed
since we're only backing up JSON files, not the entire database.
"""

import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import boto3
import argparse
from app.config.loader import load_config
from app.logging_config import get_logger

logger = get_logger("cleanup_s3_backups")

general_config = load_config("general_config")
S3_BUCKET_NAME = general_config.get("s3_bucket", "swylie-astra")

# Files to delete
FILES_TO_DELETE = [
    "astra_state.db",
    "astra_state.db-wal",
    "astra_state.db-shm"
]


def list_s3_files(s3_client, bucket: str, prefix: str = "") -> list:
    """List all files in S3 bucket with given prefix."""
    try:
        response = s3_client.list_objects_v2(Bucket=bucket, Prefix=prefix)
        if "Contents" not in response:
            return []
        return [obj["Key"] for obj in response["Contents"]]
    except Exception as e:
        logger.error(f"Failed to list S3 files: {e}")
        return []


def get_file_size(s3_client, bucket: str, key: str) -> int:
    """Get size of file in S3."""
    try:
        response = s3_client.head_object(Bucket=bucket, Key=key)
        return response.get("ContentLength", 0)
    except Exception as e:
        logger.warning(f"Failed to get size for {key}: {e}")
        return 0


def format_size(bytes: int) -> str:
    """Format bytes to human-readable size."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if bytes < 1024.0:
            return f"{bytes:.2f} {unit}"
        bytes /= 1024.0
    return f"{bytes:.2f} PB"


def cleanup_s3_database_backups(dry_run: bool = True) -> dict:
    """
    Delete database backup files from S3.
    
    Args:
        dry_run: If True, only list files without deleting
    
    Returns:
        Dict with deletion results
    """
    s3_client = boto3.client("s3")
    
    # List all files in bucket
    all_files = list_s3_files(s3_client, S3_BUCKET_NAME)
    
    results = {
        "found": [],
        "deleted": [],
        "failed": [],
        "total_size_freed": 0
    }
    
    for file_key in FILES_TO_DELETE:
        if file_key in all_files:
            size = get_file_size(s3_client, S3_BUCKET_NAME, file_key)
            results["found"].append({
                "key": file_key,
                "size": size,
                "size_formatted": format_size(size)
            })
            
            if not dry_run:
                try:
                    s3_client.delete_object(Bucket=S3_BUCKET_NAME, Key=file_key)
                    results["deleted"].append(file_key)
                    results["total_size_freed"] += size
                    logger.info(f"✅ Deleted {file_key} ({format_size(size)})")
                except Exception as e:
                    results["failed"].append({"key": file_key, "error": str(e)})
                    logger.error(f"❌ Failed to delete {file_key}: {e}")
            else:
                logger.info(f"🔍 Would delete {file_key} ({format_size(size)})")
    
    return results


def main():
    parser = argparse.ArgumentParser(description="Cleanup S3 database backups")
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually delete files (default is dry-run)"
    )
    args = parser.parse_args()
    
    dry_run = not args.execute
    
    if dry_run:
        print("🔍 DRY RUN MODE - No files will be deleted")
        print("=" * 60)
    else:
        print("⚠️  EXECUTION MODE - Files will be deleted!")
        print("=" * 60)
        response = input("Are you sure you want to delete database backups from S3? (yes/no): ")
        if response.lower() != "yes":
            print("Aborted.")
            return
    
    print(f"\n📦 S3 Bucket: {S3_BUCKET_NAME}")
    print(f"🗑️  Files to delete: {', '.join(FILES_TO_DELETE)}\n")
    
    results = cleanup_s3_database_backups(dry_run=dry_run)
    
    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)
    
    if results["found"]:
        print(f"\n📋 Found {len(results['found'])} file(s):")
        for file_info in results["found"]:
            print(f"  - {file_info['key']}: {file_info['size_formatted']}")
        
        if dry_run:
            print(f"\n💡 Total size that would be freed: {format_size(sum(f['size'] for f in results['found']))}")
        else:
            print(f"\n✅ Deleted {len(results['deleted'])} file(s)")
            print(f"💾 Total size freed: {format_size(results['total_size_freed'])}")
            
            if results["failed"]:
                print(f"\n❌ Failed to delete {len(results['failed'])} file(s):")
                for fail in results["failed"]:
                    print(f"  - {fail['key']}: {fail['error']}")
    else:
        print("\n✅ No database backup files found in S3 (already cleaned up or never existed)")


if __name__ == "__main__":
    main()
