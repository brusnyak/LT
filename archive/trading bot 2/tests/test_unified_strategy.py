"""
Test script for Unified Strategy
"""

import os
import sys
import logging
import pandas as pd
from datetime import datetime

# Add the parent directory to the path so we can import from trading_bot
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from trading_bot.strategy.unified_strategy import UnifiedStrategy
from trading_bot.strategy.signal_generator import SignalGenerator
from trading_bot.data.data_processor import DataProcessor

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_test_data(symbol, timeframe):
    """Load test data for a symbol and timeframe"""
    try:
        # Try different file paths
        file_paths = [
            f"data/{symbol}_{timeframe}.csv",
            f"charts/forex/{symbol}{timeframe.replace('M', '')}.csv",
            f"charts/crypto/{symbol}{timeframe.replace('M', '')}.csv",
            f"charts/indices/{symbol}{timeframe.replace('M', '')}.csv",
            f"charts/metals/{symbol}{timeframe.replace('M', '')}.csv"
        ]
        
        for file_path in file_paths:
            if os.path.exists(file_path):
                logger.info(f"Loading data from {file_path}")
                
                # Read the CSV file
                df = pd.read_csv(file_path)
                
                # Check if we have the required columns
                required_cols = ['open', 'high', 'low', 'close', 'volume']
                
                # Try to map common column names
                col_mapping = {
                    'Open': 'open',
                    'High': 'high',
                    'Low': 'low',
                    'Close': 'close',
                    'Volume': 'volume'
                }
                
                # Rename columns if needed
                df.columns = [col_mapping.get(col, col.lower()) for col in df.columns]
                
                # Ensure we have a datetime column
                if 'time' not in df.columns and 'date' not in df.columns and 'datetime' not in df.columns:
                    # Create a datetime column
                    df['time'] = pd.date_range(end=datetime.now(), periods=len(df), freq='1H')
                
                # Set the time column as index
                time_col = next((col for col in ['time', 'date', 'datetime'] if col in df.columns), None)
                if time_col:
                    df[time_col] = pd.to_datetime(df[time_col])
                    df = df.set_index(time_col)
                
                logger.info(f"Loaded {len(df)} rows for {symbol} {timeframe}")
                return df
        
        logger.error(f"No data file found for {symbol} {timeframe}")
        return None
    except Exception as e:
        logger.error(f"Error loading data for {symbol} {timeframe}: {e}")
        return None

def test_unified_strategy(symbol, timeframe):
    """Test the unified strategy on a symbol and timeframe"""
    try:
        # Load test data
        df = load_test_data(symbol, timeframe)
        if df is None or df.empty:
            logger.error(f"No test data available for {symbol} {timeframe}")
            return
        
        logger.info(f"Testing unified strategy with {len(df)} candles of {symbol} {timeframe} data")
        
        # Initialize the data processor
        data_processor = DataProcessor()
        
        # Initialize the unified strategy
        unified_strategy = UnifiedStrategy(data_processor=data_processor)
        
        # Initialize the signal generator
        signal_generator = SignalGenerator(data_processor=data_processor)
        
        # Add the unified strategy to the signal generator
        signal_generator.add_strategy("unified", unified_strategy)
        
        # Generate signals
        signals = signal_generator.generate_signals(symbol, df, timeframe, strategies=["unified"])
        
        # Log the results
        logger.info(f"Generated {len(signals)} signals")
        
        # Print signals
        for i, signal in enumerate(signals):
            logger.info(f"Signal {i+1}:")
            logger.info(f"  Type: {signal.get('type')}")
            logger.info(f"  Entry: {signal.get('entry_price')}")
            logger.info(f"  Stop Loss: {signal.get('stop_loss')}")
            logger.info(f"  Take Profit: {signal.get('take_profit')}")
            logger.info(f"  Risk-Reward: {signal.get('risk_reward', 0):.2f}")
            logger.info(f"  Strength: {signal.get('strength', 0)}")
            logger.info(f"  Reason: {signal.get('reason', 'No reason provided')}")
        
        # Get the analysis results
        analysis = unified_strategy.last_analysis if hasattr(unified_strategy, 'last_analysis') else None
        
        if analysis:
            logger.info("Analysis results:")
            logger.info(f"  Bias: {analysis.get('bias', 'unknown')}")
            logger.info(f"  Market structure: {analysis.get('market_structure', {}).keys()}")
            
            # Print timeframe-specific analysis
            for tf in ['higher_timeframe', 'middle_timeframe', 'lower_timeframe']:
                if tf in analysis:
                    logger.info(f"  {tf.replace('_', ' ').title()} analysis:")
                    tf_analysis = analysis[tf]
                    for key, value in tf_analysis.items():
                        if isinstance(value, dict):
                            logger.info(f"    {key}: {list(value.keys())}")
                        elif isinstance(value, list):
                            logger.info(f"    {key}: {len(value)} items")
                        else:
                            logger.info(f"    {key}: {value}")
        
        return signals, analysis
    except Exception as e:
        logger.error(f"Error testing unified strategy: {e}")
        import traceback
        traceback.print_exc()
        return None, None

if __name__ == "__main__":
    # Initialize the logger
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Load the data
    df = pd.read_csv('charts/forex/EURUSD30.csv')
    
    # Initialize the data processor
    data_processor = DataProcessor()
    
    # Initialize the unified strategy
    unified_strategy = UnifiedStrategy(data_processor=data_processor)
    
    # Generate signals
    signals = unified_strategy.generate_signals(df, 'EURUSD', 'M30')
    
    # Log the signals
    for signal in signals:
        logger.info(f"Signal: {signal}")
    