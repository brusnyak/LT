"""
Inactivity Monitor
Checks for trading inactivity and sends Telegram warnings/breaches accounts

Rules:
- 7 days of inactivity: Send Telegram warning
- 10 days of inactivity: Breach account (set is_active=False)
"""
import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv
import requests

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models.db.challenge import Challenge

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

INACTIVITY_WARNING_DAYS = 7
INACTIVITY_BREACH_DAYS = 10


def send_telegram_message(message: str):
    """Send a message via Telegram bot"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Telegram credentials not configured")
        return False
    
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "Markdown"
        }
        response = requests.post(url, json=payload, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Failed to send Telegram message: {e}")
        return False


def check_inactivity():
    """Check all active challenges for inactivity"""
    db = SessionLocal()
    
    try:
        # Get all active challenges
        challenges = db.query(Challenge).filter(Challenge.is_active == True).all()
        
        if not challenges:
            print("No active challenges found")
            return
        
        now = datetime.utcnow()
        warnings_sent = 0
        breaches = 0
        
        for challenge in challenges:
            # Determine last activity date
            last_activity = challenge.last_trade_date or challenge.created_at
            days_inactive = (now - last_activity).days
            
            print(f"\n📊 Challenge: {challenge.name} (ID: {challenge.id})")
            print(f"   Last trade: {last_activity.strftime('%Y-%m-%d %H:%M')}")
            print(f"   Days inactive: {days_inactive}")
            
            # Check for breach (10 days)
            if days_inactive >= INACTIVITY_BREACH_DAYS:
                print(f"   ⚠️ BREACH: {days_inactive} days of inactivity")
                
                # Breach the account
                challenge.is_active = False
                db.commit()
                
                # Send Telegram notification
                message = (
                    f"🚨 *ACCOUNT BREACHED*\n\n"
                    f"Challenge: {challenge.name}\n"
                    f"Reason: {days_inactive} days of inactivity\n"
                    f"Limit: {INACTIVITY_BREACH_DAYS} days\n\n"
                    f"Account has been deactivated."
                )
                send_telegram_message(message)
                breaches += 1
                
            # Check for warning (7 days)
            elif days_inactive >= INACTIVITY_WARNING_DAYS:
                print(f"   ⚠️ WARNING: {days_inactive} days of inactivity")
                
                days_remaining = INACTIVITY_BREACH_DAYS - days_inactive
                
                # Send Telegram warning
                message = (
                    f"⚠️ *INACTIVITY WARNING*\n\n"
                    f"Challenge: {challenge.name}\n"
                    f"Days inactive: {days_inactive}\n"
                    f"Days until breach: {days_remaining}\n\n"
                    f"⏰ You must make a trade within {days_remaining} days to avoid account breach.\n\n"
                    f"Last trade: {last_activity.strftime('%Y-%m-%d %H:%M UTC')}"
                )
                send_telegram_message(message)
                warnings_sent += 1
            
            else:
                print(f"   ✅ Active (last trade {days_inactive} days ago)")
        
        print(f"\n📈 Summary:")
        print(f"   Warnings sent: {warnings_sent}")
        print(f"   Accounts breached: {breaches}")
        
    except Exception as e:
        print(f"❌ Error checking inactivity: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    print("🔍 Checking for trading inactivity...")
    print(f"   Warning threshold: {INACTIVITY_WARNING_DAYS} days")
    print(f"   Breach threshold: {INACTIVITY_BREACH_DAYS} days")
    check_inactivity()
    print("\n✅ Inactivity check complete")
