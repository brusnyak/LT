#!/usr/bin/env python
"""
Test script for direct signal generation
"""

import os
import sys
import logging
import argparse
from pathlib import Path
import pandas as pd
import numpy as np

# Add parent directory to path to import trading_bot modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from trading_bot.strategy.ict_strategy import ICTStrategy
from trading_bot.strategy.combined_strategy import CombinedStrategy
from trading_bot.strategy.smc_strategy import SMCStrategy

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Test signal generation')
    
    # Required arguments
    parser.add_argument('--symbol', type=str, required=True, help='Trading symbol (e.g., EURUSD)')
    parser.add_argument('--market', type=str, required=True, choices=['forex', 'crypto', 'indices', 'metals'], 
                        help='Market type')
    
    # Optional arguments
    parser.add_argument('--timeframe', type=str, default='H1', help='Timeframe (default: H1)')
    parser.add_argument('--start-date', type=str, default='2022-02-22', 
                        help='Start date (YYYY-MM-DD, default: 2022-02-22)')
    parser.add_argument('--end-date', type=str, default=None, 
                        help='End date (YYYY-MM-DD, default: latest available)')
    parser.add_argument('--strategy', type=str, default='ict', choices=['ict', 'smc', 'combined'],
                        help='Strategy to test (default: ict)')
    parser.add_argument('--window-size', type=int, default=100,
                        help='Analysis window size (default: 100)')
    
    return parser.parse_args()

def load_data(args):
    """Load historical data for testing"""
    logger.info(f"Loading historical data for {args.symbol} {args.timeframe} from {args.start_date}")
    
    # Map timeframe to CSV suffix
    timeframe_to_suffix = {
        'M1': '1',
        'M5': '5',
        'M15': '15',
        'M30': '30',
        'H1': '60',
        'H4': '240',
        'D1': '1440',
        'W1': '10080'
    }
    
    # Get the CSV suffix for the timeframe
    csv_suffix = timeframe_to_suffix.get(args.timeframe, '60')  # Default to 60 (H1)
    logger.info(f"Using CSV suffix: {csv_suffix} for timeframe: {args.timeframe}")
    
    # Construct the file path
    file_path = Path(f"charts/{args.market}/{args.symbol}{csv_suffix}.csv")
    logger.info(f"Looking for data file at: {file_path}")
    
    if not file_path.exists():
        logger.error(f"Data file not found: {file_path}")
        return None
    
    # Load the data
    try:
        logger.info(f"Loading data from {file_path}")
        
        # Read the file with custom parsing
        with open(file_path, 'r') as f:
            lines = f.readlines()
        
        # Parse the data
        data = []
        for line in lines:
            # Skip empty lines
            if not line.strip():
                continue
                
            # Split by whitespace and filter out empty strings
            parts = [p for p in line.strip().split() if p]
            
            # Check if we have enough parts
            if len(parts) >= 6:  # date, time, open, high, low, close, volume
                try:
                    date_str = parts[0]
                    time_str = parts[1]
                    timestamp = pd.to_datetime(f"{date_str} {time_str}")
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
                except Exception as e:
                    logger.warning(f"Error parsing line: {line.strip()}, error: {e}")
                    continue
        
        # Create DataFrame
        df = pd.DataFrame(data)
        
        # Set timestamp as index
        if 'timestamp' in df.columns:
            df.set_index('timestamp', inplace=True)
        
        # Sort by index
        df.sort_index(inplace=True)
        
        logger.info(f"Loaded {len(df)} rows from {file_path}")
        
        # Filter by date range
        start_date = pd.to_datetime(args.start_date)
        if args.end_date:
            end_date = pd.to_datetime(args.end_date)
        else:
            end_date = df.index[-1]
        
        df = df[(df.index >= start_date) & (df.index <= end_date)]
        
        if df.empty:
            logger.error(f"No data available for {args.symbol} {args.timeframe} in the specified date range")
            return None
        
        logger.info(f"Filtered to {len(df)} candles from {df.index[0]} to {df.index[-1]}")
        
        return df
        
    except Exception as e:
        logger.error(f"Error parsing CSV file {file_path}: {e}")
        return None

