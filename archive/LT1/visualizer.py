"""
SMC Trading Visualization Tool
TradingView-style interactive chart with SMC analysis overlay
"""

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional


class SMCAnalyzer:
    """Analyzes price data for Smart Money Concepts"""
    
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        self.df.columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        self.df['timestamp'] = pd.to_datetime(self.df['timestamp'])
        
    def detect_swing_points(self, window: int = 5) -> Tuple[List[int], List[int]]:
        """Detect swing highs and lows"""
        highs = []
        lows = []
        
        for i in range(window, len(self.df) - window):
            # Swing High: current high is highest in window
            if all(self.df['high'].iloc[i] >= self.df['high'].iloc[i-j] for j in range(1, window+1)) and \
               all(self.df['high'].iloc[i] >= self.df['high'].iloc[i+j] for j in range(1, window+1)):
                highs.append(i)
            
            # Swing Low: current low is lowest in window
            if all(self.df['low'].iloc[i] <= self.df['low'].iloc[i-j] for j in range(1, window+1)) and \
               all(self.df['low'].iloc[i] <= self.df['low'].iloc[i+j] for j in range(1, window+1)):
                lows.append(i)
        
        return highs, lows
    
    def detect_order_blocks(self, swing_highs: List[int], swing_lows: List[int]) -> List[Dict]:
        """Detect Order Blocks based on swing points"""
        order_blocks = []
        
        # Bullish Order Blocks: Last down candle before bullish swing
        for low_idx in swing_lows:
            if low_idx > 5:
                # Find the last bearish candle before the swing low
                for i in range(low_idx - 1, max(0, low_idx - 10), -1):
                    if self.df['close'].iloc[i] < self.df['open'].iloc[i]:
                        ob = {
                            'type': 'bullish',
                            'start_idx': i,
                            'end_idx': low_idx,
                            'top': self.df['high'].iloc[i],
                            'bottom': self.df['low'].iloc[i],
                            'time': self.df['timestamp'].iloc[i],
                            'mitigated': False
                        }
                        order_blocks.append(ob)
                        break
        
        # Bearish Order Blocks: Last up candle before bearish swing
        for high_idx in swing_highs:
            if high_idx > 5:
                # Find the last bullish candle before the swing high
                for i in range(high_idx - 1, max(0, high_idx - 10), -1):
                    if self.df['close'].iloc[i] > self.df['open'].iloc[i]:
                        ob = {
                            'type': 'bearish',
                            'start_idx': i,
                            'end_idx': high_idx,
                            'top': self.df['high'].iloc[i],
                            'bottom': self.df['low'].iloc[i],
                            'time': self.df['timestamp'].iloc[i],
                            'mitigated': False
                        }
                        order_blocks.append(ob)
                        break
        
        return order_blocks
    
    def detect_fair_value_gaps(self) -> List[Dict]:
        """Detect Fair Value Gaps (FVG)"""
        fvgs = []
        
        for i in range(1, len(self.df) - 1):
            # Bullish FVG: gap between candle[i-1] low and candle[i+1] high
            if self.df['low'].iloc[i+1] > self.df['high'].iloc[i-1]:
                fvg = {
                    'type': 'bullish',
                    'start_idx': i-1,
                    'end_idx': i+1,
                    'top': self.df['low'].iloc[i+1],
                    'bottom': self.df['high'].iloc[i-1],
                    'time': self.df['timestamp'].iloc[i],
                    'filled': False
                }
                fvgs.append(fvg)
            
            # Bearish FVG: gap between candle[i-1] high and candle[i+1] low
            elif self.df['high'].iloc[i+1] < self.df['low'].iloc[i-1]:
                fvg = {
                    'type': 'bearish',
                    'start_idx': i-1,
                    'end_idx': i+1,
                    'top': self.df['low'].iloc[i-1],
                    'bottom': self.df['high'].iloc[i+1],
                    'time': self.df['timestamp'].iloc[i],
                    'filled': False
                }
                fvgs.append(fvg)
        
        return fvgs
    
    def detect_liquidity_zones(self, swing_highs: List[int], swing_lows: List[int]) -> List[Dict]:
        """Detect liquidity zones at swing points"""
        liquidity = []
        
        # Buy-side liquidity at swing highs
        for idx in swing_highs[-20:]:  # Last 20 swing highs
            liq = {
                'type': 'buy_side',
                'price': self.df['high'].iloc[idx],
                'time': self.df['timestamp'].iloc[idx],
                'idx': idx,
                'swept': False
            }
            liquidity.append(liq)
        
        # Sell-side liquidity at swing lows
        for idx in swing_lows[-20:]:  # Last 20 swing lows
            liq = {
                'type': 'sell_side',
                'price': self.df['low'].iloc[idx],
                'time': self.df['timestamp'].iloc[idx],
                'idx': idx,
                'swept': False
            }
            liquidity.append(liq)
        
        return liquidity
    
    def detect_market_structure(self, swing_highs: List[int], swing_lows: List[int]) -> List[Dict]:
        """Detect Break of Structure (BOS) and Change of Character (CHOCH)"""
        structure = []
        
        if len(swing_highs) < 2 or len(swing_lows) < 2:
            return structure
        
        # Analyze higher highs/lows
        for i in range(1, len(swing_highs)):
            curr_high = self.df['high'].iloc[swing_highs[i]]
            prev_high = self.df['high'].iloc[swing_highs[i-1]]
            
            if curr_high > prev_high:
                structure.append({
                    'type': 'BOS',
                    'direction': 'bullish',
                    'idx': swing_highs[i],
                    'price': curr_high,
                    'time': self.df['timestamp'].iloc[swing_highs[i]]
                })
            elif curr_high < prev_high:
                structure.append({
                    'type': 'CHOCH',
                    'direction': 'bearish',
                    'idx': swing_highs[i],
                    'price': curr_high,
                    'time': self.df['timestamp'].iloc[swing_highs[i]]
                })
        
        return structure


