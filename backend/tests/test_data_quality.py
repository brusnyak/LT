import pandas as pd
from datetime import datetime, timedelta

from app.core.data_loader import load_candle_data, set_data_source
from app.core.constants import Pair, Timeframe

def compare_data_sources(pair: str, timeframe: str, start_date: datetime, end_date: datetime, limit: int = 1000):
    """
    Compares historical data from cTrader and CSV for a given period.
    """
    print(f"\n{'='*60}")
    print(f"Comparing data for {pair} {timeframe} from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    print(f"{'='*60}")

    # Load from cTrader
    print("\n1. Loading data from cTrader...")
    try:
        set_data_source("ctrader")
        df_ctrader = load_candle_data(pair, timeframe, limit=limit, source="ctrader")
        df_ctrader = df_ctrader[(df_ctrader.index >= start_date) & (df_ctrader.index <= end_date)]
        print(f"   ✅ Loaded {len(df_ctrader)} candles from cTrader.")
        if not df_ctrader.empty:
            print(f"   cTrader Date range: {df_ctrader.index.min()} to {df_ctrader.index.max()}")
            print(df_ctrader.head(2).to_string())
            print("...")
            print(df_ctrader.tail(2).to_string())
        else:
            print("   ⚠️  No data from cTrader for the specified period.")
    except Exception as e:
        print(f"   ❌ Error loading from cTrader: {e}")
        df_ctrader = pd.DataFrame()

    # Load from CSV
    print("\n2. Loading data from CSV...")
    try:
        set_data_source("csv")
        df_csv = load_candle_data(pair, timeframe, limit=limit, source="csv")
        df_csv = df_csv[(df_csv.index >= start_date) & (df_csv.index <= end_date)]
        print(f"   ✅ Loaded {len(df_csv)} candles from CSV.")
        if not df_csv.empty:
            print(f"   CSV Date range: {df_csv.index.min()} to {df_csv.index.max()}")
            print(df_csv.head(2).to_string())
            print("...")
            print(df_csv.tail(2).to_string())
        else:
            print("   ⚠️  No data from CSV for the specified period.")
    except Exception as e:
        print(f"   ❌ Error loading from CSV: {e}")
        df_csv = pd.DataFrame()

    if df_ctrader.empty and df_csv.empty:
        print("\n❌ No data from either source to compare.")
        return False

    # Align and compare
    print("\n3. Comparing datasets...")
    try:
        # Ensure both dataframes have the same index (time) and columns
        common_columns = ['open', 'high', 'low', 'close', 'volume']
        
        # Filter to common time range
        common_index = df_ctrader.index.intersection(df_csv.index)
        
        if common_index.empty:
            print("   ⚠️  No common time points between cTrader and CSV data.")
            print(f"   cTrader count: {len(df_ctrader)}, CSV count: {len(df_csv)}")
            return False

        df_ctrader_aligned = df_ctrader.loc[common_index, common_columns]
        df_csv_aligned = df_csv.loc[common_index, common_columns]

        # Compare shapes
        if df_ctrader_aligned.shape != df_csv_aligned.shape:
            print(f"   ❌ Shape mismatch: cTrader {df_ctrader_aligned.shape}, CSV {df_csv_aligned.shape}")
            return False

        # Compare values
        differences = (df_ctrader_aligned - df_csv_aligned).abs().sum().sum()
        
        if differences > 0.0001: # Allow for minor floating point differences
            print(f"   ❌ Differences found! Total absolute difference: {differences:.4f}")
            # Show where differences occur
            diff_df = (df_ctrader_aligned - df_csv_aligned).abs()
            diff_rows = diff_df[(diff_df > 0.0001).any(axis=1)]
            if not diff_rows.empty:
                print("\n   Sample of differing rows (cTrader vs CSV):")
                for idx, row in diff_rows.head(5).iterrows():
                    print(f"   Time: {idx}")
                    print(f"     cTrader: {df_ctrader_aligned.loc[idx].to_dict()}")
                    print(f"     CSV:     {df_csv_aligned.loc[idx].to_dict()}")
            return False
        else:
            print("   ✅ Data quality is consistent between cTrader and CSV (within tolerance).")
            return True

    except Exception as e:
        print(f"   ❌ Error during comparison: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Define a recent period for comparison
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7) # Compare last 7 days

    # Example usage
    success = compare_data_sources(
        pair=Pair.EURUSD.value,
        timeframe=Timeframe.M5.value,
        start_date=start_date,
        end_date=end_date,
        limit=5000 # Load enough data to cover the period
    )
    
    if success:
        print("\nData quality test PASSED!")
        sys.exit(0)
    else:
        print("\nData quality test FAILED!")
        sys.exit(1)
