#!/usr/bin/env python
"""
Comprehensive test for backtesting the ICT strategy
"""

import os
import sys
import logging
import argparse
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import json
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from trading_bot.strategy.ict_strategy import ICTStrategy
from trading_bot.utils.visualization import Visualization

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Test ICT strategy backtesting')
    
    # Required arguments
    parser.add_argument('--symbol', type=str, default='EURUSD', help='Trading symbol (default: EURUSD)')
    parser.add_argument('--market', type=str, default='forex', choices=['forex', 'crypto', 'indices', 'metals'], 
                        help='Market type (default: forex)')
    
    # Optional arguments
    parser.add_argument('--timeframe', type=str, default='H1', help='Timeframe (default: H1)')
    parser.add_argument('--start-date', type=str, default='2022-02-22', 
                        help='Start date (YYYY-MM-DD, default: 2022-02-22)')
    parser.add_argument('--end-date', type=str, default='2022-03-22', 
                        help='End date (YYYY-MM-DD, default: 2022-03-22)')
    parser.add_argument('--initial-capital', type=float, default=10000.0,
                        help='Initial capital (default: 10000.0)')
    parser.add_argument('--position-size', type=float, default=0.01,
                        help='Position size in lots (default: 0.01)')
    parser.add_argument('--window-size', type=int, default=100,
                        help='Analysis window size (default: 100)')
    
    return parser.parse_args()

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

