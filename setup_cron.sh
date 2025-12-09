#!/bin/bash
# Setup cron job for inactivity monitoring
# Run this script to automatically configure daily inactivity checks

PROJECT_DIR="/Users/yegor/Documents/Agency & Security Stuff/Development/SMC"
CRON_CMD="0 9 * * * cd \"$PROJECT_DIR\" && make check-inactivity >> /tmp/smc_inactivity.log 2>&1"

echo "🔧 Setting up cron job for inactivity monitoring..."
echo ""
echo "Project directory: $PROJECT_DIR"
echo "Cron schedule: Daily at 9:00 AM"
echo "Log file: /tmp/smc_inactivity.log"
echo ""

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "check-inactivity"; then
    echo "⚠️  Cron job already exists!"
    echo ""
    echo "Current crontab:"
    crontab -l | grep "check-inactivity"
    echo ""
    read -p "Do you want to replace it? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Setup cancelled"
        exit 0
    fi
    # Remove old entry
    crontab -l | grep -v "check-inactivity" | crontab -
fi

# Add new cron job
(crontab -l 2>/dev/null; echo "$CRON_CMD") | crontab -

echo "✅ Cron job installed successfully!"
echo ""
echo "Verify with: crontab -l"
echo ""
echo "The inactivity checker will run daily at 9:00 AM"
echo "You can also run it manually anytime with: make check-inactivity"
echo ""
echo "To view logs: tail -f /tmp/smc_inactivity.log"
echo ""
echo "To remove the cron job later:"
echo "  crontab -l | grep -v 'check-inactivity' | crontab -"