def test_signal_generation(args, df):
    """Test signal generation with the specified strategy"""
    logger.info(f"Testing signal generation with {args.strategy} strategy")
    
    # Initialize the strategy
    if args.strategy == 'ict':
        strategy = ICTStrategy()
    elif args.strategy == 'smc':
        strategy = SMCStrategy()
    elif args.strategy == 'combined':
        strategy = CombinedStrategy()
    else:
        logger.error(f"Unknown strategy: {args.strategy}")
        return
    
    # Get the window size
    window_size = args.window_size
    
    # Test signal generation at different points in the data
    signal_count = 0
    signals = []
    
    # Test at the beginning, middle, and end of the data
    test_indices = [
        window_size,  # Beginning (after enough history)
        len(df) // 2,  # Middle
        len(df) - 1   # End
    ]
    
    for idx in test_indices:
        if idx < window_size:
            continue
            
        # Get a window of data for analysis
        analysis_window = df.iloc[idx-window_size:idx+1]
        
        # Generate signal
        try:
            signal = strategy.generate_signal(analysis_window, args.symbol, args.timeframe)
            
            if signal and len(signal) > 0:
                signal_count += 1
                signals.append({
                    'timestamp': analysis_window.index[-1],
                    'signal': signal
                })
                logger.info(f"Signal generated at {analysis_window.index[-1]}: {signal.get('direction')} - {signal.get('setup_type', 'Unknown')}")
            else:
                logger.info(f"No signal generated at {analysis_window.index[-1]}")
        except Exception as e:
            logger.error(f"Error generating signal at {analysis_window.index[-1]}: {e}", exc_info=True)
    
    # Test signal generation for each day in the data
    dates = pd.Series(df.index.date).unique()
    
    for date in dates[:min(10, len(dates))]:  # Test first 10 days
        # Get data for this day
        day_mask = df.index.date == date
        day_data = df[day_mask]
        
        if len(day_data) == 0:
            continue
            
        # Get the last candle of the day
        last_idx = df.index.get_loc(day_data.index[-1])
        
        if last_idx < window_size:
            continue
            
        # Get a window of data for analysis
        analysis_window = df.iloc[last_idx-window_size:last_idx+1]
        
        # Generate signal
        try:
            signal = strategy.generate_signal(analysis_window, args.symbol, args.timeframe)
            
            if signal and len(signal) > 0:
                signal_count += 1
                signals.append({
                    'timestamp': analysis_window.index[-1],
                    'signal': signal
                })
                logger.info(f"Signal generated for day {date}: {signal.get('direction')} - {signal.get('setup_type', 'Unknown')}")
            else:
                logger.info(f"No signal generated for day {date}")
        except Exception as e:
            logger.error(f"Error generating signal for day {date}: {e}", exc_info=True)
    
    # Scan the entire dataset for signals
    logger.info("Scanning entire dataset for signals...")
    
    for i in range(window_size, len(df), 10):  # Check every 10th candle to save time
        # Get a window of data for analysis
        analysis_window = df.iloc[i-window_size:i+1]
        
        # Generate signal
        try:
                signal = strategy.generate_signal(analysis_window, args.symbol, args.timeframe)
                
                if signal and len(signal) > 0:
                    signal_count += 1
                    signals.append({
                        'timestamp': analysis_window.index[-1],
                        'signal': signal
                    })
                    logger.info(f"Signal generated at {analysis_window.index[-1]}: {signal.get('direction')} - {signal.get('setup_type', 'Unknown')}")
        except Exception as e:
            logger.error(f"Error generating signal at index {i}: {e}", exc_info=True)
    
    # Summary
    logger.info(f"Signal generation test completed")
    logger.info(f"Total signals generated: {signal_count}")
    
    if signal_count > 0:
        logger.info("Signal distribution:")
        buy_signals = sum(1 for s in signals if s['signal'].get('direction') == 'BUY')
        sell_signals = sum(1 for s in signals if s['signal'].get('direction') == 'SELL')
        logger.info(f"BUY signals: {buy_signals} ({buy_signals/signal_count*100:.2f}%)")
        logger.info(f"SELL signals: {sell_signals} ({sell_signals/signal_count*100:.2f}%)")
        
        # Log signal types
        setup_types = {}
        for s in signals:
            setup_type = s['signal'].get('setup_type', 'Unknown')
            setup_types[setup_type] = setup_types.get(setup_type, 0) + 1
        
        logger.info("Signal types:")
        for setup_type, count in setup_types.items():
            logger.info(f"- {setup_type}: {count} ({count/signal_count*100:.2f}%)")
    
    return signals

