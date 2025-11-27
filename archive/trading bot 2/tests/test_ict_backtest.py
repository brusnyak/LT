#!/usr/bin/env python
"""
Test script for ICT strategy backtesting
"""

import os
import sys
import logging
import argparse
import uuid
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Add parent directory to path to import trading_bot modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from trading_bot.strategy.ict_strategy import ICTStrategy
from trading_bot.journal.prop_firm_tracker import PropFirmChallenge

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Test ICT strategy backtesting')
    
    # Required arguments
    parser.add_argument('--symbol', type=str, required=True, help='Trading symbol (e.g., EURUSD)')
    parser.add_argument('--market', type=str, required=True, choices=['forex', 'crypto', 'indices', 'metals'], 
                        help='Market type')
    
    # Optional arguments
    parser.add_argument('--timeframe', type=str, default='H1', help='Timeframe (default: H1)')
    parser.add_argument('--start-date', type=str, default='2022-02-22', 
                        help='Start date (YYYY-MM-DD, default: 2022-02-22)')
    parser.add_argument('--end-date', type=str, default=None, 
                        help='End date (YYYY-MM-DD, default: 2022-03-22)')
    parser.add_argument('--initial-capital', type=float, default=10000.0, 
                        help='Initial capital (default: 10000.0)')
    parser.add_argument('--risk-per-trade', type=float, default=0.02, 
                        help='Risk per trade as fraction of capital (default: 0.02)')
    parser.add_argument('--output-dir', type=str, default='backtest_results', 
                        help='Output directory (default: backtest_results)')
    parser.add_argument('--progressive', action='store_true', 
                        help='Run progressive backtest (day by day)')
    parser.add_argument('--visualize', action='store_true', 
                        help='Generate visualization charts')
    
    return parser.parse_args()

def load_data(args):
    """Load historical data for backtesting"""
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
        
        # IMPORTANT: Properly handle end_date
        if args.end_date:
            end_date = pd.to_datetime(args.end_date)
            logger.info(f"Filtering data from {start_date} to {end_date}")
        else:
            # If no end date specified, use the last available date
            end_date = df.index[-1]
            logger.info(f"No end date specified, using last available date: {end_date}")
        
        # Apply date filtering
        df = df[(df.index >= start_date) & (df.index <= end_date)]
        
        if df.empty:
            logger.error(f"No data available for {args.symbol} {args.timeframe} in the specified date range")
            return None
        
        logger.info(f"Filtered to {len(df)} candles from {df.index[0]} to {df.index[-1]}")
        
        return df
        
    except Exception as e:
        logger.error(f"Error parsing CSV file {file_path}: {e}")
        return None

