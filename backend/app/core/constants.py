"""Constants for the application"""
from enum import Enum


class Timeframe(str, Enum):
    """Supported timeframes"""
    M1 = "M1"
    M5 = "M5"
    M15 = "M15"
    M30 = "M30"
    H1 = "H1"
    H4 = "H4"
    D1 = "D1"


class Pair(str, Enum):
    """Supported currency pairs"""
    EURUSD = "EURUSD"
    GBPUSD = "GBPUSD"
    GBPJPY = "GBPJPY"


# Timeframe to minutes mapping
TIMEFRAME_MINUTES = {
    Timeframe.M1: 1,
    Timeframe.M5: 5,
    Timeframe.M15: 15,
    Timeframe.M30: 30,
    Timeframe.H1: 60,
    Timeframe.H4: 240,
    Timeframe.D1: 1440,
}

# Session times (UTC)
LONDON_KILL_ZONE = (7, 10)  # 07:00-10:00 UTC
NY_KILL_ZONE = (13, 16)     # 13:00-16:00 UTC

# Risk management
RISK_PER_TRADE = 0.005      # 0.5%
DAILY_LOSS_LIMIT = 0.02     # 2%
MAX_POSITIONS = 2
MIN_RR = 2.0

# Prop firm limits (fallback safety)
PROP_DAILY_LOSS = 0.07      # 7%
PROP_TOTAL_DD = 0.12        # 12%
