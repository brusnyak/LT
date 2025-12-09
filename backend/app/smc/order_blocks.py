"""
Order Block Detection Algorithm

Order blocks are institutional supply/demand zones where smart money entered positions.

Detection Criteria:
1. A candle must sweep previous liquidity (swing high or swing low)
2. The candle that swept liquidity must become a pivot point (swing reversal)
3. The OB zone is defined by the candle's high/low/mid

Types:
- Bullish OB: Bearish candle that swept sell-side liquidity (SSL) and then price reversed up
- Bearish OB: Bullish candle that swept buy-side liquidity (BSL) and then price reversed down
"""
from typing import List, Dict, Optional, Tuple, Literal # Import Literal
import pandas as pd
import numpy as np
from app.models.smc import OrderBlock, SwingPoint, MarketStructureEvent # Import OrderBlock, SwingPoint, MarketStructureEvent models
from app.smc.swings import SwingDetector # Needed for LTF refinement if we pass raw df


class OrderBlockDetector:
    """
    Detect order blocks based on liquidity sweeps and pivot formation
    
    An order block is valid when:
    1. Price sweeps a previous swing high/low (liquidity grab)
    2. The candle that swept becomes a swing point itself (reversal)
    3. The zone hasn't been fully mitigated
    """
    
    def __init__(self, lookback_window: int = 30):
        """
        Initialize order block detector
        
        Args:
            lookback_window: How many candles to look back for liquidity sweeps
                            30 for M30, 200+ for M5 as per user specs
        """
        self.lookback_window = lookback_window
    
    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate Average True Range"""
        high = df['high']
        low = df['low']
        close = df['close']
        
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.ewm(span=period, adjust=False).mean() # Use EMA for ATR as in Pine Script
        return atr

    def detect_order_blocks(
        self, 
        df: pd.DataFrame, 
        structure_events: List[MarketStructureEvent],
        df_ltf: Optional[pd.DataFrame] = None # For LTF refinement
    ) -> List[OrderBlock]:
        """
        Detect order blocks based on market structure breaks (BOS/CHOCH) and impulse origin.
        Incorporates volatility filter and optional LTF refinement.
        
        Args:
            df: OHLCV dataframe (current timeframe)
            structure_events: List of MarketStructureEvent objects
            df_ltf: Optional lower timeframe dataframe for OB refinement
            
        Returns:
            List of OrderBlock objects
        """
        order_blocks: List[OrderBlock] = []
        existing_indices = set()
        
        # Calculate ATR for volatility filter (using 200 period as per Pine default)
        atr = self._calculate_atr(df, period=200)
        
        for event in structure_events:
            # The impulse origin is the pivot that was broken to create the BOS/CHOCH
            # For a bullish BOS/CHOCH, the impulse origin is the last swing low before the break
            # For a bearish BOS/CHOCH, the impulse origin is the last swing high before the break
            
            # In the new market_structure.py, the pivot_index is the previous swing that was broken.
            # We need the *origin* of the impulse that caused the break.
            # This requires finding the swing point *before* the pivot_index that defines the impulse leg.
            
            # For now, let's assume the pivot_index in MarketStructureEvent is the candle that forms the OB.
            # This needs to be refined based on how MarketStructureDetector is implemented.
            # For a BOS/CHOCH, the OB is typically the last opposing candle before the impulse that broke structure.
            
            # Let's simplify for now and assume the OB is the candle at the pivot_index
            # This will need further refinement to match Pine Script's "origin of impulse" logic.
            
            ob_candle_index = event.pivot_index # This is the candle that was broken
            
            # We need the candle *before* the break that initiated the impulse.
            # This is a more complex logic that needs to be implemented.
            # For now, let's use the candle at the pivot_index as a placeholder.
            
            # A better approach: find the last candle *before* the structure break that is an opposing candle.
            # This requires iterating backwards from the event.index to find the actual OB candle.
            
            # For simplicity in this iteration, let's assume the OB is the candle at event.pivot_index
            # This is a temporary simplification and needs to be improved.
            
            # Let's try to find the actual OB candle: the last candle *before* the structure break
            # that is an opposing candle to the direction of the impulse.
            
            # For a bullish BOS/CHOCH (price broke above a high), the OB is a bearish candle
            # before the break.
            # For a bearish BOS/CHOCH (price broke below a low), the OB is a bullish candle
            # before the break.
            
            ob_idx = -1
            if event.direction == 'bullish': # Price broke above a high, looking for bearish OB
                for k in range(event.index - 1, -1, -1):
                    if df['close'].iloc[k] < df['open'].iloc[k]: # Bearish candle
                        ob_idx = k
                        break
            elif event.direction == 'bearish': # Price broke below a low, looking for bullish OB
                for k in range(event.index - 1, -1, -1):
                    if df['close'].iloc[k] > df['open'].iloc[k]: # Bullish candle
                        ob_idx = k
                        break
            
            if ob_idx == -1:
                continue # No suitable OB candle found
            
            # Deduplication: Don't create multiple OBs at the same candle
            if ob_idx in existing_indices:
                continue
                
            # Volatility Filter:
            # Pine: highVolatilityBar = (high - low) >= (2 * volatilityMeasure)
            candle_range = df['high'].iloc[ob_idx] - df['low'].iloc[ob_idx]
            threshold = atr.iloc[ob_idx] if not np.isnan(atr.iloc[ob_idx]) else 0
            
            # If ATR is NaN (start of data), skip filter or accept. Let's accept.
            if threshold > 0 and candle_range < (2.0 * threshold): # Using 2.0 as per Pine Script
                continue
            
            ob_high = df['high'].iloc[ob_idx]
            ob_low = df['low'].iloc[ob_idx]
            ob_open = df['open'].iloc[ob_idx]
            ob_close = df['close'].iloc[ob_idx]

            # LTF Refinement (as per Pine Script's storeOrdeBlock)
            if df_ltf is not None:
                # Find the corresponding LTF candles within the OB candle's timeframe
                ltf_start_time = df.index[ob_idx]
                ltf_end_time = df.index[ob_idx] + (df.index[1] - df.index[0]) # Duration of the current TF candle
                
                ltf_candles_in_ob = df_ltf[(df_ltf.index >= ltf_start_time) & (df_ltf.index < ltf_end_time)]
                
                if not ltf_candles_in_ob.empty:
                    if event.direction == 'bullish': # Looking for bearish OB, refine with last bullish LTF candle
                        # Find last bullish LTF candle within the OB candle
                        last_bullish_ltf = ltf_candles_in_ob[ltf_candles_in_ob['close'] > ltf_candles_in_ob['open']].iloc[-1:]
                        if not last_bullish_ltf.empty:
                            ob_high = max(ob_high, last_bullish_ltf['high'].iloc[0])
                            ob_low = max(ob_low, last_bullish_ltf['low'].iloc[0])
                    elif event.direction == 'bearish': # Looking for bullish OB, refine with last bearish LTF candle
                        # Find last bearish LTF candle within the OB candle
                        last_bearish_ltf = ltf_candles_in_ob[ltf_candles_in_ob['close'] < ltf_candles_in_ob['open']].iloc[-1:]
                        if not last_bearish_ltf.empty:
                            ob_high = min(ob_high, last_bearish_ltf['high'].iloc[0])
                            ob_low = min(ob_low, last_bearish_ltf['low'].iloc[0])

            ob_type: Literal['bullish', 'bearish'] = 'bullish' if event.direction == 'bearish' else 'bearish' # OB is opposite to impulse direction
            
            new_ob = OrderBlock( # Explicitly create Pydantic model
                type=ob_type,
                candle_index=ob_idx,
                timestamp=df.index[ob_idx],
                high=ob_high,
                low=ob_low,
                mid=(ob_high + ob_low) / 2,
                state='active',
                mitigation_level=0, # Ensure mitigation_level is always initialized
                liquidity_swept=0.0, # Placeholder
                lookback_candles=self.lookback_window,
                is_breaker=False,
                original_type=ob_type,
                breaker_time=None
            )
            order_blocks.append(new_ob)
            existing_indices.add(ob_idx)
        
        return order_blocks
    
    def update_ob_states(self, df: pd.DataFrame, order_blocks: List[OrderBlock]) -> List[OrderBlock]:
        """
        Update order block states based on price interaction.
        Tracks multi-level mitigation (25%, 50%, 75%, Full).
        Handles Breaker Blocks (flipping polarity on full mitigation).
        """
        # No longer converting to dict, work directly with Pydantic objects
        # Explicitly import OrderBlock here to ensure the latest definition is used
        from app.models.smc import OrderBlock 

        for ob in order_blocks:
            # Debugging: Print type of ob
            # print(f"DEBUG: Type of ob in update_ob_states: {type(ob)}")
            if not isinstance(ob, OrderBlock):
                # print(f"DEBUG: ob is not an OrderBlock Pydantic model. Skipping.")
                continue

            ob_idx = ob.candle_index
            ob_high = ob.high
            ob_low = ob.low
            ob_range = ob.high - ob.low
            
            if ob_range == 0:
                continue
                
            # Check all candles after the OB formation
            for i in range(ob_idx + 1, len(df)):
                candle_high = df['high'].iloc[i]
                candle_low = df['low'].iloc[i]
                
                # Skip if already fully mitigated/breaker (unless we want to track breaker mitigation too)
                if ob.mitigation_level >= 4: # Direct attribute access
                    break
                
                if ob.type == 'bullish':
                    # Bullish OB: Price comes DOWN into it
                    if candle_low <= ob_high:
                        if ob.state == 'active':
                            setattr(ob, 'state', 'touched')
                            
                        # Calculate penetration depth
                        penetration = ob_high - candle_low
                        fill_percent = penetration / ob_range
                        
                        # Update mitigation level
                        if fill_percent >= 1.0:
                            setattr(ob, 'mitigation_level', 4)
                            setattr(ob, 'state', 'mitigated')
                            
                            # BREAKER BLOCK LOGIC
                            # Bullish OB broken -> Becomes Bearish Breaker
                            setattr(ob, 'is_breaker', True)
                            setattr(ob, 'original_type', 'bullish')
                            setattr(ob, 'type', 'bearish') # Flip polarity
                            setattr(ob, 'breaker_time', df.index[i])
                            
                        elif fill_percent >= 0.75:
                            setattr(ob, 'mitigation_level', max(ob.mitigation_level, 3))
                        elif fill_percent >= 0.50:
                            setattr(ob, 'mitigation_level', max(ob.mitigation_level, 2))
                        elif fill_percent >= 0.25:
                            setattr(ob, 'mitigation_level', max(ob.mitigation_level, 1))
                            
                        if ob.state == 'mitigated':
                            break
                
                elif ob.type == 'bearish':
                    # Bearish OB: Price comes UP into it
                    if candle_high >= ob_low:
                        if ob.state == 'active':
                            setattr(ob, 'state', 'touched')
                            
                        # Calculate penetration depth
                        penetration = candle_high - ob_low
                        fill_percent = penetration / ob_range
                        
                        # Update mitigation level
                        if fill_percent >= 1.0:
                            setattr(ob, 'mitigation_level', 4)
                            setattr(ob, 'state', 'mitigated')
                            
                            # BREAKER BLOCK LOGIC
                            # Bearish OB broken -> Becomes Bullish Breaker
                            setattr(ob, 'is_breaker', True)
                            setattr(ob, 'original_type', 'bearish')
                            setattr(ob, 'type', 'bullish') # Flip polarity
                            setattr(ob, 'breaker_time', df.index[i])
                            
                        elif fill_percent >= 0.75:
                            setattr(ob, 'mitigation_level', max(ob.mitigation_level, 3))
                        elif fill_percent >= 0.50:
                            setattr(ob, 'mitigation_level', max(ob.mitigation_level, 2))
                        elif fill_percent >= 0.25:
                            setattr(ob, 'mitigation_level', max(ob.mitigation_level, 1))
                            
                        if ob.state == 'mitigated':
                            break
        
        return order_blocks # Return the list of modified Pydantic objects


def get_ob_lookback_window(timeframe: str) -> int:
    """
    Get optimal lookback window for OB detection per timeframe
    
    Args:
        timeframe: Timeframe string
        
    Returns:
        Lookback window in candles
    """
    lookback_config = {
        'M1': 100,
        'M5': 200,   # User specified 200+ for M5
        'M15': 100,
        'M30': 50,   # User specified 50 for M30
        'H1': 30,
        'H4': 20,
        'D1': 15,
    }
    
    return lookback_config.get(timeframe, 50)
