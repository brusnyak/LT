"""
Backtrader Test Runner
Runs the StructureBasedStrategy with EURUSD M5 data
"""
import sys
import os
from pathlib import Path

# Add project root and backend to path
project_root = Path(__file__).parent.parent.parent
backend_root = project_root / 'backend'
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(backend_root))

import backtrader as bt
from datetime import datetime
import argparse

# Import our data feed
from app.backtest.data_feed import CSVDataFeed, load_csv_data

# Import the strategy
sys.path.insert(0, str(project_root / 'd_strategy'))
from def_strategy import StructureBasedStrategy


def run_backtest(
    data_path,
    start_date=None,
    end_date=None,
    initial_cash=20000.0,
    commission=0.0001,  # 1 pip spread for EURUSD
    **strategy_params
):
    """
    Run backtest with the given parameters
    
    Args:
        data_path: Path to CSV data file
        start_date: Start date for backtest (optional)
        end_date: End date for backtest (optional)
        initial_cash: Starting capital
        commission: Commission per trade (as fraction)
        **strategy_params: Strategy parameters to override
    """
    
    # Create Cerebro engine
    cerebro = bt.Cerebro()
    
    # Load data
    print(f"Loading data from: {data_path}")
    df = load_csv_data(data_path, start_date, end_date)
    print(f"Loaded {len(df)} candles")
    print(f"Date range: {df.index[0]} to {df.index[-1]}")
    
    # Create data feed
    data = CSVDataFeed(dataname=df)
    cerebro.adddata(data)
    
    # Add strategy
    cerebro.addstrategy(StructureBasedStrategy, **strategy_params)
    
    # Set broker parameters
    cerebro.broker.setcash(initial_cash)
    cerebro.broker.setcommission(commission=commission)
    
    # Add analyzers
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
    
    # Print starting conditions
    print('\n' + '='*80)
    print('BACKTEST STARTING')
    print('='*80)
    print(f'Starting Portfolio Value: ${cerebro.broker.getvalue():,.2f}')
    
    # Run backtest
    results = cerebro.run()
    strat = results[0]
    
    # Print ending conditions
    print('\n' + '='*80)
    print('BACKTEST COMPLETE')
    print('='*80)
    print(f'Final Portfolio Value: ${cerebro.broker.getvalue():,.2f}')
    print(f'P&L: ${cerebro.broker.getvalue() - initial_cash:,.2f}')
    print(f'ROI: {((cerebro.broker.getvalue() / initial_cash) - 1) * 100:.2f}%')
    
    # Print analyzer results
    print('\n' + '='*80)
    print('PERFORMANCE METRICS')
    print('='*80)
    
    # Sharpe Ratio
    sharpe = strat.analyzers.sharpe.get_analysis()
    print(f"Sharpe Ratio: {sharpe.get('sharperatio', 'N/A')}")
    
    # Drawdown
    dd = strat.analyzers.drawdown.get_analysis()
    print(f"Max Drawdown: {dd.get('max', {}).get('drawdown', 0):.2f}%")
    print(f"Max Drawdown $: ${dd.get('max', {}).get('moneydown', 0):,.2f}")
    
    # Returns
    returns = strat.analyzers.returns.get_analysis()
    print(f"Total Return: {returns.get('rtot', 0) * 100:.2f}%")
    print(f"Average Return: {returns.get('ravg', 0) * 100:.2f}%")
    
    # Trade Analysis
    trades = strat.analyzers.trades.get_analysis()
    total_trades = trades.get('total', {}).get('total', 0)
    won_trades = trades.get('won', {}).get('total', 0)
    lost_trades = trades.get('lost', {}).get('total', 0)
    
    print(f"\nTotal Trades: {total_trades}")
    print(f"Won: {won_trades}")
    print(f"Lost: {lost_trades}")
    
    if total_trades > 0:
        win_rate = (won_trades / total_trades) * 100
        print(f"Win Rate: {win_rate:.2f}%")
        
        if won_trades > 0:
            avg_win = trades.get('won', {}).get('pnl', {}).get('average', 0)
            print(f"Average Win: ${avg_win:.2f}")
        
        if lost_trades > 0:
            avg_loss = trades.get('lost', {}).get('pnl', {}).get('average', 0)
            print(f"Average Loss: ${avg_loss:.2f}")
    
    print('='*80)
    
    return cerebro, strat


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run Backtrader backtest')
    parser.add_argument('--data', type=str, 
                       default='LT1/data/forex/EURUSD_M5.csv',
                       help='Path to CSV data file')
    parser.add_argument('--start', type=str, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end', type=str, help='End date (YYYY-MM-DD)')
    parser.add_argument('--cash', type=float, default=20000.0, 
                       help='Initial cash')
    parser.add_argument('--commission', type=float, default=0.0001,
                       help='Commission per trade')
    
    args = parser.parse_args()
    
    # Resolve data path
    data_path = Path(args.data)
    if not data_path.is_absolute():
        data_path = project_root / data_path
    
    if not data_path.exists():
        print(f"Error: Data file not found: {data_path}")
        sys.exit(1)
    
    # Run backtest
    run_backtest(
        data_path=str(data_path),
        start_date=args.start,
        end_date=args.end,
        initial_cash=args.cash,
        commission=args.commission
    )
