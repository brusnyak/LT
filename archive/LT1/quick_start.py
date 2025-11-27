"""
Quick Start Script - Run Different Visualizations
"""
import sys
from pathlib import Path

# Add configuration
configs = {
    "1": {"pair": "EURUSD", "tf": "M5", "candles": 1000, "desc": "EURUSD 5M - Last 1000 candles"},
    "2": {"pair": "EURUSD", "tf": "M15", "candles": 500, "desc": "EURUSD 15M - Last 500 candles"},
    "3": {"pair": "EURUSD", "tf": "H1", "candles": 200, "desc": "EURUSD 1H - Last 200 candles"},
    "4": {"pair": "GBPUSD", "tf": "M5", "candles": 1000, "desc": "GBPUSD 5M - Last 1000 candles"},
    "5": {"pair": "GBPJPY", "tf": "M5", "candles": 1000, "desc": "GBPJPY 5M - Last 1000 candles"},
}

print("🎯 SMC Visualization - Quick Start")
print("=" * 50)
for key, cfg in configs.items():
    print(f"{key}. {cfg['desc']}")
print("=" * 50)

choice = input("Select configuration (1-5): ").strip()

if choice not in configs:
    print("❌ Invalid choice")
    sys.exit(1)

config = configs[choice]
print(f"\n✅ Loading {config['desc']}...")

# Update and run visualizer
import visualizer
visualizer.PAIR = config['pair']
visualizer.TIMEFRAME = config['tf']
visualizer.NUM_CANDLES = config['candles']

if __name__ == "__main__":
    visualizer.main()
