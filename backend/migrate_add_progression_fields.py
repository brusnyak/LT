"""
Database migration to add progression tracking fields to challenges table

Run this to update existing database:
    cd backend && . venv/bin/activate && python3 migrate_add_progression_fields.py
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.database import engine


def migrate():
    """Add progression tracking fields to challenges table"""
    print("🔄 Running migration: Add progression tracking fields to challenges")
    
    try:
        with engine.connect() as conn:
            # Check which columns already exist
            result = conn.execute(text(
                "SELECT name FROM pragma_table_info('challenges')"
            ))
            existing_columns = {row[0] for row in result}
            
            migrations = []
            
            # trading_days_count
            if 'trading_days_count' not in existing_columns:
                migrations.append(("trading_days_count", "ALTER TABLE challenges ADD COLUMN trading_days_count INTEGER DEFAULT 0"))
            
            # min_trading_days
            if 'min_trading_days' not in existing_columns:
                migrations.append(("min_trading_days", "ALTER TABLE challenges ADD COLUMN min_trading_days INTEGER DEFAULT 4"))
            
            # phase_start_date
            if 'phase_start_date' not in existing_columns:
                migrations.append(("phase_start_date", "ALTER TABLE challenges ADD COLUMN phase_start_date DATETIME"))
            
            # phase_completed_date
            if 'phase_completed_date' not in existing_columns:
                migrations.append(("phase_completed_date", "ALTER TABLE challenges ADD COLUMN phase_completed_date DATETIME"))
            
            # breach_reason
            if 'breach_reason' not in existing_columns:
                migrations.append(("breach_reason", "ALTER TABLE challenges ADD COLUMN breach_reason VARCHAR"))
            
            if not migrations:
                print("✅ All progression fields already exist, skipping migration")
                return
            
            # Execute migrations
            for field_name, sql in migrations:
                print(f"   Adding {field_name}...")
                conn.execute(text(sql))
            
            # Set phase_start_date to created_at for existing challenges
            conn.execute(text(
                "UPDATE challenges SET phase_start_date = created_at WHERE phase_start_date IS NULL"
            ))
            
            conn.commit()
            
            print(f"✅ Migration complete: Added {len(migrations)} fields")
            print("   Fields added:", ", ".join(m[0] for m in migrations))
            print("   Note: Existing challenges will have:")
            print("   - trading_days_count = 0")
            print("   - min_trading_days = 4")
            print("   - phase_start_date = created_at")
            
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        raise


if __name__ == "__main__":
    migrate()