def run_backtest(args, df):
    """Run backtest with the ICT strategy"""
    logger.info(f"Running backtest for {args.symbol} {args.timeframe} from {args.start_date} to {args.end_date}")
    
    # Initialize strategy
    strategy = ICTStrategy()
    
    # Initialize backtest variables
    initial_capital = args.initial_capital
    position_size = args.position_size
    window_size = args.window_size
    
    equity = [initial_capital]
    trades = []
    current_position = None
    
    # Filter by date range
    start_date = pd.to_datetime(args.start_date)
    end_date = pd.to_datetime(args.end_date)
    
    df = df[(df.index >= start_date) & (df.index <= end_date)]
    
    if df.empty:
        logger.error(f"No data available for {args.symbol} {args.timeframe} in the specified date range")
        return None, None
    
    logger.info(f"Filtered to {len(df)} candles from {df.index[0]} to {df.index[-1]}")
    
    # Run backtest
    for i in range(window_size, len(df)):
        # Get current candle
        current_candle = df.iloc[i]
        current_time = df.index[i]
        
        # Get analysis window
        analysis_window = df.iloc[i-window_size:i+1]
        
        # Check if we have an open position
        if current_position:
            # Check if stop loss or take profit was hit
            if current_position['direction'] == 'BUY':
                # Check if stop loss was hit
                if current_candle['low'] <= current_position['stop_loss']:
                    # Close position at stop loss
                    profit_loss = (current_position['stop_loss'] - current_position['entry_price']) * current_position['position_size'] * 100000
                    equity.append(equity[-1] + profit_loss)
                    
                    # Record trade
                    current_position['exit_price'] = current_position['stop_loss']
                    current_position['exit_time'] = current_time
                    current_position['profit_loss'] = profit_loss
                    current_position['exit_reason'] = 'stop_loss'
                    trades.append(current_position)
                    
                    logger.info(f"Stop loss hit at {current_time}: {current_position['stop_loss']}, P/L: {profit_loss}")
                    
                    # Reset position
                    current_position = None
                    continue
                
                # Check if take profit was hit
                if current_candle['high'] >= current_position['take_profit']:
                    # Close position at take profit
                    profit_loss = (current_position['take_profit'] - current_position['entry_price']) * current_position['position_size'] * 100000
                    equity.append(equity[-1] + profit_loss)
                    
                    # Record trade
                    current_position['exit_price'] = current_position['take_profit']
                    current_position['exit_time'] = current_time
                    current_position['profit_loss'] = profit_loss
                    current_position['exit_reason'] = 'take_profit'
                    trades.append(current_position)
                    
                    logger.info(f"Take profit hit at {current_time}: {current_position['take_profit']}, P/L: {profit_loss}")
                    
                    # Reset position
                    current_position = None
                    continue
            else:  # SELL
                # Check if stop loss was hit
                if current_candle['high'] >= current_position['stop_loss']:
                    # Close position at stop loss
                    profit_loss = (current_position['entry_price'] - current_position['stop_loss']) * current_position['position_size'] * 100000
                    equity.append(equity[-1] + profit_loss)
                    
                    # Record trade
                    current_position['exit_price'] = current_position['stop_loss']
                    current_position['exit_time'] = current_time
                    current_position['profit_loss'] = profit_loss
                    current_position['exit_reason'] = 'stop_loss'
                    trades.append(current_position)
                    
                    logger.info(f"Stop loss hit at {current_time}: {current_position['stop_loss']}, P/L: {profit_loss}")
                    
                    # Reset position
                    current_position = None
                    continue
                
                # Check if take profit was hit
                if current_candle['low'] <= current_position['take_profit']:
                    # Close position at take profit
                    profit_loss = (current_position['entry_price'] - current_position['take_profit']) * current_position['position_size'] * 100000
                    equity.append(equity[-1] + profit_loss)
                    
                    # Record trade
                    current_position['exit_price'] = current_position['take_profit']
                    current_position['exit_time'] = current_time
                    current_position['profit_loss'] = profit_loss
                    current_position['exit_reason'] = 'take_profit'
                    trades.append(current_position)
                    
                    logger.info(f"Take profit hit at {current_time}: {current_position['take_profit']}, P/L: {profit_loss}")
                    
                    # Reset position
                    current_position = None
                    continue
            
            # If no exit, update equity with the same value
            equity.append(equity[-1])
            continue
        
            # No position, check for signal
            try:
                signal = strategy.generate_signal(analysis_window, args.symbol, args.timeframe)
                
                if signal and len(signal) > 0:
                    # Check if signal has required fields
                    if all(k in signal for k in ['direction', 'entry_price', 'stop_loss', 'take_profit']):
                        # Create position
                        current_position = {
                            'symbol': args.symbol,
                            'direction': signal['direction'],
                            'entry_price': signal['entry_price'],
                            'stop_loss': signal['stop_loss'],
                            'take_profit': signal['take_profit'],
                            'entry_time': current_time,
                            'position_size': position_size,
                            'setup_type': signal.get('setup_type', 'Unknown'),
                            'strength': signal.get('strength', 0),
                            'risk_reward': signal.get('risk_reward', 0)
                        }
                        
                        logger.info(f"Signal generated at {current_time}: {signal['direction']} at {signal['entry_price']}")
                        logger.info(f"Stop Loss: {signal['stop_loss']}, Take Profit: {signal['take_profit']}")
                        
                        # Update equity (no change on entry)
                        equity.append(equity[-1])
                    else:
                        # Signal doesn't have required fields
                        logger.warning(f"Signal at {current_time} missing required fields: {signal}")
                        equity.append(equity[-1])
                else:
                    # No signal
                    equity.append(equity[-1])
            except Exception as e:
                logger.error(f"Error generating signal at {current_time}: {e}", exc_info=True)
                equity.append(equity[-1])
    
    # Calculate backtest results
    results = {
        'symbol': args.symbol,
        'timeframe': args.timeframe,
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d'),
        'initial_capital': initial_capital,
        'final_equity': equity[-1],
        'total_return': (equity[-1] - initial_capital) / initial_capital * 100,
        'total_trades': len(trades),
        'winning_trades': sum(1 for t in trades if t['profit_loss'] > 0),
        'losing_trades': sum(1 for t in trades if t['profit_loss'] <= 0),
        'win_rate': sum(1 for t in trades if t['profit_loss'] > 0) / len(trades) * 100 if trades else 0,
        'average_win': sum(t['profit_loss'] for t in trades if t['profit_loss'] > 0) / sum(1 for t in trades if t['profit_loss'] > 0) if sum(1 for t in trades if t['profit_loss'] > 0) > 0 else 0,
        'average_loss': sum(t['profit_loss'] for t in trades if t['profit_loss'] <= 0) / sum(1 for t in trades if t['profit_loss'] <= 0) if sum(1 for t in trades if t['profit_loss'] <= 0) > 0 else 0,
        'profit_factor': abs(sum(t['profit_loss'] for t in trades if t['profit_loss'] > 0) / sum(t['profit_loss'] for t in trades if t['profit_loss'] <= 0)) if sum(t['profit_loss'] for t in trades if t['profit_loss'] <= 0) != 0 else float('inf'),
        'max_drawdown': max([(max(equity[:i+1]) - equity[i]) / max(equity[:i+1]) * 100 for i in range(len(equity))]) if equity else 0
    }
    
    logger.info(f"Backtest completed with {len(trades)} trades")
    logger.info(f"Win rate: {results['win_rate']:.2f}%")
    logger.info(f"Total return: {results['total_return']:.2f}%")
    logger.info(f"Profit factor: {results['profit_factor']:.2f}")
    logger.info(f"Max drawdown: {results['max_drawdown']:.2f}%")
    
    return results, trades, equity