def analyze_signals(signals, df):
    """Analyze the generated signals"""
    if not signals:
        logger.info("No signals to analyze")
        return
    
    logger.info("Analyzing signals...")
    
    # Calculate win rate (assuming perfect execution)
    wins = 0
    losses = 0
    
    for signal_data in signals:
        signal = signal_data['signal']
        timestamp = signal_data['timestamp']
        
        # Find the index of this timestamp in the dataframe
        try:
            idx = df.index.get_loc(timestamp)
        except KeyError:
            logger.warning(f"Timestamp {timestamp} not found in dataframe")
            continue
        
        # Check if we have enough future data to evaluate
        if idx + 20 >= len(df):
            logger.warning(f"Not enough future data to evaluate signal at {timestamp}")
            continue
        
        # Get future data
        future_data = df.iloc[idx+1:idx+21]
        
        # Evaluate the signal
        direction = signal.get('direction')
        entry_price = signal.get('entry_price')
        stop_loss = signal.get('stop_loss')
        take_profit = signal.get('take_profit')
        
        if not all([direction, entry_price, stop_loss, take_profit]):
            logger.warning(f"Signal at {timestamp} missing required fields")
            continue
        
        # Check if stop loss or take profit was hit
        if direction == 'BUY':
            # Check if stop loss was hit
            if future_data['low'].min() <= stop_loss:
                losses += 1
                logger.info(f"Signal at {timestamp} (BUY): Stop loss hit")
            # Check if take profit was hit
            elif future_data['high'].max() >= take_profit:
                wins += 1
                logger.info(f"Signal at {timestamp} (BUY): Take profit hit")
            else:
                logger.info(f"Signal at {timestamp} (BUY): Neither stop loss nor take profit hit")
        else:  # SELL
            # Check if stop loss was hit
            if future_data['high'].max() >= stop_loss:
                losses += 1
                logger.info(f"Signal at {timestamp} (SELL): Stop loss hit")
            # Check if take profit was hit
            elif future_data['low'].min() <= take_profit:
                wins += 1
                logger.info(f"Signal at {timestamp} (SELL): Take profit hit")
            else:
                logger.info(f"Signal at {timestamp} (SELL): Neither stop loss nor take profit hit")
    
    # Calculate win rate
    total = wins + losses
    win_rate = wins / total * 100 if total > 0 else 0
    
    logger.info(f"Signal analysis completed")
    logger.info(f"Wins: {wins}, Losses: {losses}, Total: {total}")
    logger.info(f"Win rate: {win_rate:.2f}%")
    
    return {
        'wins': wins,
        'losses': losses,
        'total': total,
        'win_rate': win_rate
    }

def save_results(args, signals, analysis_results):
    """Save test results to file"""
    if not signals:
        logger.info("No signals to save")
        return
    
    logger.info("Saving test results...")
    
    # Create output directory
    output_dir = Path("signal_test_results")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create a filename
    filename = f"{args.symbol}_{args.timeframe}_{args.strategy}_signals.json"
    file_path = output_dir / filename
    
    # Convert signals to serializable format
    serializable_signals = []
    for signal_data in signals:
        timestamp = signal_data['timestamp']
        signal = signal_data['signal']
        
        serializable_signal = {
            'timestamp': timestamp.isoformat(),
            'direction': signal.get('direction'),
            'entry_price': signal.get('entry_price'),
            'stop_loss': signal.get('stop_loss'),
            'take_profit': signal.get('take_profit'),
            'setup_type': signal.get('setup_type', 'Unknown'),
            'strength': signal.get('strength', 0),
            'timeframe': signal.get('timeframe'),
            'strategy': signal.get('strategy')
        }
        
        serializable_signals.append(serializable_signal)
    
    # Create results dictionary
    results = {
        'symbol': args.symbol,
        'timeframe': args.timeframe,
        'strategy': args.strategy,
        'window_size': args.window_size,
        'start_date': args.start_date,
        'end_date': args.end_date,
        'signals': serializable_signals,
        'analysis': analysis_results
    }
    
    # Save to JSON
    import json
    with open(file_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Results saved to {file_path}")

def main():
    """Main function"""
    # Parse command line arguments
    args = parse_args()
    
    # Load historical data
    df = load_data(args)
    
    if df is None or df.empty:
        logger.error("No data available for testing")
        return
    
    # Test signal generation
    signals = test_signal_generation(args, df)
    
    # Analyze signals
    if signals:
        analysis_results = analyze_signals(signals, df)
    else:
        analysis_results = None
    
    # Save results
    save_results(args, signals, analysis_results)
    
    logger.info("Signal generation test completed successfully")

if __name__ == "__main__":
    main()
