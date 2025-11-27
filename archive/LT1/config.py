# SMC Visualizer Configuration

# Data Configuration
PAIR = "EURUSD"  # Options: EURUSD, GBPUSD, GBPJPY
TIMEFRAME = "M5"  # Options: M1, M5, M15, M30, H1, H4, D1
NUM_CANDLES = 1000  # Number of candles to display (max: all available)

# SMC Analysis Toggle
SHOW_ORDER_BLOCKS = True
SHOW_FAIR_VALUE_GAPS = True
SHOW_LIQUIDITY = True
SHOW_MARKET_STRUCTURE = True

# Swing Detection Parameters
SWING_WINDOW = 5  # Window size for swing point detection (3-10 recommended)

# Display Settings
CHART_HEIGHT = 900  # Chart height in pixels
DARK_THEME = True  # Use TradingView dark theme

# Session Times (UTC)
LONDON_OPEN = 8  # 8:00 UTC
LONDON_CLOSE = 12  # 12:00 UTC
NY_OPEN = 13  # 13:00 UTC
NY_CLOSE = 17  # 17:00 UTC