class SimpleBacktestEngine:
    """Simplified backtest engine for testing"""
    
    def __init__(self, initial_capital=10000.0, risk_per_trade=0.02, lookback=100):
        """Initialize the backtest engine"""
        self.initial_capital = initial_capital
        self.risk_per_trade = risk_per_trade
        self.lookback = lookback  # Number of candles to include for analysis
        self.trades = []
        self.equity = [initial_capital]
        self.drawdown = [0]
        self.strategy = None
        self.symbol = None
        self.timeframe = None
        self.df = None
        self.current_index = 0
    
    def initialize_backtest(self, df, strategy, symbol, timeframe):
        """Initialize a backtest"""
        self.df = df
        self.strategy = strategy
        self.symbol = symbol
        self.timeframe = timeframe
        self.current_index = 0
        self.trades = []
        self.equity = [self.initial_capital]
        self.drawdown = [0]
    
    def process_candle(self, candle):
        """Process a single candle"""
        # Get the current index in the full dataframe
        current_idx = self.df.index.get_loc(candle.index[0])
        
        # We need enough history for the strategy to analyze
        if current_idx < self.lookback:
            # Not enough history yet
            return
        
        # Get a window of data for analysis (including current candle)
        analysis_window = self.df.iloc[current_idx-self.lookback:current_idx+1]
        
        # Generate signal using the analysis window
        try:
            signal = self.strategy.generate_signal(analysis_window, self.symbol, self.timeframe)
            
            # Debug logging
            if signal and len(signal) > 0:
                logger.info(f"Signal generated at {candle.index[0]}: {signal.get('direction')} - {signal.get('setup_type', 'Unknown')}")
            
            # If signal is valid, create a trade
            if signal and isinstance(signal, dict) and 'direction' in signal and 'entry_price' in signal:
                # Ensure we have stop loss and take profit
                if 'stop_loss' not in signal or 'take_profit' not in signal:
                    # Calculate default stop loss and take profit
                    if signal['direction'] == 'BUY':
                        signal['stop_loss'] = signal['entry_price'] * 0.99  # 1% below entry
                        signal['take_profit'] = signal['entry_price'] * 1.02  # 2% above entry
                    else:
                        signal['stop_loss'] = signal['entry_price'] * 1.01  # 1% above entry
                        signal['take_profit'] = signal['entry_price'] * 0.98  # 2% below entry
                
                # Calculate position size
                risk_amount = self.equity[-1] * self.risk_per_trade
                risk_pips = abs(signal['entry_price'] - signal['stop_loss'])
                position_size = risk_amount / risk_pips if risk_pips > 0 else 0
                
                # Create trade
                trade = {
                    'id': str(uuid.uuid4()),
                    'symbol': self.symbol,
                    'direction': signal['direction'],
                    'entry_price': signal['entry_price'],
                    'stop_loss': signal['stop_loss'],
                    'take_profit': signal['take_profit'],
                    'position_size': position_size,
                    'entry_time': candle.index[0].isoformat(),
                    'exit_time': None,
                    'exit_price': None,
                    'profit': 0,
                    'status': 'open',
                    'strategy': signal.get('strategy', 'ICT'),
                    'setup_type': signal.get('setup_type', 'Unknown')
                }
                
                logger.info(f"Created trade: {trade['direction']} at {trade['entry_price']}")
                self.trades.append(trade)
        except Exception as e:
            logger.error(f"Error processing candle at {candle.index[0]}: {e}", exc_info=True)
        
        # Update existing trades
        self._update_trades(candle)
        
        # Update equity and drawdown
        current_equity = self._calculate_equity()
        self.equity.append(current_equity)
        
        # Calculate drawdown
        peak_equity = max(self.equity)
        current_drawdown = (peak_equity - current_equity) / peak_equity * 100 if peak_equity > 0 else 0
        self.drawdown.append(current_drawdown)
        
        # Increment current index
        self.current_index += 1
        
    def _update_trades(self, candle):
        """Update existing trades based on current candle"""
        for trade in self.trades:
            # Skip closed trades
            if trade['status'] != 'open':
                continue
            
            # Get candle data
            high = candle['high'].iloc[0]
            low = candle['low'].iloc[0]
            close = candle['close'].iloc[0]
            
            # Check for stop loss or take profit hit
            if trade['direction'] == 'BUY':
                # Check stop loss
                if low <= trade['stop_loss']:
                    trade['exit_price'] = trade['stop_loss']
                    trade['exit_time'] = candle.index[0].isoformat()
                    trade['profit'] = (trade['exit_price'] - trade['entry_price']) * trade['position_size']
                    trade['status'] = 'closed'
                # Check take profit
                elif high >= trade['take_profit']:
                    trade['exit_price'] = trade['take_profit']
                    trade['exit_time'] = candle.index[0].isoformat()
                    trade['profit'] = (trade['exit_price'] - trade['entry_price']) * trade['position_size']
                    trade['status'] = 'closed'
            else:  # SELL
                # Check stop loss
                if high >= trade['stop_loss']:
                    trade['exit_price'] = trade['stop_loss']
                    trade['exit_time'] = candle.index[0].isoformat()
                    trade['profit'] = (trade['entry_price'] - trade['exit_price']) * trade['position_size']
                    trade['status'] = 'closed'
                # Check take profit
                elif low <= trade['take_profit']:
                    trade['exit_price'] = trade['take_profit']
                    trade['exit_time'] = candle.index[0].isoformat()
                    trade['profit'] = (trade['entry_price'] - trade['exit_price']) * trade['position_size']
                    trade['status'] = 'closed'
    
    def _calculate_equity(self):
        """Calculate current equity"""
        equity = self.initial_capital
        
        # Add profit from closed trades
        for trade in self.trades:
            if trade['status'] == 'closed':
                equity += trade['profit']
        
        return equity
    
    def get_results(self):
        """Get backtest results"""
        return {
            'trades': self.trades,
            'equity': self.equity,
            'drawdown': self.drawdown,
            'start_date': self.df.index[0].isoformat() if self.df is not None and not self.df.empty else None,
            'end_date': self.df.index[-1].isoformat() if self.df is not None and not self.df.empty else None
        }

