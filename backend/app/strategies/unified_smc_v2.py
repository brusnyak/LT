"""
Unified SMC Strategy - Robust Implementation

This strategy integrates multiple SMC concepts using a modular, tier-based confidence system.

Core Philosophy:
- Market Structure (Swings, BOS, CHOCH) generates PRIMARY signals
- Other components (OB, FVG, Liquidity, Sessions) ADD confidence
- No hard filters - additive scoring system
- Multi-TP system for better RR

Target Performance:
- Win Rate: >= 60%
- Avg RR: >= 2.0
- Max DD: < 4%
"""

from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
from datetime import datetime, time

from app.strategies.base import BaseStrategy
from app.models.strategy import Signal
from app.models.smc import SwingPoint, MarketStructureEvent, LiquidityZone, OrderBlock, FairValueGap
from app.smc.swings import SwingDetector, get_optimal_lookback
from app.smc.market_structure import MarketStructureDetector
from app.smc.liquidity import LiquidityDetector
from app.smc.order_blocks import OrderBlockDetector
from app.smc.fvg import FVGDetector


class UnifiedSMCStrategyV2(BaseStrategy):
    """
    Unified SMC Strategy V2 - Robust, Modular Implementation
    
    Components:
    1. Market Structure (MS) - Primary signal generator
    2. Order Blocks (OB) - Entry refinement
    3. Fair Value Gaps (FVG) - TP targets
    4. Liquidity (LIQ) - TP targets + confidence boost
    5. Session Filter - Timing optimization (soft filter)
    
    Signal Generation:
    - Base: CHOCH or BOS (50 points)
    - +20: Near swing point
    - +15: Near order block
    - +10: Liquidity sweep detected
    - +10: In trading session
    - +5: FVG target available
    """
    
    # Trading sessions (UTC)
    LONDON_OPEN = (time(7, 0), time(10, 0))
    NY_OPEN = (time(13, 0), time(16, 0))
    OVERLAP = (time(12, 0), time(16, 0))
    
    def __init__(self):
        super().__init__(
            name="Unified SMC Strategy V2",
            description="Robust modular SMC strategy with tier-based confidence"
        )
        
        # Initialize detectors
        self.swing_detector = SwingDetector()
        self.market_structure_detector = MarketStructureDetector()
        self.liquidity_detector = LiquidityDetector()
        self.ob_detector = OrderBlockDetector()
        self.fvg_detector = FVGDetector()
        
        # Configuration
        self.min_rr = 1.5  # Minimum risk:reward ratio
        self.min_confidence = 60  # Minimum confidence to generate signal
        self.ob_max_age = 50  # Max candles for OB to be valid
        self.session_filter_mode = 'soft'  # 'soft' or 'hard'
        
    def analyze(self, df_multi_tf: Dict[str, pd.DataFrame], config: Optional[Dict] = None) -> Dict:
        """
        Main analysis method - orchestrates all components
        """
        signals: List[Signal] = []
        metadata: Dict = {}
        
        if config is None:
            config = {}
        
        # Get execution timeframe
        execution_tf = config.get('execution_tf', 'M5')
        if execution_tf not in df_multi_tf:
            execution_tf = list(df_multi_tf.keys())[0] if df_multi_tf else 'M5'
        
        df = df_multi_tf.get(execution_tf)
        if df is None or df.empty:
            return {"signals": [], "error": "No data provided"}
        
        # === STEP 1: Detect All Components ===
        
        # 1.1 Swings
        lookback_left, lookback_right = get_optimal_lookback(execution_tf)
        self.swing_detector.lookback_left = lookback_left
        self.swing_detector.lookback_right = lookback_right
        
        swing_data = self.swing_detector.get_swing_data(df)
        classified_swings = swing_data['classified_swings']
        
        swing_highs = [s for s in classified_swings if s.type == 'high']
        swing_lows = [s for s in classified_swings if s.type == 'low']
        
        # 1.2 Market Structure (BOS, CHOCH)
        structure_events = self.market_structure_detector.detect_structure(df, classified_swings)
        
        # 1.3 Order Blocks (needs structure events)
        order_blocks = self.ob_detector.detect_order_blocks(df, structure_events)
        # Filter by age
        current_idx = len(df) - 1
        valid_obs = [ob for ob in order_blocks 
                     if (current_idx - ob.candle_index) <= self.ob_max_age]
        
        # 1.4 Fair Value Gaps
        fvgs = self.fvg_detector.detect_fvgs(df)
        unfilled_fvgs = [fvg for fvg in fvgs if not fvg.filled]
        
        # 1.5 Liquidity Zones
        sweep_threshold = config.get('sweep_threshold', 0.5)
        eqh_eql_threshold = config.get('eqh_eql_threshold', 0.1)
        
        liquidity_zones = self.liquidity_detector.detect_liquidity_zones(
            df, swing_highs, swing_lows,
            sweep_threshold_multiplier=sweep_threshold,
            eqh_eql_threshold_multiplier=eqh_eql_threshold
        )
        
        # Store metadata
        metadata.update({
            'swing_highs': len(swing_highs),
            'swing_lows': len(swing_lows),
            'structure_events': len(structure_events),
            'order_blocks': len(valid_obs),
            'fvgs': len(unfilled_fvgs),
            'liquidity_zones': len(liquidity_zones)
        })
        
        # === STEP 2: Generate Signals ===
        
        for event in structure_events:
            # Only generate signals on CHOCH (stronger signal)
            # BOS can be added later if needed
            if event.type != 'CHOCH':
                continue
            
            signal_type = 'LONG' if event.direction == 'bullish' else 'SHORT'
            
            try:
                candle_idx = df.index.get_loc(event.timestamp)
                current_price = df['close'].iloc[candle_idx]
                current_time = event.timestamp
                
                # === TIER-BASED CONFIDENCE SCORING ===
                
                confidence = 50  # Base confidence for CHOCH
                reason_parts = [f"{event.direction.upper()} CHOCH"]
                
                # Layer 1: Swing Proximity (+20)
                near_swing, swing_distance = self._check_swing_proximity(
                    current_price, signal_type, classified_swings, event.timestamp
                )
                if near_swing:
                    confidence += 20
                    reason_parts.append("Near Swing")
                
                # Layer 2: Order Block (+15)
                near_ob, ob_zone = self._check_ob_proximity(
                    current_price, signal_type, valid_obs, candle_idx
                )
                if near_ob:
                    confidence += 15
                    reason_parts.append("OB Zone")
                
                # Layer 3: Liquidity Sweep (+10)
                liquidity_swept, swept_liq = self._check_liquidity_sweep(
                    signal_type, liquidity_zones, event.timestamp
                )
                if liquidity_swept:
                    confidence += 10
                    reason_parts.append(f"Liq Sweep ({swept_liq.subtype if swept_liq else 'unknown'})")
                
                # Layer 4: Session (+10)
                in_session, session_name = self._check_trading_session(current_time)
                if in_session:
                    confidence += 10
                    reason_parts.append(f"{session_name} Session")
                
                # Layer 5: FVG Target (+5)
                fvg_target = self._find_fvg_target(current_price, signal_type, unfilled_fvgs)
                if fvg_target:
                    confidence += 5
                    reason_parts.append("FVG Target")
                
                # === CHECK MINIMUM CONFIDENCE ===
                if confidence < self.min_confidence:
                    continue
                
                # === CALCULATE SL/TP ===
                
                # Stop Loss: Priority order
                sl_price = self._calculate_stop_loss(
                    current_price, signal_type, classified_swings, 
                    event.timestamp, ob_zone, df, candle_idx
                )
                
                # Take Profit: Multi-target system
                tp1_price, tp2_price = self._calculate_take_profits(
                    current_price, signal_type, sl_price,
                    unfilled_fvgs, liquidity_zones, classified_swings,
                    event.timestamp
                )
                
                # === VALIDATE RR ===
                
                risk = abs(current_price - sl_price)
                reward1 = abs(tp1_price - current_price)
                reward2 = abs(tp2_price - current_price)
                
                # Average RR (50% at TP1, 50% at TP2)
                avg_reward = (reward1 + reward2) / 2
                rr = avg_reward / risk if risk > 0 else 0
                
                if rr < self.min_rr:
                    continue
                
                # === CREATE SIGNAL ===
                
                signal = Signal(
                    type=signal_type,
                    price=current_price,
                    sl=sl_price,
                    tp=tp1_price,  # Primary TP
                    tp2=tp2_price,  # Secondary TP
                    time=current_time,
                    reason=" + ".join(reason_parts),
                    confidence=confidence,
                    timeframe=execution_tf,
                    rr=round(rr, 2)
                )
                
                signals.append(signal)
                
            except (KeyError, IndexError) as e:
                continue
        
        # Sort by confidence (highest first)
        signals.sort(key=lambda s: s.confidence, reverse=True)
        
        return {
            "signals": signals,
            "metadata": metadata,
            "execution_tf": execution_tf
        }
    
    def _check_swing_proximity(
        self, price: float, signal_type: str, 
        swings: List[SwingPoint], timestamp: pd.Timestamp
    ) -> Tuple[bool, float]:
        """Check if price is near a recent swing point"""
        relevant_swings = [
            s for s in swings 
            if s.timestamp < timestamp and s.type == ('low' if signal_type == 'LONG' else 'high')
        ]
        
        if not relevant_swings:
            return False, float('inf')
        
        # Get most recent swing
        recent_swing = max(relevant_swings, key=lambda s: s.timestamp)
        distance = abs(price - recent_swing.price) / price
        
        # Within 0.5% is considered "near"
        return distance < 0.005, distance
    
    def _check_ob_proximity(
        self, price: float, signal_type: str,
        obs: List[OrderBlock], current_idx: int
    ) -> Tuple[bool, Optional[OrderBlock]]:
        """Check if price is near a valid order block"""
        relevant_obs = [
            ob for ob in obs
            if ob.type == ('bullish' if signal_type == 'LONG' else 'bearish')
            and not ob.mitigated
        ]
        
        for ob in relevant_obs:
            # Check if price is within OB zone
            if signal_type == 'LONG':
                if ob.bottom <= price <= ob.top:
                    return True, ob
            else:
                if ob.bottom <= price <= ob.top:
                    return True, ob
        
        return False, None
    
    def _check_liquidity_sweep(
        self, signal_type: str, liquidity_zones: List[LiquidityZone],
        timestamp: pd.Timestamp
    ) -> Tuple[bool, Optional[LiquidityZone]]:
        """Check if liquidity was swept before this signal"""
        for lz in liquidity_zones:
            if lz.swept and lz.sweep_time and lz.sweep_time <= timestamp:
                # LONG needs sell-side sweep, SHORT needs buy-side sweep
                if signal_type == 'LONG' and lz.type == 'sell_side':
                    return True, lz
                elif signal_type == 'SHORT' and lz.type == 'buy_side':
                    return True, lz
        
        return False, None
    
    def _check_trading_session(self, timestamp: pd.Timestamp) -> Tuple[bool, str]:
        """Check if current time is in a trading session"""
        if not isinstance(timestamp, pd.Timestamp):
            return False, ""
        
        current_time = timestamp.time()
        
        # Check London Open
        if self.LONDON_OPEN[0] <= current_time <= self.LONDON_OPEN[1]:
            return True, "London"
        
        # Check NY Open
        if self.NY_OPEN[0] <= current_time <= self.NY_OPEN[1]:
            return True, "NY"
        
        # Check Overlap
        if self.OVERLAP[0] <= current_time <= self.OVERLAP[1]:
            return True, "Overlap"
        
        return False, ""
    
    def _find_fvg_target(
        self, price: float, signal_type: str, fvgs: List[FairValueGap]
    ) -> Optional[FairValueGap]:
        """Find nearest unfilled FVG as potential TP target"""
        relevant_fvgs = [
            fvg for fvg in fvgs
            if fvg.type == ('bullish' if signal_type == 'LONG' else 'bearish')
        ]
        
        if not relevant_fvgs:
            return None
        
        # Find nearest FVG in the direction of the trade
        if signal_type == 'LONG':
            targets = [fvg for fvg in relevant_fvgs if fvg.bottom > price]
            if targets:
                return min(targets, key=lambda f: f.bottom - price)
        else:
            targets = [fvg for fvg in relevant_fvgs if fvg.top < price]
            if targets:
                return min(targets, key=lambda f: price - f.top)
        
        return None
    
    def _calculate_stop_loss(
        self, price: float, signal_type: str, swings: List[SwingPoint],
        timestamp: pd.Timestamp, ob_zone: Optional[OrderBlock],
        df: pd.DataFrame, current_idx: int
    ) -> float:
        """Calculate stop loss using priority system"""
        
        # Priority 1: Recent swing point (V3 proven method)
        relevant_swings = [
            s for s in swings
            if s.timestamp < timestamp and s.type == ('low' if signal_type == 'LONG' else 'high')
        ]
        
        if relevant_swings:
            recent_swing = max(relevant_swings, key=lambda s: s.timestamp)
            # Add small buffer
            buffer = 0.0005  # 0.05%
            if signal_type == 'LONG':
                return recent_swing.price * (1 - buffer)
            else:
                return recent_swing.price * (1 + buffer)
        
        # Priority 2: OB boundary
        if ob_zone:
            if signal_type == 'LONG':
                return ob_zone.bottom * 0.9995
            else:
                return ob_zone.top * 1.0005
        
        # Priority 3: ATR-based fallback
        atr = self._calculate_atr(df, current_idx)
        if signal_type == 'LONG':
            return price - (atr * 1.5)
        else:
            return price + (atr * 1.5)
    
    def _calculate_take_profits(
        self, price: float, signal_type: str, sl_price: float,
        fvgs: List[FairValueGap], liquidity_zones: List[LiquidityZone],
        swings: List[SwingPoint], timestamp: pd.Timestamp
    ) -> Tuple[float, float]:
        """Calculate TP1 and TP2 using multi-target system"""
        
        risk = abs(price - sl_price)
        
        # TP1: Conservative (1.5-2R) - Nearest FVG or swing
        tp1_candidates = []
        
        # Check FVGs
        fvg_target = self._find_fvg_target(price, signal_type, fvgs)
        if fvg_target:
            if signal_type == 'LONG':
                tp1_candidates.append(fvg_target.bottom)
            else:
                tp1_candidates.append(fvg_target.top)
        
        # Check swings
        relevant_swings = [
            s for s in swings
            if s.timestamp < timestamp and s.type == ('high' if signal_type == 'LONG' else 'low')
        ]
        if relevant_swings:
            recent_swing = max(relevant_swings, key=lambda s: s.timestamp)
            tp1_candidates.append(recent_swing.price)
        
        # Default TP1: 1.5R
        if signal_type == 'LONG':
            tp1_default = price + (risk * 1.5)
            tp1_candidates.append(tp1_default)
            tp1_price = min([c for c in tp1_candidates if c > price], default=tp1_default)
        else:
            tp1_default = price - (risk * 1.5)
            tp1_candidates.append(tp1_default)
            tp1_price = max([c for c in tp1_candidates if c < price], default=tp1_default)
        
        # TP2: Aggressive (2.5-3R) - Next major structure or liquidity
        tp2_candidates = []
        
        # Check liquidity zones
        for lz in liquidity_zones:
            if not lz.swept:
                if signal_type == 'LONG' and lz.type == 'buy_side' and lz.price > price:
                    tp2_candidates.append(lz.price)
                elif signal_type == 'SHORT' and lz.type == 'sell_side' and lz.price < price:
                    tp2_candidates.append(lz.price)
        
        # Default TP2: 2.5R
        if signal_type == 'LONG':
            tp2_default = price + (risk * 2.5)
            tp2_candidates.append(tp2_default)
            tp2_price = min([c for c in tp2_candidates if c > tp1_price], default=tp2_default)
        else:
            tp2_default = price - (risk * 2.5)
            tp2_candidates.append(tp2_default)
            tp2_price = max([c for c in tp2_candidates if c < tp1_price], default=tp2_default)
        
        return tp1_price, tp2_price
    
    def _calculate_atr(self, df: pd.DataFrame, current_idx: int, period: int = 14) -> float:
        """Calculate Average True Range"""
        if current_idx < period:
            period = current_idx
        
        if period <= 0:
            return df['close'].iloc[current_idx] * 0.01  # 1% fallback
        
        high_low = df['high'].iloc[current_idx-period:current_idx] - df['low'].iloc[current_idx-period:current_idx]
        high_close = abs(df['high'].iloc[current_idx-period:current_idx] - df['close'].shift(1).iloc[current_idx-period:current_idx])
        low_close = abs(df['low'].iloc[current_idx-period:current_idx] - df['close'].shift(1).iloc[current_idx-period:current_idx])
        
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = tr.mean()
        
        return atr if not pd.isna(atr) else df['close'].iloc[current_idx] * 0.01
    
    def get_config_schema(self) -> Dict:
        """Return configuration schema for this strategy"""
        return {
            'min_rr': {
                'type': 'number',
                'default': 1.5,
                'min': 1.0,
                'max': 5.0,
                'description': 'Minimum risk:reward ratio for signals'
            },
            'min_confidence': {
                'type': 'number',
                'default': 60,
                'min': 0,
                'max': 100,
                'description': 'Minimum confidence score to generate signal'
            },
            'ob_max_age': {
                'type': 'number',
                'default': 50,
                'min': 10,
                'max': 200,
                'description': 'Maximum age (candles) for order blocks'
            },
            'session_filter_mode': {
                'type': 'select',
                'default': 'soft',
                'options': ['soft', 'hard', 'off'],
                'description': 'Session filter mode: soft (boost confidence), hard (only trade in sessions), off (ignore sessions)'
            },
            'sweep_threshold': {
                'type': 'number',
                'default': 0.5,
                'min': 0.1,
                'max': 2.0,
                'description': 'ATR multiplier for liquidity sweep detection'
            },
            'eqh_eql_threshold': {
                'type': 'number',
                'default': 0.1,
                'min': 0.05,
                'max': 0.5,
                'description': 'Threshold for equal highs/lows detection'
            }
        }