def visualize_backtest(args, df, trades, equity):
    """Visualize backtest results"""
    if not trades:
        logger.warning("No trades to visualize")
        return
    
    logger.info("Creating backtest visualization...")
    
    # Create output directory
    output_dir = Path("backtest_results")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create equity curve
    plt.figure(figsize=(12, 6))
    plt.plot(range(len(equity)), equity)
    plt.title(f"{args.symbol} {args.timeframe} Equity Curve")
    plt.xlabel("Candles")
    plt.ylabel("Equity")
    plt.grid(True)
    
    # Save equity curve
    equity_path = output_dir / f"{args.symbol}_{args.timeframe}_equity.png"
    plt.savefig(equity_path)
    plt.close()
    
    logger.info(f"Equity curve saved to {equity_path}")
    
    # Create trade visualization
    visualizer = Visualization()
    
    # Visualize each trade
    for i, trade in enumerate(trades):
        # Get data for visualization (50 candles before and 20 after the trade)
        entry_idx = df.index.get_loc(trade['entry_time'])
        start_idx = max(0, entry_idx - 50)
        
        # If trade has exit time, include candles after exit
        if 'exit_time' in trade and trade['exit_time'] is not None:
            exit_idx = df.index.get_loc(trade['exit_time'])
            end_idx = min(len(df), exit_idx + 20)
        else:
            end_idx = min(len(df), entry_idx + 20)
        
        # Get visualization data
        viz_data = df.iloc[start_idx:end_idx]
        
        # Create trade data for visualization
        trade_data = {
            'symbol': args.symbol,
            'direction': trade['direction'],
            'entry_price': trade['entry_price'],
            'stop_loss': trade['stop_loss'],
            'take_profit': trade['take_profit'],
            'exit_price': trade.get('exit_price'),
            'entry_time': trade['entry_time'],
            'exit_time': trade.get('exit_time'),
            'profit_loss': trade.get('profit_loss', 0),
            'setup_type': trade.get('setup_type', 'Unknown')
        }
        
        # Create chart
        chart_buffer = visualizer.create_trade_chart(viz_data, trade_data)
        
        if chart_buffer:
            # Save chart
            chart_path = output_dir / f"{args.symbol}_{args.timeframe}_trade_{i+1}.png"
            visualizer.save_chart_to_file(chart_buffer, chart_path)
            logger.info(f"Trade chart saved to {chart_path}")
    
    # Create summary visualization
    plt.figure(figsize=(12, 8))
    
    # Plot price
    plt.subplot(2, 1, 1)
    plt.plot(df.index, df['close'])
    
    # Plot entry and exit points
    for trade in trades:
        if trade['direction'] == 'BUY':
            plt.scatter(trade['entry_time'], trade['entry_price'], color='green', marker='^', s=100)
            if 'exit_time' in trade and trade['exit_time'] is not None:
                plt.scatter(trade['exit_time'], trade['exit_price'], color='red', marker='v', s=100)
        else:  # SELL
            plt.scatter(trade['entry_time'], trade['entry_price'], color='red', marker='v', s=100)
            if 'exit_time' in trade and trade['exit_time'] is not None:
                plt.scatter(trade['exit_time'], trade['exit_price'], color='green', marker='^', s=100)
    
    plt.title(f"{args.symbol} {args.timeframe} Price with Trades")
    plt.ylabel("Price")
    plt.grid(True)
    
    # Plot equity curve
    plt.subplot(2, 1, 2)
    plt.plot(range(len(equity)), equity)
    plt.title("Equity Curve")
    plt.xlabel("Candles")
    plt.ylabel("Equity")
    plt.grid(True)
    
    # Save summary chart
    summary_path = output_dir / f"{args.symbol}_{args.timeframe}_summary.png"
    plt.tight_layout()
    plt.savefig(summary_path)
    plt.close()
    
    logger.info(f"Summary chart saved to {summary_path}")