def run_standard_backtest(args, df):
    """Run a standard backtest (all at once)"""
    logger.info(f"Running standard backtest for {args.symbol} {args.timeframe}")
    
    # Initialize backtest engine with lookback
    engine = SimpleBacktestEngine(
        initial_capital=args.initial_capital,
        risk_per_trade=args.risk_per_trade,
        lookback=100  # Use 100 candles for analysis
    )
    
    # Initialize ICT strategy
    strategy = ICTStrategy()
    
    # Test direct signal generation
    test_signal = test_direct_signal_generation(df, args.symbol, args.timeframe)
    logger.info(f"Test signal generation result: {test_signal}")
    
    # Initialize backtest
    engine.initialize_backtest(
        df=df,
        strategy=strategy,
        symbol=args.symbol,
        timeframe=args.timeframe
    )
    
    # Process all candles at once
    for i in range(len(df)):
        candle = df.iloc[[i]]
        engine.process_candle(candle)
    
    # Get results
    results = engine.get_results()
    
    logger.info(f"Backtest completed with {len(results['trades'])} trades")
    
    return results



def run_progressive_backtest(args, df):
    """Run a progressive backtest (day by day)"""
    logger.info(f"Running progressive backtest for {args.symbol} {args.timeframe}")
    
    # Initialize backtest engine
    engine = SimpleBacktestEngine(
        initial_capital=args.initial_capital,
        risk_per_trade=args.risk_per_trade
    )
    
    # Initialize ICT strategy - use default parameters
    strategy = ICTStrategy()
    
    # Initialize backtest
    engine.initialize_backtest(
        df=df,
        strategy=strategy,
        symbol=args.symbol,
        timeframe=args.timeframe
    )
    
    # Get unique dates in the dataframe
    dates = pd.Series(df.index.date).unique()
    logger.info(f"Progressive backtest will run through {len(dates)} trading days")
    
    # Process day by day
    for date in dates:
        logger.info(f"Processing day: {date}")
        
        # Get candles for this day
        day_mask = df.index.date == date
        day_candles = df[day_mask]
        
        # Process each candle
        for idx in day_candles.index:
            candle = df.loc[[idx]]
            engine.process_candle(candle)
        
        # Log daily summary
        daily_trades = [t for t in engine.trades if pd.to_datetime(t['entry_time']).date() == date]
        logger.info(f"Day {date}: {len(daily_trades)} trades, equity: {engine.equity[-1]:.2f}")
    
    # Get results
    results = engine.get_results()
    logger.info(f"Progressive backtest completed with {len(results['trades'])} trades")
    
    return results

