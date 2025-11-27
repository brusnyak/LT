import backtrader as bt

class MeanReversionStrategy(bt.Strategy):
    params = (("period", 15), 
              ("qty", 0.7),                 # reduced quantity for lower risk and drawdown
              ("stop_loss", 0.001),         # fixed stop loss remains at 0.1%
              ("take_profit", 0.030),       # 3% profit target
              ("use_trailing_stop", True),
              ("trailing_stop", 0.005),     # tightened trailing stop (0.2%)
              ("min_profit_for_trail", 0.003))  # activate trailing stop after 0.3% profit
    
    def __init__(self):
        self.close_price = self.datas[0].close
        self.sma = bt.indicators.SimpleMovingAverage(self.datas[0], period=self.params.period)
        self.crossover_down = bt.indicators.CrossDown(self.close_price, self.sma)
        self.crossover_up = bt.indicators.CrossUp(self.close_price, self.sma)
        self.order = None
        self.entry_price = None
        self.max_price = None  # tracks maximum price after entry
        self.rrs = []  # store risk/reward ratios

    def next(self):
        if self.order:
            return

        if self.position and self.entry_price:
            # Update max_price after entry
            self.max_price = max(self.max_price or self.entry_price, self.close_price[0])
            
            # Activate trailing stop when price is at least min_profit_for_trail in profit
            if self.params.use_trailing_stop and self.close_price[0] >= self.entry_price * (1 + self.params.min_profit_for_trail):
                trailing_stop_level = self.max_price * (1 - self.params.trailing_stop)
                if self.close_price[0] < trailing_stop_level:
                    self.log(f"Trailing stop triggered @ {self.close_price[0]} (Level: {trailing_stop_level:.5f})")
                    self.order = self.close()
                    return

            # Exit if fixed take profit condition is met
            if self.close_price[0] >= self.entry_price * (1 + self.params.take_profit):
                self.log(f"Take profit triggered @ {self.close_price[0]}")
                self.order = self.close()
                return

            # Exit if fixed stop loss condition is met
            if self.close_price[0] < self.entry_price * (1 - self.params.stop_loss):
                self.log(f"Stop loss triggered @ {self.close_price[0]}")
                self.order = self.close()
                return

            # Exit on moving average crossover upward only if in a low profit zone
            if self.crossover_up and self.close_price[0] < self.entry_price * (1 + self.params.take_profit / 2):
                self.log(f"Exit signal (crossover up) at {self.close_price[0]} within lower profit range")
                self.order = self.close()
                return

        # Enter trade on a crossover down signal
        if not self.position and self.crossover_down:
            self.log(f"Entry signal (crossover down) at {self.close_price[0]}")
            self.max_price = None  # reset maximum price tracker
            self.order = self.buy(size=self.params.qty)

    def notify_order(self, order: bt.Order) -> None:
        if order.status == order.Completed:
            if order.isbuy():
                self.entry_price = order.executed.price
                self.max_price = self.entry_price
            self.order = None

    def notify_trade(self, trade: bt.Trade) -> None:
        if trade.isclosed and self.entry_price:
            risk = self.entry_price * self.params.stop_loss * self.params.qty
            if risk:
                rr = trade.pnl / risk
                self.rrs.append(rr)
                self.log(f"Trade closed. PnL: {trade.pnl:.4f}, Risk: {risk:.4f}, RR: {rr:.2f}")

    def stop(self) -> None:
        if self.rrs:
            avg_rr = sum(self.rrs) / len(self.rrs)
            self.log(f"Average Risk Reward Ratio over {len(self.rrs)} trades: {avg_rr:.2f}")

    def log(self, txt: str) -> None:
        dt = self.datas[0].datetime.date(0)
        t = self.datas[0].datetime.time(0)
        print(f"{dt} {t} {txt}")
