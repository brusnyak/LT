"""
Database migration to add last_trade_date field to challenges table

Run this once to update existing database:
    cd backend && . venv/bin/activate && python3 migrate_add_last_trade_date.py
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.database import engine


def migrate():
    """Add last_trade_date column to challenges table"""
    print("🔄 Running migration: Add last_trade_date to challenges")
    
    try:
        with engine.connect() as conn:
            # Check if column already exists
            result = conn.execute(text(
                "SELECT COUNT(*) FROM pragma_table_info('challenges') WHERE name='last_trade_date'"
            ))
            exists = result.scalar() > 0
            
            if exists:
                print("✅ Column 'last_trade_date' already exists, skipping migration")
                return
            
            # Add the column
            conn.execute(text(
                "ALTER TABLE challenges ADD COLUMN last_trade_date DATETIME"
            ))
            conn.commit()
            
            print("✅ Migration complete: Added last_trade_date column")
            print("   Note: Existing challenges will have NULL last_trade_date")
            print("   They will use created_at for inactivity calculations")
            
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        raise


if __name__ == "__main__":
    migrate()