def analyze_results(args, df, results):
    """Analyze backtest results"""
    logger.info("Analyzing backtest results")
    
    # Calculate basic metrics
    total_trades = len(results['trades'])
    winning_trades = sum(1 for t in results['trades'] if t.get('profit', 0) > 0)
    losing_trades = sum(1 for t in results['trades'] if t.get('profit', 0) < 0)
    
    win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
    
    total_profit = sum(t.get('profit', 0) for t in results['trades'])
    total_loss = sum(t.get('profit', 0) for t in results['trades'] if t.get('profit', 0) < 0)
    profit_factor = abs(sum(t.get('profit', 0) for t in results['trades'] if t.get('profit', 0) > 0) / total_loss) if total_loss != 0 else float('inf')
    
    initial_capital = args.initial_capital
    final_capital = results['equity'][-1] if results['equity'] else initial_capital
    total_return = (final_capital - initial_capital) / initial_capital * 100
    
    # Calculate drawdown
    equity_curve = results['equity']
    drawdown = results.get('drawdown', [])
    
    if not drawdown and equity_curve:
        drawdown = []
        peak = equity_curve[0]
        
        for equity in equity_curve:
            if equity > peak:
                peak = equity
            drawdown_pct = (peak - equity) / peak * 100 if peak > 0 else 0
            drawdown.append(drawdown_pct)
    
    max_drawdown = max(drawdown) if drawdown else 0
    
    # Calculate average trade metrics
    avg_profit = total_profit / total_trades if total_trades > 0 else 0
    avg_win = sum(t.get('profit', 0) for t in results['trades'] if t.get('profit', 0) > 0) / winning_trades if winning_trades > 0 else 0
    avg_loss = abs(sum(t.get('profit', 0) for t in results['trades'] if t.get('profit', 0) < 0) / losing_trades) if losing_trades > 0 else 0
    
    # Calculate risk-reward ratio
    risk_reward_ratio = avg_win / avg_loss if avg_loss > 0 else float('inf')
    
    # Calculate expectancy
    expectancy = (win_rate / 100 * avg_win) - ((1 - win_rate / 100) * avg_loss)
    
    # Calculate trade frequency
    if df is not None and not df.empty and total_trades > 0:
        trading_days = len(pd.Series(df.index.date).unique())
        trades_per_day = total_trades / trading_days if trading_days > 0 else 0
    else:
        trading_days = 0
        trades_per_day = 0
    
    # Create performance dictionary
    performance = {
        'total_trades': total_trades,
        'winning_trades': winning_trades,
        'losing_trades': losing_trades,
        'win_rate': win_rate,
        'profit_factor': profit_factor,
        'total_return': total_return,
        'max_drawdown': max_drawdown,
        'final_capital': final_capital,
        'avg_profit': avg_profit,
        'avg_win': avg_win,
        'avg_loss': avg_loss,
        'risk_reward_ratio': risk_reward_ratio,
        'expectancy': expectancy,
        'trading_days': trading_days,
        'trades_per_day': trades_per_day
    }
    
    # Print summary
    logger.info("=== Backtest Summary ===")
    logger.info(f"Symbol: {args.symbol} {args.timeframe}")
    logger.info(f"Period: {df.index[0].date()} to {df.index[-1].date()}")
    logger.info(f"Total trades: {performance['total_trades']}")
    logger.info(f"Win rate: {performance['win_rate']:.2f}%")
    logger.info(f"Profit factor: {performance['profit_factor']:.2f}")
    logger.info(f"Total return: {performance['total_return']:.2f}%")
    logger.info(f"Max drawdown: {performance['max_drawdown']:.2f}%")
    logger.info(f"Risk-reward ratio: {performance['risk_reward_ratio']:.2f}")
    logger.info(f"Expectancy: ${performance['expectancy']:.2f}")
    logger.info(f"Trades per day: {performance['trades_per_day']:.2f}")
    
    return performance

