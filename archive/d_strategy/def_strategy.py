"""
Renamed strategy file to avoid Python import issues with 'def' keyword
"""
import backtrader as bt
import numpy as np
import math

# --- Simplified Pivot Detection (Basic Version) ---
def find_pivots(data, window=5):
    """
    Find approximate pivot points (highs/lows) in a list of prices.
    Returns lists of indices for highs and lows.
    """
    highs = []
    lows = []
    for i in range(window, len(data) - window):
        if all(data[i] >= data[i - j] for j in range(1, window + 1)) and \
           all(data[i] >= data[i + j] for j in range(1, window + 1)):
            if data[i] == max(data[i - window:i + window + 1]):
                highs.append(i)
            elif data[i] == min(data[i - window:i + window + 1]):
                lows.append(i)
    return highs, lows

# --- Simplified Order Block Detection (Basic Version) ---
def detect_order_blocks(highs, lows, period=50):
    """
    Detect potential order blocks (support/resistance) based on recent highs/lows.
    Returns a list of potential order blocks (as tuples of high, low).
    """
    return []  # Placeholder for real logic.

class StructureBasedStrategy(bt.Strategy):
    params = (
        ("period", 15),
        ("qty", 0.7),  # Default qty if dynamic sizing is disabled
        ("stop_loss", 0.001),
        ("take_profit", 0.040),
        ("use_trailing_stop", True),
        ("trailing_stop", 0.005),
        ("min_profit_for_trail", 0.003),
        ("volatility_period", 20),
        ("volatility_multiplier", 1.5),
        ("use_volatility_adaptive_sl", False),
        ("enable_position_sizing", True),  # Enable dynamic sizing
        ("position_size_factor", 0.005),   # 0.5% risk of account balance per trade
        ("contract_size", 100000),         # Forex standard: 100,000 units per lot
        ("max_lot_size", 50.0),            # Maximum lot size allowed by the broker
        ("structure_window", 5),           # Window for pivot detection
        ("max_recent_blocks", 5),          # Max number of recent blocks to track
    )

    def __init__(self):
        self.close_price = self.datas[0].close
        self.sma = bt.indicators.SimpleMovingAverage(self.datas[0], period=self.params.period)
        self.crossover_down = bt.indicators.CrossDown(self.close_price, self.sma)
        self.crossover_up = bt.indicators.CrossUp(self.close_price, self.sma)
        self.atr = bt.indicators.AverageTrueRange(period=self.params.volatility_period)
        self.recent_highs = []
        self.recent_lows = []
        self.recent_order_blocks = []
        self.last_structure_time = 0
        self.last_structure_type = None  # 'BOS' or 'CHoCH'
        self.order = None
        self.entry_price = None
        self.max_price = None
        self.rrs = []
        self.active_positions = 0
        self.adaptive_sl = None

    def next(self):
        # Limit to 2 positions
        if self.active_positions >= 2:
            return

        # Skip new orders if one is already pending
        if self.order:
            return

        # --- Manage Existing Position ---
        if self.position and self.entry_price:
            self.max_price = max(self.max_price or self.entry_price, self.close_price[0])
            
            if self.params.use_volatility_adaptive_sl:
                self.adaptive_sl = self.entry_price * (1 - (self.atr[0] *
                                    self.params.volatility_multiplier / self.close_price[0]))

            if self.params.use_trailing_stop and self.close_price[0] >= self.entry_price * (1 + self.params.min_profit_for_trail):
                trailing_stop_level = self.max_price * (1 - self.params.trailing_stop)
                if self.params.use_volatility_adaptive_sl and self.adaptive_sl:
                    trailing_stop_level = min(trailing_stop_level, self.adaptive_sl)
                if self.close_price[0] < trailing_stop_level:
                    self.log(f"Trailing stop triggered @ {self.close_price[0]} (Level: {trailing_stop_level:.5f})")
                    self.order = self.close()
                    return

            if self.close_price[0] >= self.entry_price * (1 + self.params.take_profit):
                self.log(f"Take profit triggered @ {self.close_price[0]}")
                self.order = self.close()
                return

            stop_loss_level = self.entry_price * (1 - self.params.stop_loss)
            if self.params.use_volatility_adaptive_sl and self.adaptive_sl:
                stop_loss_level = min(stop_loss_level, self.adaptive_sl)
            if self.close_price[0] < stop_loss_level:
                self.log(f"Stop loss triggered @ {self.close_price[0]} (Level: {stop_loss_level:.5f})")
                self.order = self.close()
                return

            if self.crossover_up and self.close_price[0] < self.entry_price * (1 + self.params.take_profit * 0.75):
                self.log(f"Exit signal (crossover up) at {self.close_price[0]} (Early Exit)")
                self.order = self.close()
                return

        # --- New Position Entry ---
        if not self.position and self.crossover_down:
            structure_confirmed = True  # Placeholder for proper structure detection
            order_block_breakout = True  # Placeholder for order block filter

            if structure_confirmed and order_block_breakout:
                self.log(f"Entry signal (SMA CrossDown + Structure Confirmed) at {self.close_price[0]}")
                self.max_price = None
                self.active_positions += 1
                if self.params.enable_position_sizing:
                    account_balance = self.broker.getvalue()
                    risk_capital = account_balance * self.params.position_size_factor  # risk in account currency
                    # Risk per lot: if price moves against you by stop_loss percent, money lost per lot
                    risk_per_lot = self.close_price[0] * self.params.stop_loss * self.params.contract_size
                    # Compute lots so that risk per trade is limited to risk_capital:
                    size = risk_capital / risk_per_lot if risk_per_lot > 0 else self.params.qty
                    size = max(0.1, size)
                    size = min(size, self.params.max_lot_size)
                    self.order = self.buy(size=size)
                else:
                    self.order = self.buy(size=self.params.qty)
            else:
                self.log("Entry skipped: Structure or Order Block conditions not met.")

    def notify_order(self, order: bt.Order) -> None:
        if order.status == order.Completed:
            if order.isbuy():
                self.entry_price = order.executed.price
                self.max_price = self.entry_price
            elif order.issell():
                self.active_positions -= 1
            self.order = None

    def notify_trade(self, trade: bt.Trade) -> None:
        if trade.isclosed and self.entry_price:
            # When dynamic sizing is enabled, risk is computed per standard lot
            used_qty = self.params.qty if not self.params.enable_position_sizing else 1
            risk = self.entry_price * self.params.stop_loss * self.params.contract_size * used_qty
            if risk > 0:
                rr = trade.pnl / risk
                self.rrs.append(rr)
                self.log(f"Trade closed. PnL: {trade.pnl:.4f}, Risk: {risk:.4f}, RR: {rr:.2f}")
            else:
                self.log(f"Trade closed. PnL: {trade.pnl:.4f}")

    def stop(self) -> None:
        if self.rrs:
            avg_rr = sum(self.rrs) / len(self.rrs)
            self.log(f"Average Risk Reward Ratio over {len(self.rrs)} trades: {avg_rr:.2f}")

    def log(self, txt: str) -> None:
        dt = self.datas[0].datetime.date(0)
        t = self.datas[0].datetime.time(0)
        print(f"{dt} {t} {txt}")
