#!/usr/bin/env python3
"""
Market Structure Detection Test
Validates BOS/CHOCH detection accuracy by printing detailed results
"""
import pandas as pd
from pathlib import Path

from app.core.data_loader import load_candle_data # Corrected import
from app.core.constants import Pair, Timeframe
from app.smc.swings import SwingDetector, get_optimal_lookback
from app.smc.order_blocks import OrderBlockDetector
from app.smc.liquidity import LiquidityDetector
from app.smc.market_structure import MarketStructureDetector


def test_market_structure(pair: str = "EURUSD", timeframe: str = "M30", limit: int = 300):
    """Test market structure detection and print results"""
    
    print(f"\n{'='*80}")
    print(f"MARKET STRUCTURE DETECTION TEST")
    print(f"Pair: {pair} | Timeframe: {timeframe} | Candles: {limit}")
    print(f"{'='*80}\n")
    
    # Load data
    df = load_candle_data(pair, timeframe, limit=limit) # Corrected function call
    
    print(f"✓ Loaded {len(df)} candles")
    print(f"  Date range: {df.index[0]} to {df.index[-1]}\n")
    
    # Detect swings
    swing_lookback_left, swing_lookback_right = get_optimal_lookback(timeframe)
    print(f"✓ Using swing lookback: {swing_lookback_left}, {swing_lookback_right}")
    
    swing_detector = SwingDetector(lookback_left=swing_lookback_left, lookback_right=swing_lookback_right)
    swing_highs, swing_lows = swing_detector.detect_swings(df)
    
    print(f"✓ Detected {len(swing_highs)} swing highs, {len(swing_lows)} swing lows\n")
    
    # Detect Liquidity
    liq_detector = LiquidityDetector()
    liquidity_zones = liq_detector.detect_liquidity_zones(df, swing_highs, swing_lows)
    
    print(f"✓ Detected {len(liquidity_zones)} liquidity zones")

    # Detect market structure
    ms_detector = MarketStructureDetector()
    structure_events = ms_detector.detect_structure(df, swing_highs, swing_lows)
    
    print(f"✓ Detected {len(structure_events)} structure events")
    
    # Detect Order Blocks
    ob_detector = OrderBlockDetector()
    order_blocks = ob_detector.detect_order_blocks(df, structure_events)
    order_blocks = ob_detector.update_ob_states(df, order_blocks)
    
    print(f"✓ Detected {len(order_blocks)} order blocks")

    # Visualize results
    print("\n" + "="*80)
    print(f"MARKET STRUCTURE EVENTS: {len(structure_events)} total")
    print("="*80)
    
    if not structure_events:
        print("⚠️  No market structure events detected!")
    
    bos_count = sum(1 for e in structure_events if e['type'] == 'BOS')
    choch_count = sum(1 for e in structure_events if e['type'] == 'CHOCH')
    bullish_count = sum(1 for e in structure_events if e['direction'] == 'bullish')
    bearish_count = sum(1 for e in structure_events if e['direction'] == 'bearish')
    
    print(f"\nSummary:")
    print(f"  BOS (Break of Structure): {bos_count}")
    print(f"  CHOCH (Change of Character): {choch_count}")
    print(f"  Bullish: {bullish_count}")
    print(f"  Bearish: {bearish_count}")
    
    print("\n" + "="*80)
    print("ORDER BLOCKS:")
    print("="*80)
    
    active_obs = sum(1 for ob in order_blocks if ob['state'] == 'active')
    mitigated_obs = sum(1 for ob in order_blocks if ob['state'] == 'mitigated')
    touched_obs = sum(1 for ob in order_blocks if ob['state'] == 'touched')
    
    print(f"\nSummary:")
    print(f"  Total: {len(order_blocks)}")
    print(f"  Active: {active_obs}")
    print(f"  Touched: {touched_obs}")
    print(f"  Mitigated: {mitigated_obs}")
    
    print("\n" + "="*80)
    print("LIQUIDITY ZONES:")
    print("="*80)
    
    swing_liq = sum(1 for l in liquidity_zones if l.get('subtype') in ['swing_high', 'swing_low'])
    session_liq = sum(1 for l in liquidity_zones if l.get('subtype') in ['session_high', 'session_low'])
    eq_liq = sum(1 for l in liquidity_zones if l.get('subtype') in ['eqh', 'eql'])
    swept_liq = sum(1 for l in liquidity_zones if l['swept'])
    
    print(f"\nSummary:")
    print(f"  Total: {len(liquidity_zones)}")
    print(f"  Swing: {swing_liq}")
    print(f"  Session: {session_liq}")
    print(f"  Equal Highs/Lows: {eq_liq}")
    print(f"  Swept: {swept_liq}")

    print("\n" + "="*80)
    print("DETAILED EVENTS:")
    print("="*80)
    
    for i, event in enumerate(structure_events):
        icon = "🔵" if event['type'] == 'BOS' else "🟠"
        dir_icon = "📈" if event['direction'] == 'bullish' else "📉"
        
        print(f"\n{i+1}. {icon} {event['type']} {dir_icon} {event['direction'].upper()}")
        print(f"   Time: {event['timestamp']}")
        print(f"   Price: {event['price']:.5f}")
        print(f"   Pivot: {event['pivot_timestamp']} (idx: {event['pivot_index']})")
        print(f"   Break: Bar {event['index']}")
        if event.get('impulse_origin_index'):
            print(f"   Impulse Origin: Bar {event['impulse_origin_index']}")
        print(f"   {event['description']}")

    print("\n" + "="*80)
    print("DETAILED ORDER BLOCKS:")
    print("="*80)
    
    for i, ob in enumerate(order_blocks):
        icon = "🟩" if ob['type'] == 'bullish' else "🟥"
        state_icon = "✅" if ob['state'] == 'active' else "⚠️" if ob['state'] == 'touched' else "❌"
        breaker_tag = " [BREAKER]" if ob.get('is_breaker') else ""
        
        print(f"\n{i+1}. {icon} {ob['type'].upper()} OB {state_icon} {ob['state'].upper()}{breaker_tag}")
        print(f"   Created: {ob['timestamp']} (Bar {ob['candle_index']})")
        print(f"   Range: {ob['low']:.5f} - {ob['high']:.5f}")
        print(f"   Mitigation Level: {ob.get('mitigation_level', 0):.5f}")
        print(f"   From: {ob.get('structure_event', 'Unknown')}")
        
    print("\n" + "="*80)
    print("DETAILED LIQUIDITY:")
    print("="*80)
    
    for i, liq in enumerate(liquidity_zones[:10]): # Show first 10
        icon = "💧"
        swept_icon = "🧹" if liq['swept'] else "🔒"
        type_str = liq.get('subtype', liq['type']).upper()
        
        print(f"\n{i+1}. {icon} {type_str} {swept_icon}")
        print(f"   Price: {liq['price']:.5f}")
        print(f"   Time: {liq['timestamp']}")
        if 'session' in liq:
            print(f"   Session: {liq['session']}")

    print("\n" + "="*80)
    print("TREND ANALYSIS:")
    print(f"{'='*80}\n")
    
    # Analyze trend transitions
    if structure_events:
        first_direction = structure_events[0]['direction']
        last_direction = structure_events[-1]['direction']
        
        print(f"Starting trend: {first_direction.upper()}")
        print(f"Ending trend: {last_direction.upper()}")
        
        # Count trend changes
        trend_changes = sum(
            1 for i in range(1, len(structure_events))
            if structure_events[i]['direction'] != structure_events[i-1]['direction']
        )
        print(f"Trend changes: {trend_changes}")
    
    print(f"\n{'='*80}\n")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Market Structure Detection")
    parser.add_argument("--pair", default="EURUSD", help="Currency pair")
    parser.add_argument("--timeframe", default="M30", help="Timeframe")
    parser.add_argument("--limit", type=int, default=300, help="Number of candles")
    
    args = parser.parse_args()
    
    test_market_structure(args.pair, args.timeframe, args.limit)