def visualize_results(args, df, results, performance):
    """Generate visualization charts"""
    if not args.visualize:
        return
        
    logger.info("Generating visualization charts")
    
    try:
        # Create output directory if it doesn't exist
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate equity curve chart
        equity_curve = pd.Series(results['equity'], index=df.index[:len(results['equity'])])
        plt.figure(figsize=(12, 6))
        plt.plot(equity_curve)
        plt.title(f"{args.symbol} {args.timeframe} Equity Curve")
        plt.xlabel("Date")
        plt.ylabel("Equity")
        plt.grid(True)
        plt.savefig(output_dir / f"{args.symbol}_{args.timeframe}_equity_curve.png")
        plt.close()
        logger.info(f"Saved equity curve chart to {output_dir / f'{args.symbol}_{args.timeframe}_equity_curve.png'}")
        
        # Generate drawdown chart
        if 'drawdown' in results and results['drawdown']:
            drawdown = pd.Series(results['drawdown'], index=df.index[:len(results['drawdown'])])
            plt.figure(figsize=(12, 6))
            plt.plot(drawdown)
            plt.title(f"{args.symbol} {args.timeframe} Drawdown")
            plt.xlabel("Date")
            plt.ylabel("Drawdown (%)")
            plt.grid(True)
            plt.savefig(output_dir / f"{args.symbol}_{args.timeframe}_drawdown.png")
            plt.close()
            logger.info(f"Saved drawdown chart to {output_dir / f'{args.symbol}_{args.timeframe}_drawdown.png'}")
        
        # Generate trade chart with entry/exit points
        if results['trades']:
            # Create a subset of data for visualization (last 100 candles)
            chart_df = df.iloc[-min(len(df), 100):]
            
            # Filter trades to match the chart data
            chart_trades = [t for t in results['trades'] 
                           if pd.to_datetime(t['entry_time']) in chart_df.index]
            
            if chart_trades:
                plt.figure(figsize=(14, 7))
                
                # Plot price
                plt.plot(chart_df.index, chart_df['close'], label='Close Price')
                
                # Plot entry points
                for trade in chart_trades:
                    entry_time = pd.to_datetime(trade['entry_time'])
                    entry_price = trade['entry_price']
                    
                    if trade['direction'] == 'BUY':
                        plt.scatter(entry_time, entry_price, color='green', marker='^', s=100, label='Buy Entry' if 'Buy Entry' not in plt.gca().get_legend_handles_labels()[1] else "")
                    else:
                        plt.scatter(entry_time, entry_price, color='red', marker='v', s=100, label='Sell Entry' if 'Sell Entry' not in plt.gca().get_legend_handles_labels()[1] else "")
                    
                    # Plot exit points if trade is closed
                    if trade['status'] == 'closed' and trade['exit_time']:
                        exit_time = pd.to_datetime(trade['exit_time'])
                        exit_price = trade['exit_price']
                        
                        if trade['profit'] > 0:
                            plt.scatter(exit_time, exit_price, color='blue', marker='o', s=100, label='Profit Exit' if 'Profit Exit' not in plt.gca().get_legend_handles_labels()[1] else "")
                        else:
                            plt.scatter(exit_time, exit_price, color='black', marker='x', s=100, label='Loss Exit' if 'Loss Exit' not in plt.gca().get_legend_handles_labels()[1] else "")
                
                plt.title(f"{args.symbol} {args.timeframe} Trades")
                plt.xlabel("Date")
                plt.ylabel("Price")
                plt.legend()
                plt.grid(True)
                plt.savefig(output_dir / f"{args.symbol}_{args.timeframe}_trades.png")
                plt.close()
                logger.info(f"Saved trade chart to {output_dir / f'{args.symbol}_{args.timeframe}_trades.png'}")
        
        # Save results to CSV
        trades_df = pd.DataFrame(results['trades'])
        if not trades_df.empty:
            trades_df.to_csv(output_dir / f"{args.symbol}_{args.timeframe}_trades.csv", index=False)
            logger.info(f"Saved trades to {output_dir / f'{args.symbol}_{args.timeframe}_trades.csv'}")
        
        # Save performance metrics to CSV
        performance_df = pd.DataFrame([performance])
        performance_df.to_csv(output_dir / f"{args.symbol}_{args.timeframe}_performance.csv", index=False)
        logger.info(f"Saved performance metrics to {output_dir / f'{args.symbol}_{args.timeframe}_performance.csv'}")
        
        # Generate prop firm challenge metrics if applicable
        try:
            from trading_bot.journal.prop_firm_tracker import PropFirmChallenge
            
            # Create a sample prop firm challenge
            challenge_data = {
                'account_size': args.initial_capital,
                'challenge_type': 'Evaluation',
                'profit_target': 10.0,  # 10% profit target
                'max_total_loss': 5.0,  # 5% max loss
                'daily_loss_limit': 4.0,  # 4% daily loss limit
                'profit_share': 80.0,  # 80% profit share
                'drawdown_type': 'Trailing',
                'time_limit': 30,  # 30 days
                'leverage': {"FX": 30, "Indices": 10, "Crypto": 2},
                'min_trading_days': 5,
                'funded_min_trading_days': 3,
                'payout_frequency': 14,
                'allows_copy_trading': True,
                'prohibited_strategies': [],
                'start_date': df.index[0].to_pydatetime()
            }
            
            # Create a challenge object
            challenge = PropFirmChallenge(**challenge_data)
            
            # Calculate challenge metrics
            final_balance = results['equity'][-1] if results['equity'] else args.initial_capital
            profit_loss = final_balance - args.initial_capital
            profit_loss_pct = (profit_loss / args.initial_capital) * 100
            
            # Check for violations
            max_daily_loss = 0
            prev_day = None
            daily_equity = []
            
            for i, timestamp in enumerate(df.index[:len(results['equity'])]):
                day = timestamp.date()
                if prev_day is None or day != prev_day:
                    if daily_equity:
                        daily_loss = (min(daily_equity) - daily_equity[0]) / daily_equity[0] * 100
                        max_daily_loss = min(max_daily_loss, daily_loss)
                    daily_equity = [results['equity'][i]]
                    prev_day = day
                else:
                    daily_equity.append(results['equity'][i])
            
            # Check the last day
            if daily_equity:
                daily_loss = (min(daily_equity) - daily_equity[0]) / daily_equity[0] * 100
                max_daily_loss = min(max_daily_loss, daily_loss)
            
            # Calculate max drawdown
            max_drawdown = max(results['drawdown']) if 'drawdown' in results and results['drawdown'] else 0
            
            # Check for violations
            violations = []
            
            # Check max total loss
            if profit_loss_pct < -challenge.max_total_loss:
                violations.append(f"Max total loss exceeded: {profit_loss_pct:.2f}% (limit: {challenge.max_total_loss}%)")
            
            # Check daily loss limit
            if abs(max_daily_loss) > challenge.daily_loss_limit:
                violations.append(f"Daily loss limit exceeded: {abs(max_daily_loss):.2f}% (limit: {challenge.daily_loss_limit}%)")
            
            # Check max drawdown
            if max_drawdown > challenge.max_total_loss:
                violations.append(f"Max drawdown exceeded: {max_drawdown:.2f}% (limit: {challenge.max_total_loss}%)")
            
            # Calculate trading days
            trading_days = len(pd.Series(df.index[:len(results['equity'])].date).unique())
            
            # Check min trading days
            if trading_days < challenge.min_trading_days:
                violations.append(f"Minimum trading days not met: {trading_days} (required: {challenge.min_trading_days})")
            
            # Check if profit target reached
            profit_target_reached = profit_loss_pct >= challenge.profit_target
            
            # Create challenge results
            challenge_results = {
                'account_size': challenge.account_size,
                'final_balance': final_balance,
                'profit_loss': profit_loss,
                'profit_loss_pct': profit_loss_pct,
                'max_drawdown': max_drawdown,
                'max_daily_loss': abs(max_daily_loss),
                'trading_days': trading_days,
                'profit_target_reached': profit_target_reached,
                'violations': violations,
                'passed': profit_target_reached and not violations
            }
            
            # Save challenge results to CSV
            challenge_df = pd.DataFrame([challenge_results])
            challenge_df.to_csv(output_dir / f"{args.symbol}_{args.timeframe}_challenge.csv", index=False)
            logger.info(f"Saved prop firm challenge metrics to {output_dir / f'{args.symbol}_{args.timeframe}_challenge.csv'}")
            
            # Print challenge summary
            logger.info("=== Prop Firm Challenge Summary ===")
            logger.info(f"Account size: ${challenge.account_size:.2f}")
            logger.info(f"Final balance: ${final_balance:.2f}")
            logger.info(f"Profit/Loss: ${profit_loss:.2f} ({profit_loss_pct:.2f}%)")
            logger.info(f"Max drawdown: {max_drawdown:.2f}%")
            logger.info(f"Max daily loss: {abs(max_daily_loss):.2f}%")
            logger.info(f"Trading days: {trading_days}")
            logger.info(f"Profit target reached: {profit_target_reached}")
            
            if violations:
                logger.info("Violations:")
                for violation in violations:
                    logger.info(f"- {violation}")
            
            logger.info(f"Challenge passed: {profit_target_reached and not violations}")
            
        except Exception as e:
            logger.warning(f"Error generating prop firm challenge metrics: {e}")
    
    except Exception as e:
        logger.error(f"Error generating visualization: {e}", exc_info=True)

