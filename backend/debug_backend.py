import sys
import os
import pandas as pd
import traceback

# Add backend directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.core.data_loader import load_candle_data
from app.smc.swings import SwingDetector, get_optimal_lookback
from app.smc.market_structure import MarketStructureDetector
from app.smc.order_blocks import OrderBlockDetector, get_ob_lookback_window
from app.smc.liquidity import LiquidityDetector

def debug_backend():
    pair = "EURUSD"
    timeframe = "M5"
    limit = 1000
    
    print(f"Loading data for {pair} {timeframe}...")
    try:
        df = load_candle_data(pair, timeframe, limit=limit)
        print(f"Loaded {len(df)} candles")
    except Exception as e:
        print(f"Error loading data: {e}")
        return

    try:
        print("\n--- Testing Swings ---")
        swing_lookback_left, swing_lookback_right = get_optimal_lookback(timeframe)
        print(f"Optimal lookback: {swing_lookback_left}, {swing_lookback_right}")
        swing_detector = SwingDetector(lookback_left=swing_lookback_left, lookback_right=swing_lookback_right)
        swing_highs, swing_lows = swing_detector.detect_swings(df)
        print(f"Swings: {len(swing_highs)} highs, {len(swing_lows)} lows")
        
        print("\n--- Testing Market Structure ---")
        structure_detector = MarketStructureDetector()
        structure_events = structure_detector.detect_structure(df, swing_highs, swing_lows)
        print(f"Structure events: {len(structure_events)}")
        
        print("\n--- Testing Order Blocks ---")
        lookback_window = get_ob_lookback_window(timeframe)
        ob_detector = OrderBlockDetector(lookback_window=lookback_window)
        order_blocks = ob_detector.detect_order_blocks(df, structure_events)
        print(f"Order blocks detected: {len(order_blocks)}")
        
        print("\n--- Testing Liquidity ---")
        liq_detector = LiquidityDetector()
        liquidity_zones = liq_detector.detect_liquidity_zones(df, swing_highs, swing_lows)
        print(f"Liquidity zones detected: {len(liquidity_zones)}")
        
        print("\nAll tests passed!")
        
    except Exception as e:
        print("\nCRITICAL ERROR:")
        traceback.print_exc()

if __name__ == "__main__":
    debug_backend()