def save_backtest_results(args, results, trades):
    """Save backtest results to file"""
    if not results or not trades:
        logger.warning("No results to save")
        return
    
    logger.info("Saving backtest results...")
    
    # Create output directory
    output_dir = Path("backtest_results")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Convert trades to serializable format
    serializable_trades = []
    for trade in trades:
        serializable_trade = {
            'symbol': trade['symbol'],
            'direction': trade['direction'],
            'entry_price': trade['entry_price'],
            'stop_loss': trade['stop_loss'],
            'take_profit': trade['take_profit'],
            'entry_time': trade['entry_time'].isoformat(),
            'exit_time': trade['exit_time'].isoformat() if 'exit_time' in trade and trade['exit_time'] is not None else None,
            'exit_price': trade.get('exit_price'),
            'profit_loss': trade.get('profit_loss', 0),
            'exit_reason': trade.get('exit_reason'),
            'setup_type': trade.get('setup_type', 'Unknown'),
            'strength': trade.get('strength', 0),
            'risk_reward': trade.get('risk_reward', 0)
        }
        
        serializable_trades.append(serializable_trade)
    
    # Create results dictionary
    output_results = {
        'backtest_params': {
            'symbol': args.symbol,
            'timeframe': args.timeframe,
            'start_date': args.start_date,
            'end_date': args.end_date,
            'initial_capital': args.initial_capital,
            'position_size': args.position_size,
            'window_size': args.window_size
        },
        'backtest_results': results,
        'trades': serializable_trades
    }
    
    # Save to JSON
    results_path = output_dir / f"{args.symbol}_{args.timeframe}_results.json"
    with open(results_path, 'w') as f:
        json.dump(output_results, f, indent=2)
    
    logger.info(f"Results saved to {results_path}")
    
    # Save trades to CSV
    trades_df = pd.DataFrame([
        {
            'symbol': t['symbol'],
            'direction': t['direction'],
            'entry_price': t['entry_price'],
            'stop_loss': t['stop_loss'],
            'take_profit': t['take_profit'],
            'entry_time': t['entry_time'],
            'exit_time': t.get('exit_time'),
            'exit_price': t.get('exit_price'),
            'profit_loss': t.get('profit_loss', 0),
            'exit_reason': t.get('exit_reason', ''),
            'setup_type': t.get('setup_type', 'Unknown'),
            'risk_reward': t.get('risk_reward', 0)
        }
        for t in trades
    ])
    
    trades_path = output_dir / f"{args.symbol}_{args.timeframe}_trades.csv"
    trades_df.to_csv(trades_path)
    
    logger.info(f"Trades saved to {trades_path}")

def main():
    """Main function"""
    # Parse command line arguments
    args = parse_args()
    
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
    
    # Construct the file path
    file_path = Path(f"charts/{args.market}/{args.symbol}{csv_suffix}.csv")
    logger.info(f"Looking for data file at: {file_path}")
    
    # Load data
    df = load_test_data(file_path)
    
    if df is None or df.empty:
        logger.error("No data available for testing")
        return
    
    # Run backtest
    results, trades, equity = run_backtest(args, df)
    
    if results and trades:
        # Visualize backtest
        visualize_backtest(args, df, trades, equity)
        
        # Save results
        save_backtest_results(args, results, trades)
        
        logger.info("Backtest completed successfully")
    else:
        logger.error("Backtest failed to generate results")

if __name__ == "__main__":
    main()
