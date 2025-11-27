#!/usr/bin/env python
"""
Direct test of ICT strategy signal generation
"""

import os
import sys
import logging
import pandas as pd
from pathlib import Path

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from trading_bot.strategy.ict_strategy import ICTStrategy

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_test_data(file_path):
    """Load test data from a CSV file"""
    try:
        if not os.path.exists(file_path):
            logger.warning(f"Test data file not found: {file_path}")
            return None
        
        # Read the file content
        with open(file_path, 'r') as f:
            lines = f.readlines()
        
        # Skip comment lines starting with #
        data_lines = [line.strip() for line in lines if not line.strip().startswith('#')]
        
        # Parse the data lines
        data = []
        for line in data_lines:
            parts = line.split()
            if len(parts) >= 6:  # At least date, time, OHLC
                try:
                    timestamp = f"{parts[0]} {parts[1]}"
                    open_price = float(parts[2])
                    high_price = float(parts[3])
                    low_price = float(parts[4])
                    close_price = float(parts[5])
                    volume = int(parts[6]) if len(parts) > 6 else 0
                    
                    data.append({
                        'timestamp': timestamp,
                        'open': open_price,
                        'high': high_price,
                        'low': low_price,
                        'close': close_price,
                        'volume': volume
                    })
                except (ValueError, IndexError) as e:
                    logger.warning(f"Error parsing line: {line} - {e}")
                    continue
        
        # Create DataFrame
        if data:
            df = pd.DataFrame(data)
            
            # Convert timestamp to datetime
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # Set timestamp as index
            df = df.set_index('timestamp')
            
            # Sort by index
            df = df.sort_index()
            
            logger.info(f"Successfully loaded {len(df)} rows from {file_path}")
            return df
        else:
            logger.warning(f"No valid data found in {file_path}")
            return None
    except Exception as e:
        logger.error(f"Error loading test data from {file_path}: {e}")
        return None

def test_ict_strategy():
    """Test ICT strategy signal generation"""
    # Load data
    file_path = "charts/forex/EURUSD60.csv"
    df = load_test_data(file_path)
    
    if df is None or df.empty:
        logger.error("No data available for testing")
        return
    
    # Filter to a specific date range
    start_date = pd.to_datetime("2022-01-01")
    end_date = pd.to_datetime("2022-03-31")
    
    df = df[(df.index >= start_date) & (df.index <= end_date)]
    
    if df.empty:
        logger.error("No data available in the specified date range")
        return
    
    logger.info(f"Testing with {len(df)} candles from {df.index[0]} to {df.index[-1]}")
    
    # Initialize strategy
    strategy = ICTStrategy()
    
    # Test at different points in the data
    window_size = 100
    test_points = [
        window_size,  # Beginning
        len(df) // 4,  # 25%
        len(df) // 2,  # 50%
        3 * len(df) // 4,  # 75%
        len(df) - 1  # End
    ]
    
    for point in test_points:
        if point < window_size:
            continue
        
        # Get window
        window = df.iloc[point-window_size:point+1]
        
        # Generate signal
        logger.info(f"Testing at {window.index[-1]}")
        
        try:
            # Analyze data
            analysis = strategy.analyze_sync(window, "EURUSD", "H1")
            
            # Log analysis results safely
            logger.info(f"Analysis results:")
            
            # Daily bias
            daily_bias = analysis.get('daily_bias', {})
            if isinstance(daily_bias, dict):
                logger.info(f"  Daily bias: {daily_bias.get('direction', 'neutral')}")
            else:
                logger.info(f"  Daily bias: neutral")
            
            # Order blocks
            order_blocks = analysis.get('order_blocks', {})
            if isinstance(order_blocks, dict):
                bullish_count = len(order_blocks.get('bullish', []))
                bearish_count = len(order_blocks.get('bearish', []))
                logger.info(f"  Order blocks: {bullish_count + bearish_count}")
            elif isinstance(order_blocks, list):
                logger.info(f"  Order blocks: {len(order_blocks)}")
            else:
                logger.info(f"  Order blocks: 0")
            
            # Fair value gaps
            fair_value_gaps = analysis.get('fair_value_gaps', {})
            if isinstance(fair_value_gaps, dict):
                bullish_count = len(fair_value_gaps.get('bullish', []))
                bearish_count = len(fair_value_gaps.get('bearish', []))
                logger.info(f"  Fair value gaps: {bullish_count + bearish_count}")
            elif isinstance(fair_value_gaps, list):
                logger.info(f"  Fair value gaps: {len(fair_value_gaps)}")
            else:
                logger.info(f"  Fair value gaps: 0")
            
            # Liquidity levels
            liquidity_levels = analysis.get('liquidity_levels', {})
            if isinstance(liquidity_levels, dict):
                above_count = len(liquidity_levels.get('above', []))
                below_count = len(liquidity_levels.get('below', []))
                logger.info(f"  Liquidity levels: {above_count + below_count}")
            elif isinstance(liquidity_levels, list):
                logger.info(f"  Liquidity levels: {len(liquidity_levels)}")
            else:
                logger.info(f"  Liquidity levels: 0")
            
            # Setups
            setups = analysis.get('setups', [])
            logger.info(f"  Setups: {len(setups)}")
            
            # Signals
            signals = analysis.get('signals', [])
            logger.info(f"  Signals: {len(signals)}")
            
            # Generate signal
            signal = strategy.generate_signal(window, "EURUSD", "H1")
            
            if signal:
                logger.info(f"Signal generated: {signal}")
            else:
                logger.info("No signal generated")
        except Exception as e:
            logger.error(f"Error testing at {window.index[-1]}: {e}", exc_info=True)


if __name__ == "__main__":
    test_ict_strategy()