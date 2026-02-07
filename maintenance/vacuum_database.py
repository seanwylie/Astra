#!/usr/bin/env python3
"""
Vacuum and optimize the Astra SQLite database to reduce size and improve performance.
Run this periodically to reclaim space from deleted records and optimize indexes.
"""

import sqlite3
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.logging_config import get_logger

logger = get_logger("vacuum_database")

DB_PATH = PROJECT_ROOT / "data" / "astra_state.db"


def get_db_size():
    """Get current database size in GB."""
    if not DB_PATH.exists():
        return 0
    return DB_PATH.stat().st_size / (1024 ** 3)


def vacuum_database():
    """Vacuum the database to reclaim space."""
    if not DB_PATH.exists():
        logger.error(f"Database not found: {DB_PATH}")
        return False
    
    initial_size = get_db_size()
    logger.info(f"📊 Initial database size: {initial_size:.2f} GB")
    
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        # Get table sizes before vacuum
        cursor.execute("""
            SELECT name
            FROM sqlite_master
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
        """)
        tables = cursor.fetchall()
        logger.info(f"📋 Found {len(tables)} tables")
        
        # Analyze tables for better query planning
        logger.info("🔍 Analyzing tables...")
        for (table_name,) in tables:
            try:
                cursor.execute(f"ANALYZE {table_name}")
            except Exception as e:
                logger.warning(f"Failed to analyze {table_name}: {e}")
        
        # Vacuum to reclaim space
        logger.info("🧹 Vacuuming database (this may take a while for large databases)...")
        cursor.execute("VACUUM")
        conn.commit()
        
        # Optimize for better performance
        logger.info("⚡ Optimizing database...")
        cursor.execute("PRAGMA optimize")
        conn.commit()
        
        conn.close()
        
        final_size = get_db_size()
        reclaimed = initial_size - final_size
        
        logger.info(f"✅ Vacuum complete!")
        logger.info(f"📊 Final database size: {final_size:.2f} GB")
        logger.info(f"💾 Space reclaimed: {reclaimed:.2f} GB ({reclaimed/initial_size*100:.1f}%)")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to vacuum database: {e}")
        return False


if __name__ == "__main__":
    print("🧹 Astra Database Vacuum Tool")
    print("=" * 50)
    
    if not DB_PATH.exists():
        print(f"❌ Database not found: {DB_PATH}")
        sys.exit(1)
    
    print(f"📁 Database: {DB_PATH}")
    print(f"📊 Current size: {get_db_size():.2f} GB")
    print()
    
    confirm = input("⚠️  This will lock the database temporarily. Continue? (yes/no): ")
    if confirm.strip().lower() != "yes":
        print("❌ Cancelled.")
        sys.exit(0)
    
    success = vacuum_database()
    sys.exit(0 if success else 1)
