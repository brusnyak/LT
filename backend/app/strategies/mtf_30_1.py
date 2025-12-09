from typing import Dict, Optional, List, Any
import pandas as pd
from app.strategies.base import BaseStrategy
from app.models.strategy import Signal
from app.models.smc import OrderBlock # Import OrderBlock
from app.smc.order_blocks import OrderBlockDetector
from app.smc.market_structure import MarketStructureDetector
from app.smc.swings import SwingDetector

class MTF30_1Strategy(BaseStrategy):
    def __init__(self):
        super().__init__(
            name="MTF 30/1",
            description="Multi-timeframe strategy: 4H Trend, 30M POI, 1M Entry"
        )

    def analyze(self, df_multi_tf: Dict[str, pd.DataFrame], config: Optional[Dict] = None) -> Dict:
        df_4h = df_multi_tf.get('H4')
        df_30m = df_multi_tf.get('30M')
        df_1m = df_multi_tf.get('1M')

        if df_4h is None or df_30m is None or df_1m is None:
            return {"signals": [], "error": "Missing required timeframes (H4, 30M, 1M)"}

        # 1. Determine 4H Trend
        trend = self._analyze_4h_trend(df_4h)

        # 2. Find 30M POIs aligned with trend
        pois = self._find_30m_pois(df_30m, trend)

        # 3. Find 1M Entries inside POIs
        signals = self._find_1m_entries(df_1m, pois, trend)

        return {
            "signals": signals,
            "metadata": {"trend": trend, "pois": pois},
            "visualizations": {"overlays": pois}
        }

    def _analyze_4h_trend(self, df: pd.DataFrame) -> str:
        # Simple trend: Price > EMA 50
        ema = df['close'].ewm(span=50).mean()
        last_close = df['close'].iloc[-1]
        return "BULLISH" if last_close > ema.iloc[-1] else "BEARISH"

    def _find_30m_pois(self, df: pd.DataFrame, trend: str) -> List[Dict]:
        print(f"  _find_30m_pois: Analyzing {len(df)} 30M candles. Trend: {trend}")
        # Detect Swings
        swing_detector = SwingDetector(lookback_left=5, lookback_right=5)
        swing_highs, swing_lows = swing_detector.detect_swings(df)
        print(f"    Detected {len(swing_highs)} swing highs and {len(swing_lows)} swing lows.")
        classified_swings = swing_detector.classify_swings(swing_highs, swing_lows) # Classify swings
        
        # Detect Structure
        structure_detector = MarketStructureDetector()
        structure_events = structure_detector.detect_structure(df, classified_swings) # Pass classified swings
        print(f"    Detected {len(structure_events)} structure events.")
        
        # Detect OBs
        ob_detector = OrderBlockDetector(lookback_window=50)
        obs: List[OrderBlock] = ob_detector.detect_order_blocks(df, structure_events) # Ensure type hint
        print(f"    Detected {len(obs)} initial order blocks.")
        obs = ob_detector.update_ob_states(df, obs)
        print(f"    Updated OB states. Example OB: {obs[0].dict() if obs else 'None'}") # Use .dict() for printing
        
        # Filter POIs by Trend
        valid_pois = []
        for ob in obs:
            # Order Blocks don't have mitigation_level, they have 'state'
            if ob.state in ['active', 'touched', 'partial']: # Only consider unmitigated/active OBs
                if trend == "BULLISH" and ob.type == 'bullish':
                    valid_pois.append(ob.dict())
                elif trend == "BEARISH" and ob.type == 'bearish':
                    valid_pois.append(ob.dict())
        print(f"    Found {len(valid_pois)} POIs aligned with trend.")
        return valid_pois

    def _find_1m_entries(self, df: pd.DataFrame, pois: List[Dict], trend: str) -> List[Signal]:
        print(f"  _find_1m_entries: Analyzing {len(df)} 1M candles. POIs: {len(pois)}. Trend: {trend}")
        signals = []
        
        # Detect 1M Swings
        swing_detector = SwingDetector(lookback_left=5, lookback_right=5)
        swing_highs, swing_lows = swing_detector.detect_swings(df)
        classified_swings = swing_detector.classify_swings(swing_highs, swing_lows) # Classify 1M swings
        
        # Detect 1M Structure
        structure_detector = MarketStructureDetector()
        structure_events = structure_detector.detect_structure(df, classified_swings) # Pass classified swings
        
        # Filter recent events (last 20 candles)
        recent_events = [e for e in structure_events if e.index > len(df) - 20] # Access index attribute
        
        current_price = df['close'].iloc[-1]
        current_time = df.index[-1] # Access time from the DataFrame index
        
        for poi in pois:
            # Check if price is in POI
            in_poi = False
            if poi['type'] == 'bullish':
                if poi['low'] <= current_price <= poi['high']:
                    in_poi = True
            else: # bearish
                if poi['low'] <= current_price <= poi['high']:
                    in_poi = True
            
            if in_poi:
                # Check for ChoCH
                for event in recent_events:
                    if event.type == 'CHOCH': # Access type attribute
                        if trend == "BULLISH" and event.direction == 'bullish': # Access direction attribute
                            # Valid Long Signal
                            signals.append(Signal(
                                time=current_time,
                                type='LONG',
                                price=current_price,
                                sl=poi['low'], # SL below POI
                                tp=current_price + (current_price - poi['low']) * 3, # 3R Target
                                reason="MTF 30/1: 4H Bullish -> 30M OB -> 1M ChoCH"
                            ))
                        elif trend == "BEARISH" and event.direction == 'bearish': # Access direction attribute
                            # Valid Short Signal
                            signals.append(Signal(
                                time=current_time,
                                type='SHORT',
                                price=current_price,
                                sl=poi['high'], # SL above POI
                                tp=current_price - (poi['high'] - current_price) * 3, # 3R Target
                                reason="MTF 30/1: 4H Bearish -> 30M OB -> 1M ChoCH"
                            ))
                            
        return signals

    def get_config_schema(self) -> Dict:
        return {}