class TradingViewChart:
    """Creates TradingView-style interactive charts"""
    
    def __init__(self, df: pd.DataFrame, pair: str = "EURUSD", timeframe: str = "5M"):
        self.df = df.copy()
        self.df.columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        self.df['timestamp'] = pd.to_datetime(self.df['timestamp'])
        self.pair = pair
        self.timeframe = timeframe
        self.analyzer = SMCAnalyzer(self.df)
        
    def create_chart(self, show_ob: bool = True, show_fvg: bool = True, 
                    show_liquidity: bool = True, show_structure: bool = True,
                    num_candles: int = 500) -> go.Figure:
        """Create interactive chart with SMC analysis"""
        
        # Use last N candles
        df_plot = self.df.tail(num_candles).copy()
        df_plot.reset_index(drop=True, inplace=True)
        
        # Run SMC analysis
        swing_highs, swing_lows = self.analyzer.detect_swing_points(window=5)
        order_blocks = self.analyzer.detect_order_blocks(swing_highs, swing_lows)
        fvgs = self.analyzer.detect_fair_value_gaps()
        liquidity = self.analyzer.detect_liquidity_zones(swing_highs, swing_lows)
        structure = self.analyzer.detect_market_structure(swing_highs, swing_lows)
        
        # Create subplots
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            row_heights=[0.7, 0.3],
            subplot_titles=(f'{self.pair} - {self.timeframe}', 'Volume')
        )
        
        # Add candlestick chart
        fig.add_trace(
            go.Candlestick(
                x=df_plot['timestamp'],
                open=df_plot['open'],
                high=df_plot['high'],
                low=df_plot['low'],
                close=df_plot['close'],
                name='Price',
                increasing_line_color='#26a69a',
                decreasing_line_color='#ef5350'
            ),
            row=1, col=1
        )
        
        # Add volume bars
        colors = ['#26a69a' if df_plot['close'].iloc[i] >= df_plot['open'].iloc[i] 
                 else '#ef5350' for i in range(len(df_plot))]
        fig.add_trace(
            go.Bar(
                x=df_plot['timestamp'],
                y=df_plot['volume'],
                name='Volume',
                marker_color=colors,
                opacity=0.5
            ),
            row=2, col=1
        )
        
        # Filter to visible range
        start_idx = len(self.df) - num_candles
        end_idx = len(self.df)
        
        # Add Order Blocks
        if show_ob:
            for ob in order_blocks:
                if start_idx <= ob['start_idx'] < end_idx:
                    color = 'rgba(38, 166, 154, 0.2)' if ob['type'] == 'bullish' else 'rgba(239, 83, 80, 0.2)'
                    fig.add_shape(
                        type="rect",
                        x0=self.df['timestamp'].iloc[ob['start_idx']],
                        x1=self.df['timestamp'].iloc[min(ob['end_idx'] + 50, len(self.df)-1)],
                        y0=ob['bottom'],
                        y1=ob['top'],
                        fillcolor=color,
                        line=dict(color=color.replace('0.2', '0.5'), width=1),
                        row=1, col=1
                    )
                    # Add label
                    fig.add_annotation(
                        x=self.df['timestamp'].iloc[ob['start_idx']],
                        y=ob['top'] if ob['type'] == 'bearish' else ob['bottom'],
                        text=f"OB-{ob['type'][:4].upper()}",
                        showarrow=False,
                        font=dict(size=8, color='white'),
                        bgcolor=color.replace('0.2', '0.7'),
                        row=1, col=1
                    )
        
        # Add Fair Value Gaps
        if show_fvg:
            for fvg in fvgs:
                if start_idx <= fvg['start_idx'] < end_idx:
                    color = 'rgba(255, 193, 7, 0.15)' if fvg['type'] == 'bullish' else 'rgba(156, 39, 176, 0.15)'
                    fig.add_shape(
                        type="rect",
                        x0=self.df['timestamp'].iloc[fvg['start_idx']],
                        x1=self.df['timestamp'].iloc[min(fvg['end_idx'] + 30, len(self.df)-1)],
                        y0=fvg['bottom'],
                        y1=fvg['top'],
                        fillcolor=color,
                        line=dict(color=color.replace('0.15', '0.5'), width=1, dash='dot'),
                        row=1, col=1
                    )
        
        # Add Liquidity Zones
        if show_liquidity:
            for liq in liquidity:
                if start_idx <= liq['idx'] < end_idx:
                    color = '#ff6b6b' if liq['type'] == 'buy_side' else '#4ecdc4'
                    fig.add_hline(
                        y=liq['price'],
                        line_dash="dash",
                        line_color=color,
                        line_width=1,
                        annotation_text=f"LIQ-{liq['type'][:4].upper()}",
                        annotation_position="right",
                        annotation_font_size=8,
                        row=1, col=1
                    )
        
        # Add Market Structure
        if show_structure:
            for struct in structure:
                if start_idx <= struct['idx'] < end_idx:
                    color = '#00ff00' if struct['direction'] == 'bullish' else '#ff0000'
                    fig.add_annotation(
                        x=self.df['timestamp'].iloc[struct['idx']],
                        y=struct['price'],
                        text=struct['type'],
                        showarrow=True,
                        arrowhead=2,
                        arrowsize=1,
                        arrowcolor=color,
                        font=dict(size=10, color=color),
                        bgcolor='rgba(0, 0, 0, 0.5)',
                        row=1, col=1
                    )
        
        # Update layout for dark theme (TradingView style)
        fig.update_layout(
            title=f'{self.pair} - {self.timeframe} | SMC Analysis',
            template='plotly_dark',
            height=900,
            xaxis_rangeslider_visible=False,
            hovermode='x unified',
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        fig.update_xaxes(gridcolor='#2a2e39', showgrid=True)
        fig.update_yaxes(gridcolor='#2a2e39', showgrid=True)
        
        return fig


def load_forex_data(data_dir: Path, pair: str, timeframe: str) -> pd.DataFrame:
    """Load forex CSV data"""
    filename = f"{pair}_{timeframe}.csv"
    filepath = data_dir / filename
    
    if not filepath.exists():
        raise FileNotFoundError(f"Data file not found: {filepath}")
    
    df = pd.read_csv(filepath, header=None)
    df.columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
    return df


def main():
    """Main visualization function"""
    # Configuration
    DATA_DIR = Path(__file__).parent.parent / "charts" / "forex"
    PAIR = "EURUSD"
    TIMEFRAME = "M5"
    NUM_CANDLES = 1000  # Number of candles to display
    
    print(f"📊 Loading {PAIR} {TIMEFRAME} data...")
    df = load_forex_data(DATA_DIR, PAIR, TIMEFRAME)
    print(f"✅ Loaded {len(df)} candles")
    
    print(f"🔍 Creating TradingView-style chart with SMC analysis...")
    chart = TradingViewChart(df, pair=PAIR, timeframe=TIMEFRAME)
    fig = chart.create_chart(
        show_ob=True,
        show_fvg=True,
        show_liquidity=True,
        show_structure=True,
        num_candles=NUM_CANDLES
    )
    
    print(f"🚀 Opening interactive chart in browser...")
    fig.show()
    
    # Save to HTML
    output_file = Path(__file__).parent / f"chart_{PAIR}_{TIMEFRAME}.html"
    fig.write_html(str(output_file))
    print(f"💾 Chart saved to: {output_file}")


if __name__ == "__main__":
    main()
