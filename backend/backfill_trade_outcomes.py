"""
Backfill Trade Outcomes
Determines WIN/LOSS/BE status for manual trades by simulating price movement
"""
import sys
import os
from datetime import datetime
from sqlalchemy.orm import Session

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models.db.trainer import DBManualTrade
from app.core.data_loader import load_candle_data
import pandas as pd


def backfill_trade_outcomes():
    """Backfill outcomes for all manual trades"""
    db = SessionLocal()
    
    try:
        # Get all trades without outcomes
        trades = db.query(DBManualTrade).filter(
            DBManualTrade.outcome == None
        ).all()
        
        print(f"\n🔍 Found {len(trades)} trades to backfill\n")
        
        if len(trades) == 0:
            print("✅ All trades already have outcomes!")
            return
        
        # Group by symbol for efficient data loading
        trades_by_symbol = {}
        for trade in trades:
            if trade.symbol not in trades_by_symbol:
                trades_by_symbol[trade.symbol] = []
            trades_by_symbol[trade.symbol].append(trade)
        
        total_wins = 0
        total_losses = 0
        total_open = 0
        
        # Process each symbol
        for symbol, symbol_trades in trades_by_symbol.items():
            print(f"📊 Processing {symbol} ({len(symbol_trades)} trades)...")
            
            # Load M1 data for precision
            try:
                df = load_candle_data(symbol, 'M1', limit=0, source='csv')
                # Reset index to get timestamp as column
                df = df.reset_index()
                df.rename(columns={'time': 'timestamp'}, inplace=True)
                df['timestamp'] = pd.to_datetime(df['timestamp'])
            except Exception as e:
                print(f"   ⚠️  Could not load M1 data for {symbol}: {e}")
                print(f"   Trying M5 data instead...")
                try:
                    df = load_candle_data(symbol, 'M5', limit=0, source='csv')
                    # Reset index to get timestamp as column
                    df = df.reset_index()
                    df.rename(columns={'time': 'timestamp'}, inplace=True)
                    df['timestamp'] = pd.to_datetime(df['timestamp'])
                except Exception as e2:
                    print(f"   ❌ Could not load any data for {symbol}: {e2}")
                    continue
            
            # Process each trade
            for trade in symbol_trades:
                entry_time = pd.to_datetime(trade.entry_time)
                
                # Make timezone-aware to match CSV data (Europe/Bratislava)
                if entry_time.tz is None:
                    import pytz
                    bratislava_tz = pytz.timezone('Europe/Bratislava')
                    entry_time = bratislava_tz.localize(entry_time)
                
                # Filter data after entry time
                future_data = df[df['timestamp'] > entry_time].copy()
                
                if len(future_data) == 0:
                    print(f"   ⚠️  No future data for trade {trade.id[:8]} (entry: {entry_time})")
                    trade.outcome = 'OPEN'
                    total_open += 1
                    continue
                
                # Check if SL or TP was hit
                sl_hit = False
                tp_hit = False
                close_time = None
                close_price = None
                
                for idx, candle in future_data.iterrows():
                    if trade.type == 'LONG':
                        # Check SL (below entry)
                        if candle['low'] <= trade.sl_price:
                            sl_hit = True
                            close_time = candle['timestamp']
                            close_price = trade.sl_price
                            break
                        # Check TP (above entry)
                        if candle['high'] >= trade.tp_price:
                            tp_hit = True
                            close_time = candle['timestamp']
                            close_price = trade.tp_price
                            break
                    else:  # SHORT
                        # Check SL (above entry)
                        if candle['high'] >= trade.sl_price:
                            sl_hit = True
                            close_time = candle['timestamp']
                            close_price = trade.sl_price
                            break
                        # Check TP (below entry)
                        if candle['low'] <= trade.tp_price:
                            tp_hit = True
                            close_time = candle['timestamp']
                            close_price = trade.tp_price
                            break
                
                # Determine outcome
                if tp_hit:
                    outcome = 'WIN'
                    # Calculate PnL (simplified, assuming 1 lot)
                    if trade.type == 'LONG':
                        pnl = trade.tp_price - trade.entry_price
                    else:
                        pnl = trade.entry_price - trade.tp_price
                    total_wins += 1
                elif sl_hit:
                    outcome = 'LOSS'
                    if trade.type == 'LONG':
                        pnl = trade.sl_price - trade.entry_price
                    else:
                        pnl = trade.entry_price - trade.sl_price
                    total_losses += 1
                else:
                    outcome = 'OPEN'
                    close_time = None
                    close_price = None
                    pnl = 0
                    total_open += 1
                
                # Update trade
                trade.outcome = outcome
                trade.close_time = close_time
                trade.close_price = close_price
                trade.pnl = pnl
                
                # Print result
                status_emoji = "✅" if outcome == "WIN" else "❌" if outcome == "LOSS" else "⏳"
                print(f"   {status_emoji} {trade.type:5} @ {trade.entry_price:.5f} → {outcome:4} (PnL: {pnl:+.5f})")
        
        # Commit all changes
        db.commit()
        
        # Print summary
        print(f"\n{'='*60}")
        print(f"✅ Backfill Complete!")
        print(f"{'='*60}")
        print(f"   Total Trades: {len(trades)}")
        print(f"   Wins:         {total_wins} ({total_wins/len(trades)*100:.1f}%)")
        print(f"   Losses:       {total_losses} ({total_losses/len(trades)*100:.1f}%)")
        print(f"   Open:         {total_open} ({total_open/len(trades)*100:.1f}%)")
        print(f"{'='*60}\n")
        
        # Print per-symbol stats
        print("📊 Per-Symbol Statistics:")
        for symbol in trades_by_symbol.keys():
            symbol_trades_all = db.query(DBManualTrade).filter(
                DBManualTrade.symbol == symbol,
                DBManualTrade.outcome != None
            ).all()
            
            if len(symbol_trades_all) > 0:
                wins = sum(1 for t in symbol_trades_all if t.outcome == 'WIN')
                losses = sum(1 for t in symbol_trades_all if t.outcome == 'LOSS')
                total = len(symbol_trades_all)
                win_rate = wins / total * 100 if total > 0 else 0
                
                print(f"   {symbol:8} - {total:3} trades | {wins:3} W / {losses:3} L | WR: {win_rate:.1f}%")
        
    except Exception as e:
        print(f"\n❌ Error during backfill: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    print("\n" + "="*60)
    print("🔄 Trade Outcome Backfill Script")
    print("="*60)
    backfill_trade_outcomes()