def save_results(args, results, performance):
    """Save backtest results to file"""
    logger.info("Saving backtest results")
    
    try:
        # Create output directory if it doesn't exist
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save trades to JSON
        import json
        
        # Convert trades to serializable format
        serializable_trades = []
        for trade in results['trades']:
            serializable_trade = {k: str(v) if isinstance(v, (pd.Timestamp, datetime)) else v 
                                 for k, v in trade.items()}
            serializable_trades.append(serializable_trade)
        
        # Create serializable results
        serializable_results = {
            'trades': serializable_trades,
            'equity': results['equity'],
            'drawdown': results['drawdown'],
            'start_date': results['start_date'],
            'end_date': results['end_date'],
            'performance': performance
        }
        
        # Save to JSON
        with open(output_dir / f"{args.symbol}_{args.timeframe}_results.json", 'w') as f:
            json.dump(serializable_results, f, indent=2)
        
        logger.info(f"Saved results to {output_dir / f'{args.symbol}_{args.timeframe}_results.json'}")
        
    except Exception as e:
        logger.error(f"Error saving results: {e}", exc_info=True)

def test_direct_signal_generation(df, symbol, timeframe):
    """Test direct signal generation with a sample window"""
    strategy = ICTStrategy()
    # Take a sample window (e.g., 100 candles)
    sample_window = df.iloc[-100:]
    signal = strategy.generate_signal(sample_window, symbol, timeframe)
    logger.info(f"Direct signal test: {signal}")
    return signal



def main():
    """Main function"""
    # Parse command line arguments
    args = parse_args()
    
    # Import visualization module if needed
    if args.visualize:
        try:
            from trading_bot.utils.visualization import setup_visualization
            setup_visualization()
            logger.info("Initialized visualization module")
        except ImportError:
            logger.warning("Visualization module not available, charts will not be generated")
            args.visualize = False
    
    # Load historical data
    df = load_data(args)
    
    if df is None or df.empty:
        logger.error("No data available for backtesting")
        return
    
    # Run backtest
    if args.progressive:
        results = run_progressive_backtest(args, df)
    else:
        results = run_standard_backtest(args, df)
    
    # Analyze results
    performance = analyze_results(args, df, results)
    
    # Generate visualization
    visualize_results(args, df, results, performance)
    
    # Save results
    save_results(args, results, performance)
    
    logger.info("Backtest completed successfully")

if __name__ == "__main__":
    main()

