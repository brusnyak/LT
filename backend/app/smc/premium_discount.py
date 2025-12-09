from typing import List, Dict, Literal, Optional
import pandas as pd
from datetime import datetime
from app.models.smc import SwingPoint, PremiumDiscountZone # Import models


class PremiumDiscountDetector:
    """
    Detects Premium, Discount, and Equilibrium zones based on recent swing high and swing low.
    Also identifies Optimal Trade Entry (OTE) zones within Premium/Discount.
    """

    def __init__(self):
        pass

    def detect_zones(
        self, 
        df: pd.DataFrame, 
        swing_highs: List[SwingPoint], 
        swing_lows: List[SwingPoint]
    ) -> List[PremiumDiscountZone]:
        """
        Detects Premium, Discount, Equilibrium, and OTE zones.
        
        Args:
            df: OHLCV dataframe
            swing_highs: List of SwingPoint objects for swing highs
            swing_lows: List of SwingPoint objects for swing lows
            
        Returns:
            List of PremiumDiscountZone objects
        """
        zones: List[PremiumDiscountZone] = []

        if not swing_highs or not swing_lows:
            return zones

        # Get the most recent swing high and swing low
        latest_swing_high = max(swing_highs, key=lambda x: x.timestamp)
        latest_swing_low = max(swing_lows, key=lambda x: x.timestamp)

        # Ensure the swing high is above the swing low
        if latest_swing_high.price <= latest_swing_low.price:
            return zones # Invalid range

        # Define the overall price range
        price_range = latest_swing_high.price - latest_swing_low.price
        
        # Equilibrium (50% of the range)
        equilibrium_level = latest_swing_low.price + (price_range / 2)
        zones.append(PremiumDiscountZone(
            type='equilibrium',
            start_time=latest_swing_low.timestamp, # Use the earlier of the two swing timestamps
            end_time=df.index[-1],
            top=equilibrium_level * 1.0005, # Small buffer for visualization
            bottom=equilibrium_level * 0.9995,
            color='#878b94' # GRAY from Pine Script
        ))

        # Premium Zone (above equilibrium)
        zones.append(PremiumDiscountZone(
            type='premium',
            start_time=latest_swing_low.timestamp,
            end_time=df.index[-1],
            top=latest_swing_high.price,
            bottom=equilibrium_level,
            color='#8b5a5a' # RED from Pine Script
        ))

        # Discount Zone (below equilibrium)
        zones.append(PremiumDiscountZone(
            type='discount',
            start_time=latest_swing_low.timestamp,
            end_time=df.index[-1],
            top=equilibrium_level,
            bottom=latest_swing_low.price,
            color='#4a7c59' # GREEN from Pine Script
        ))

        # OTE Zone (Optimal Trade Entry - 0.62-0.79 Fibonacci retracement within discount)
        # This is typically from the swing high to swing low for a retracement.
        # For a bullish move, OTE is in the discount zone (0.62-0.79 retracement from high to low)
        # For a bearish move, OTE is in the premium zone (0.62-0.79 retracement from low to high)
        
        # Let's assume OTE is always within the discount zone for bullish entries,
        # and within the premium zone for bearish entries, as implied by Pine Script.
        # The Pine Script's OTE calculation is:
        # oteHigh = trailing.bottom + 0.79 * priceRange
        # oteLow = trailing.bottom + 0.62 * priceRange
        # This implies OTE is always in the discount zone relative to the overall range.
        
        ote_high = latest_swing_low.price + 0.79 * price_range
        ote_low = latest_swing_low.price + 0.62 * price_range
        
        zones.append(PremiumDiscountZone(
            type='ote',
            start_time=latest_swing_low.timestamp,
            end_time=df.index[-1],
            top=ote_high,
            bottom=ote_low,
            color='#2157f3' # BLUE from Pine Script
        ))

        return zones
