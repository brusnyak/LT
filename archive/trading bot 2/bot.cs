using System;
using System.Linq;
using System.Collections.Generic;
using cAlgo.API;
using cAlgo.API.Indicators;
using cAlgo.API.Internals;

namespace cAlgo.Robots
{
    [Robot(TimeZone = TimeZones.UTC, AccessRights = AccessRights.None)]
    public class ICTSmartMoneyBot : Robot
    {
        #region Parameters

        // Account & Risk Management Parameters
        [Parameter("Max Daily Drawdown %", Group = "Account Setup", DefaultValue = 2.0)]
        public double MaxDailyDrawdownPercent { get; set; }

        [Parameter("Max Position Size %", Group = "Account Setup", DefaultValue = 1.0)]
        public double MaxPositionSizePercent { get; set; }

        [Parameter("Max Open Positions", Group = "Account Setup", DefaultValue = 2)]
        public int MaxOpenPositions { get; set; }

        [Parameter("Daily Profit Target %", Group = "Account Setup", DefaultValue = 3.0)]
        public double DailyProfitTargetPercent { get; set; }

        [Parameter("Risk-Reward Ratio", Group = "Account Setup", DefaultValue = 2.0)]
        public double MinRiskRewardRatio { get; set; }

        // Timeframe Configuration
        [Parameter("Timeframe Preset", Group = "Timeframes", DefaultValue = "4H/30M/1M")]
        public string TimeframePreset { get; set; }

        [Parameter("Higher Timeframe", Group = "Timeframes", DefaultValue = "Hour4")]
        public string HigherTimeframeStr { get; set; }

        [Parameter("Middle Timeframe", Group = "Timeframes", DefaultValue = "Minute30")]
        public string MiddleTimeframeStr { get; set; }

        [Parameter("Lower Timeframe", Group = "Timeframes", DefaultValue = "Minute")]
        public string LowerTimeframeStr { get; set; }

        // Strategy Components
        [Parameter("Enable Order Blocks", Group = "Strategy Components", DefaultValue = true)]
        public bool EnableOrderBlocks { get; set; }

        [Parameter("Enable Fair Value Gaps", Group = "Strategy Components", DefaultValue = true)]
        public bool EnableFairValueGaps { get; set; }

        [Parameter("Enable Liquidity Sweeps", Group = "Strategy Components", DefaultValue = true)]
        public bool EnableLiquiditySweeps { get; set; }

        [Parameter("Enable Breaker Blocks", Group = "Strategy Components", DefaultValue = true)]
        public bool EnableBreakerBlocks { get; set; }

        [Parameter("Enable Market Structure", Group = "Strategy Components", DefaultValue = true)]
        public bool EnableMarketStructure { get; set; }

        [Parameter("Enable Kill Zones", Group = "Strategy Components", DefaultValue = true)]
        public bool EnableKillZones { get; set; }

        // Technical Indicators
        [Parameter("EMA Fast Period", Group = "Indicators", DefaultValue = 8)]
        public int EmaFastPeriod { get; set; }

        [Parameter("EMA Medium Period", Group = "Indicators", DefaultValue = 21)]
        public int EmaMediumPeriod { get; set; }

        [Parameter("EMA Slow Period", Group = "Indicators", DefaultValue = 50)]
        public int EmaSlowPeriod { get; set; }

        [Parameter("ATR Period", Group = "Indicators", DefaultValue = 14)]
        public int AtrPeriod { get; set; }

        [Parameter("RSI Period", Group = "Indicators", DefaultValue = 14)]
        public int RsiPeriod { get; set; }

        [Parameter("Bollinger Bands Period", Group = "Indicators", DefaultValue = 20)]
        public int BollingerBandsPeriod { get; set; }

        [Parameter("Bollinger Bands Deviation", Group = "Indicators", DefaultValue = 2.0)]
        public double BollingerBandsDeviation { get; set; }

        // Visualization Settings
        [Parameter("Show Market Structure", Group = "Visualization", DefaultValue = true)]
        public bool ShowMarketStructure { get; set; }

        [Parameter("Show Order Blocks", Group = "Visualization", DefaultValue = true)]
        public bool ShowOrderBlocks { get; set; }

        [Parameter("Show Fair Value Gaps", Group = "Visualization", DefaultValue = true)]
        public bool ShowFairValueGaps { get; set; }

        [Parameter("Max Visual Elements", Group = "Visualization", DefaultValue = 5)]
        public int MaxVisualElements { get; set; }

        // Backtesting Specific
        [Parameter("Force Trade Execution", Group = "Backtesting", DefaultValue = false)]
        public bool ForceTradeExecution { get; set; }

        [Parameter("Reduced Risk Checks", Group = "Backtesting", DefaultValue = false)]
        public bool ReducedRiskChecks { get; set; }

        #endregion

        #region Instance Variables

        // Timeframes
        private TimeFrame _higherTimeframe;
        private TimeFrame _middleTimeframe;
        private TimeFrame _lowerTimeframe;

        // Market Data
        private Bars _higherTimeframeBars;
        private Bars _middleTimeframeBars;
        private Bars _lowerTimeframeBars;

        // Technical Indicators
        private MovingAverage _emaFast;
        private MovingAverage _emaMedium;
        private MovingAverage _emaSlow;
        private AverageTrueRange _atr;
        private RelativeStrengthIndex _rsi;
        private BollingerBands _bollingerBands;

        // Risk Management
        private double _initialBalance;
        private double _dailyHighBalance;
        private double _dailyStartBalance;
        private DateTime _currentTradingDay;
        private List<Position> _todayPositions;
        private double _dailyPnL;

        // ICT Analysis Components
        private ICTAnalyzer _ictAnalyzer;
        private SMCAnalyzer _smcAnalyzer;
        private SessionAnalyzer _sessionAnalyzer;

        // Market Structure
        private List<SwingPoint> _swingHighs;
        private List<SwingPoint> _swingLows;
        private MarketStructure _marketStructure;

        // Order Blocks and Fair Value Gaps
        private List<OrderBlock> _orderBlocks;
        private List<FairValueGap> _fairValueGaps;
        private List<BreakerBlock> _breakerBlocks;
        private List<LiquidityLevel> _liquidityLevels;

        // Trading Session
        private TradingSession _currentSession;
        private bool _isInKillZone;
        private bool _isInTradingWindow;

        // Signal Tracking
        private List<TradeSignal> _activeSignals;
        private DateTime _lastSignalTime;
        private DateTime _lastBarTime = DateTime.MinValue;

        // Visualization Objects
        private Dictionary<string, ChartObject> _chartObjects;
        private int _objectCounter;
        private int _cleanupCounter;

        #endregion

        protected override void OnStart()
        {
            // Apply timeframe preset first
            ApplyTimeframePreset();

            // Initialize timeframes
            _higherTimeframe = GetTimeFrame(HigherTimeframeStr);
            _middleTimeframe = GetTimeFrame(MiddleTimeframeStr);
            _lowerTimeframe = GetTimeFrame(LowerTimeframeStr);

            // Initialize bars
            _higherTimeframeBars = MarketData.GetBars(_higherTimeframe);
            _middleTimeframeBars = MarketData.GetBars(_middleTimeframe);
            _lowerTimeframeBars = MarketData.GetBars(_lowerTimeframe);

            // Initialize technical indicators
            _emaFast = Indicators.MovingAverage(Bars.ClosePrices, EmaFastPeriod, MovingAverageType.Exponential);
            _emaMedium = Indicators.MovingAverage(Bars.ClosePrices, EmaMediumPeriod, MovingAverageType.Exponential);
            _emaSlow = Indicators.MovingAverage(Bars.ClosePrices, EmaSlowPeriod, MovingAverageType.Exponential);
            _atr = Indicators.AverageTrueRange(Bars, AtrPeriod, MovingAverageType.Simple);
            _rsi = Indicators.RelativeStrengthIndex(Bars.ClosePrices, RsiPeriod);
            _bollingerBands = Indicators.BollingerBands(Bars.ClosePrices, BollingerBandsPeriod, BollingerBandsDeviation, MovingAverageType.Simple);

            // Initialize risk management
            _initialBalance = Account.Balance;
            _dailyHighBalance = _initialBalance;
            _dailyStartBalance = _initialBalance;
            _currentTradingDay = Server.Time.Date;
            _todayPositions = new List<Position>();
            _dailyPnL = 0;

            // Initialize analyzers
            _ictAnalyzer = new ICTAnalyzer(this, Symbol);
            _smcAnalyzer = new SMCAnalyzer(this, Symbol);
            _sessionAnalyzer = new SessionAnalyzer(this);

            // Initialize data structures
            _swingHighs = new List<SwingPoint>();
            _swingLows = new List<SwingPoint>();
            _orderBlocks = new List<OrderBlock>();
            _fairValueGaps = new List<FairValueGap>();
            _breakerBlocks = new List<BreakerBlock>();
            _liquidityLevels = new List<LiquidityLevel>();
            _activeSignals = new List<TradeSignal>();
            _chartObjects = new Dictionary<string, ChartObject>();
            _objectCounter = 0;
            _cleanupCounter = 0;

            // Subscribe to events
            Positions.Opened += OnPositionsOpened;
            Positions.Closed += OnPositionsClosed;

            // Adapt for backtesting if needed
            if (IsBacktesting)
            {
                AdaptTimeframesForBacktesting();
            }

            Print("ICT Smart Money Bot initialized successfully");
            Print($"Trading {Symbol.Name} with risk parameters: Max DD: {MaxDailyDrawdownPercent}%, Max Position: {MaxPositionSizePercent}%");
            Print($"Timeframes: Higher: {_higherTimeframe}, Middle: {_middleTimeframe}, Lower: {_lowerTimeframe}");
        }

        protected override void OnTick()
        {
            // Check for new trading day
            if (Server.Time.Date != _currentTradingDay)
            {
                StartNewTradingDay();
            }

            // Update daily P&L
            UpdateDailyPnL();

            // Check risk management limits (skip in backtesting with reduced checks)
            if (!ReducedRiskChecks || !IsBacktesting)
            {
                if (!CheckRiskLimits())
                {
                    return;
                }
            }

            // Update session information
            UpdateSessionInfo();

            // Only process during market hours if not backtesting
            if (!IsBacktesting && !_isInTradingWindow && !_isInKillZone)
            {
                return;
            }

            // Check for new bars
            if (IsNewBar())
            {
                // Perform analysis on new bars
                PerformAnalysis();

                // Process signals on new bars for more consistent backtesting
                ProcessSignals();
            }
        }

        protected override void OnBar()
        {
            // Perform multi-timeframe analysis
            PerformMultiTimeframeAnalysis();

            // Generate and process signals
            ProcessSignals();

            // Update visualizations
            if (ShowMarketStructure || ShowOrderBlocks || ShowFairValueGaps)
            {
                UpdateVisualizations();
            }

            // Periodically clean up old chart objects
            _cleanupCounter++;
            if (_cleanupCounter >= 20)
            {
                CleanupOldVisualElements();
                _cleanupCounter = 0;
            }
        }

        protected override void OnStop()
        {
            // Clean up chart objects
            foreach (var obj in _chartObjects.Values)
            {
                Chart.RemoveObject(obj.Name);
            }
            _chartObjects.Clear();
        }

        private void ApplyTimeframePreset()
        {
            switch (TimeframePreset)
            {
                case "Daily/4H/1H":
                    HigherTimeframeStr = "Daily";
                    MiddleTimeframeStr = "Hour4";
                    LowerTimeframeStr = "Hour";
                    break;
                case "4H/1H/15M":
                    HigherTimeframeStr = "Hour4";
                    MiddleTimeframeStr = "Hour";
                    LowerTimeframeStr = "Minute15";
                    break;
                case "1H/30M/5M":
                    HigherTimeframeStr = "Hour";
                    MiddleTimeframeStr = "Minute30";
                    LowerTimeframeStr = "Minute5";
                    break;
                case "30M/15M/1M":
                    HigherTimeframeStr = "Minute30";
                    MiddleTimeframeStr = "Minute15";
                    LowerTimeframeStr = "Minute";
                    break;
                case "4H/30M/1M": // Your requested preset
                    HigherTimeframeStr = "Hour4";
                    MiddleTimeframeStr = "Minute30";
                    LowerTimeframeStr = "Minute";
                    break;
                case "Weekly/Daily/4H":
                    HigherTimeframeStr = "Weekly";
                    MiddleTimeframeStr = "Daily";
                    LowerTimeframeStr = "Hour4";
                    break;
                case "5M/3M/1M":
                    HigherTimeframeStr = "Minute5";
                    MiddleTimeframeStr = "Minute3";
                    LowerTimeframeStr = "Minute";
                    break;
                    // Default case uses the parameter values as is
            }
        }

        private void AdaptTimeframesForBacktesting()
        {
            // If we're in backtest mode and only have one timeframe available
            Print($"Backtest mode detected. Adapting analysis to use available data on {Bars.TimeFrame}");

            // Use the current timeframe for analysis, but maintain the hierarchy
            // This ensures the analysis logic still works even with limited data
            _higherTimeframeBars = Bars;
            _middleTimeframeBars = Bars;
            _lowerTimeframeBars = Bars;

            Print($"Using {Bars.TimeFrame} data for all timeframe analyses in backtest mode");
        }

        private bool IsNewBar()
        {
            if (Bars.OpenTimes.LastValue != _lastBarTime)
            {
                _lastBarTime = Bars.OpenTimes.LastValue;
                return true;
            }
            return false;
        }

        private void StartNewTradingDay()
        {
            _currentTradingDay = Server.Time.Date;
            _dailyStartBalance = Account.Balance;
            _dailyHighBalance = Account.Balance;
            _dailyPnL = 0;
            _todayPositions.Clear();
            Print($"Starting new trading day: {_currentTradingDay.ToShortDateString()}");
            Print($"Starting balance: {_dailyStartBalance}");
        }

        private void UpdateDailyPnL()
        {
            // Calculate current P&L from open positions
            double openPositionsPnL = Positions.Sum(p => p.NetProfit);

            // Calculate P&L from today's closed positions
            double closedPositionsPnL = 0;
            foreach (var position in _todayPositions)
            {
                if (!Positions.Contains(position)) // If position is no longer in active positions
                {
                    closedPositionsPnL += position.NetProfit;
                }
            }

            // Update daily P&L
            _dailyPnL = openPositionsPnL + closedPositionsPnL;

            // Update daily high balance
            if (Account.Balance > _dailyHighBalance)
            {
                _dailyHighBalance = Account.Balance;
            }
        }

        

        private bool CheckRiskLimits()
        {
            // Check daily drawdown limit
            double dailyDrawdown = (_dailyHighBalance - Account.Balance) / _dailyStartBalance * 100;
            if (dailyDrawdown >= MaxDailyDrawdownPercent)
            {
                // Daily drawdown limit reached
                return false;
            }

            // Check daily profit target
            double dailyProfitPercent = _dailyPnL / _dailyStartBalance * 100;
            if (dailyProfitPercent >= DailyProfitTargetPercent)
            {
                // Daily profit target reached
                return false;
            }

            // Check max open positions
            if (Positions.Count >= MaxOpenPositions)
            {
                // Max open positions reached
                return false;
            }

            return true;
        }

        private void UpdateSessionInfo()
        {
            DateTime utcTime = Server.Time.ToUniversalTime();
            int hour = utcTime.Hour;
            int minute = utcTime.Minute;

            // Determine current trading session
            if (hour >= 0 && hour < 8)
            {
                _currentSession = TradingSession.Asian;
            }
            else if (hour >= 8 && hour < 12)
            {
                _currentSession = TradingSession.London;
            }
            else if (hour >= 12 && hour < 16)
            {
                _currentSession = TradingSession.NewYork;
            }
            else
            {
                _currentSession = TradingSession.Overnight;
            }

            // Check if we're in a kill zone (London or NY open)
            _isInKillZone = (hour >= 7 && hour < 9) || (hour >= 13 && hour < 15);

            // Check if we're in a trading window (active market hours)
            _isInTradingWindow = hour >= 7 && hour < 17;
        }

        private void PerformAnalysis()
        {
            // Identify swing points
            _swingHighs = _ictAnalyzer.IdentifySwingHighs(Bars, 5);
            _swingLows = _ictAnalyzer.IdentifySwingLows(Bars, 5);

            // Analyze market structure
            _marketStructure = _ictAnalyzer.AnalyzeMarketStructure(_swingHighs, _swingLows);

            if (EnableOrderBlocks)
            {
                // Identify order blocks
                _orderBlocks = _smcAnalyzer.IdentifyOrderBlocks(Bars, 50);
            }

            if (EnableFairValueGaps)
            {
                // Identify fair value gaps
                _fairValueGaps = _smcAnalyzer.IdentifyFairValueGaps(Bars, 50);
            }

            if (EnableLiquiditySweeps)
            {
                // Identify liquidity levels
                _liquidityLevels = _ictAnalyzer.IdentifyLiquidityLevels(Bars, _swingHighs, _swingLows);
            }

            if (EnableBreakerBlocks)
            {
                // Identify breaker blocks
                _breakerBlocks = _ictAnalyzer.IdentifyBreakerBlocks(Bars, _orderBlocks);

                // Update order block status based on breaker blocks
                UpdateOrderBlockStatus(_orderBlocks, Bars, _breakerBlocks);
            }
        }


        private void PerformMultiTimeframeAnalysis()
        {
            // Perform analysis on higher timeframe
            List<SwingPoint> htfSwingHighs = _ictAnalyzer.IdentifySwingHighs(_higherTimeframeBars, 5);
            List<SwingPoint> htfSwingLows = _ictAnalyzer.IdentifySwingLows(_higherTimeframeBars, 5);
            MarketStructure htfMarketStructure = _ictAnalyzer.AnalyzeMarketStructure(htfSwingHighs, htfSwingLows);

            // Perform analysis on middle timeframe
            List<SwingPoint> mtfSwingHighs = _ictAnalyzer.IdentifySwingHighs(_middleTimeframeBars, 5);
            List<SwingPoint> mtfSwingLows = _ictAnalyzer.IdentifySwingLows(_middleTimeframeBars, 5);
            MarketStructure mtfMarketStructure = _ictAnalyzer.AnalyzeMarketStructure(mtfSwingHighs, mtfSwingLows);

            // Perform analysis on lower timeframe (already done in PerformAnalysis)

            // Identify session patterns
            Dictionary<string, PriceZone> sessionPatterns = _sessionAnalyzer.IdentifySessionPatterns(Bars);

            // Identify market shifts
            List<EntryOpportunity> marketShifts = _ictAnalyzer.IdentifyMarketShifts(Bars, _swingHighs, _swingLows);

            // Generate entry opportunities
            List<EntryOpportunity> entryOpportunities = _ictAnalyzer.IdentifyEntryOpportunities(
                Bars,
                _marketStructure,
                _orderBlocks,
                _fairValueGaps,
                _liquidityLevels,
                _breakerBlocks,
                _isInKillZone
            );

            // Filter opportunities based on multi-timeframe alignment
            FilterOpportunitiesByAlignment(entryOpportunities, htfMarketStructure, mtfMarketStructure);

            // Convert opportunities to trade signals
            ConvertOpportunitiesToSignals(entryOpportunities);
        }

        private void FilterOpportunitiesByAlignment(List<EntryOpportunity> opportunities,
                                                  MarketStructure htfStructure,
                                                  MarketStructure mtfStructure)
        {
            foreach (var opportunity in opportunities)
            {
                // Check alignment with higher timeframe
                bool htfAligned = false;
                if (opportunity.Direction == TradeDirection.Buy && htfStructure.Trend == "Uptrend")
                {
                    htfAligned = true;
                    opportunity.Strength += 15;
                }
                else if (opportunity.Direction == TradeDirection.Sell && htfStructure.Trend == "Downtrend")
                {
                    htfAligned = true;
                    opportunity.Strength += 15;
                }

                // Check alignment with middle timeframe
                bool mtfAligned = false;
                if (opportunity.Direction == TradeDirection.Buy && mtfStructure.Trend == "Uptrend")
                {
                    mtfAligned = true;
                    opportunity.Strength += 10;
                }
                else if (opportunity.Direction == TradeDirection.Sell && mtfStructure.Trend == "Downtrend")
                {
                    mtfAligned = true;
                    opportunity.Strength += 10;
                }

                // Add alignment information to opportunity
                opportunity.IsAlignedWithHigherTimeframe = htfAligned;
                opportunity.IsAlignedWithMiddleTimeframe = mtfAligned;
            }
        }


        private void ConvertOpportunitiesToSignals(List<EntryOpportunity> opportunities)
        {
            foreach (var opportunity in opportunities)
            {
                // Only consider strong opportunities
                if (opportunity.Strength < 60)
                {
                    continue;
                }

                // Check if we already have a similar signal
                bool isDuplicate = _activeSignals.Any(s =>
                    s.Direction == opportunity.Direction &&
                    Math.Abs(s.EntryPrice - opportunity.EntryPrice) < Symbol.PipSize * 5 &&
                    (Server.Time - s.CreatedTime).TotalMinutes < 60);

                if (isDuplicate)
                {
                    continue;
                }

                // Create a new trade signal
                TradeSignal signal = new TradeSignal
                {
                    Direction = opportunity.Direction,
                    EntryPrice = opportunity.EntryPrice,
                    SetupType = opportunity.SetupType,
                    Strength = opportunity.Strength,
                    CreatedTime = Server.Time,
                    IsActive = true
                };

                // Calculate stop loss and take profit
                CalculateStopLossAndTakeProfit(signal, opportunity);

                // Add to active signals
                _activeSignals.Add(signal);

                // Log the signal
                Print($"New {signal.Direction} signal generated: {signal.SetupType} at {signal.EntryPrice}, SL: {signal.StopLoss}, TP: {signal.TakeProfit}, Strength: {signal.Strength}");
            }
        }

        private void CalculateStopLossAndTakeProfit(TradeSignal signal, EntryOpportunity opportunity)
        {
            double atrValue = _atr.Result.LastValue;

            if (signal.Direction == TradeDirection.Buy)
            {
                // For buy signals, place stop loss below recent swing low or below the zone
                double stopLoss = 0;

                if (opportunity.Zone != null)
                {
                    // Use the zone's low as stop loss reference
                    stopLoss = opportunity.Zone.Low - (Symbol.PipSize * 5);
                }
                else
                {
                    // Use recent swing low
                    SwingPoint recentLow = _swingLows.OrderByDescending(s => s.Time)
                                                    .FirstOrDefault(s => s.Price < signal.EntryPrice);

                    if (recentLow != null)
                    {
                        stopLoss = recentLow.Price - (Symbol.PipSize * 5);
                    }
                    else
                    {
                        // Use ATR-based stop loss
                        stopLoss = signal.EntryPrice - (atrValue * 1.5);
                    }
                }

                // Calculate risk
                double risk = signal.EntryPrice - stopLoss;

                // Calculate take profit based on risk-reward ratio
                double takeProfit = signal.EntryPrice + (risk * MinRiskRewardRatio);

                signal.StopLoss = stopLoss;
                signal.TakeProfit = takeProfit;
            }
            else // Sell signal
            {
                // For sell signals, place stop loss above recent swing high or above the zone
                double stopLoss = 0;

                if (opportunity.Zone != null)
                {
                    // Use the zone's high as stop loss reference
                    stopLoss = opportunity.Zone.High + (Symbol.PipSize * 5);
                }
                else
                {
                    // Use recent swing high
                    SwingPoint recentHigh = _swingHighs.OrderByDescending(s => s.Time)
                                                      .FirstOrDefault(s => s.Price > signal.EntryPrice);

                    if (recentHigh != null)
                    {
                        stopLoss = recentHigh.Price + (Symbol.PipSize * 5);
                    }
                    else
                    {
                        // Use ATR-based stop loss
                        stopLoss = signal.EntryPrice + (atrValue * 1.5);
                    }
                }

                // Calculate risk
                double risk = stopLoss - signal.EntryPrice;

                // Calculate take profit based on risk-reward ratio
                double takeProfit = signal.EntryPrice - (risk * MinRiskRewardRatio);

                signal.StopLoss = stopLoss;
                signal.TakeProfit = takeProfit;
            }
        }

        private void ProcessSignals()
        {
            // Process active signals
            foreach (var signal in _activeSignals.ToList())
            {
                // Skip signals that are no longer active
                if (!signal.IsActive)
                {
                    continue;
                }

                // Check if the signal is expired
                if ((Server.Time - signal.CreatedTime).TotalHours > 4)
                {
                    signal.IsActive = false;
                    continue;
                }

                // Check if we already have a position for this signal
                bool hasPosition = Positions.Any(p =>
                    p.Label.Contains(signal.SetupType.ToString()) &&
                    Math.Abs(p.EntryPrice - signal.EntryPrice) < Symbol.PipSize * 10);

                if (hasPosition)
                {
                    signal.IsActive = false;
                    continue;
                }

                // Check if the signal can be executed
                bool canExecute = CanExecuteSignal(signal);

                if (canExecute || ForceTradeExecution)
                {
                    ExecuteTradeSignal(signal);
                    signal.IsActive = false;
                }
            }

            // Clean up inactive signals
            _activeSignals.RemoveAll(s => !s.IsActive);
        }

        private bool CanExecuteSignal(TradeSignal signal)
        {
            double currentPrice = Symbol.Bid;

            // For buy signals, check if price is near entry
            if (signal.Direction == TradeDirection.Buy)
            {
                return currentPrice <= signal.EntryPrice + (Symbol.PipSize * 5) &&
                       currentPrice >= signal.EntryPrice - (Symbol.PipSize * 5);
            }
            // For sell signals, check if price is near entry
            else
            {
                return currentPrice >= signal.EntryPrice - (Symbol.PipSize * 5) &&
                       currentPrice <= signal.EntryPrice + (Symbol.PipSize * 5);
            }
        }

        private void ExecuteTradeSignal(TradeSignal signal)
        {
            // Calculate position size
            double positionSize = CalculatePositionSize(signal);

            // Execute the trade
            TradeResult result;

            if (signal.Direction == TradeDirection.Buy)
            {
                result = ExecuteMarketOrder(TradeType.Buy, Symbol.Name, positionSize,
                                          $"{signal.SetupType}_{_objectCounter}",
                                          signal.StopLoss, signal.TakeProfit);
            }
            else
            {
                result = ExecuteMarketOrder(TradeType.Buy, Symbol.Name, positionSize,
                                          $"{signal.SetupType}_{_objectCounter}",
                                          signal.StopLoss, signal.TakeProfit);
            }

            // Log the result
            if (result.IsSuccessful)
            {
                Print($"Executed {signal.Direction} trade: {signal.SetupType} at {result.Position.EntryPrice}, SL: {signal.StopLoss}, TP: {signal.TakeProfit}, Size: {positionSize}");

                // Add to today's positions
                _todayPositions.Add(result.Position);

                // Update last signal time
                _lastSignalTime = Server.Time;
            }
            else
            {
                Print($"Failed to execute {signal.Direction} trade: {result.Error}");
            }
        }

        private double CalculatePositionSize(TradeSignal signal)
        {
            // Calculate risk amount based on account balance and risk percentage
            double riskAmount = Account.Balance * (MaxPositionSizePercent / 100.0);

            // Calculate risk in pips
            double riskInPips = 0;

            if (signal.Direction == TradeDirection.Buy)
            {
                riskInPips = Math.Abs(signal.EntryPrice - signal.StopLoss) / Symbol.PipSize;
            }
            else
            {
                riskInPips = Math.Abs(signal.StopLoss - signal.EntryPrice) / Symbol.PipSize;
            }

            // Calculate position size based on risk
            double positionSize = riskAmount / (riskInPips * Symbol.PipValue);

            // Round to standard lot size
            positionSize = Math.Floor(positionSize / Symbol.VolumeInUnitsStep) * Symbol.VolumeInUnitsStep;

            // Ensure minimum position size
            if (positionSize < Symbol.VolumeInUnitsMin)
            {
                positionSize = Symbol.VolumeInUnitsMin;
            }

            // Ensure maximum position size
            if (positionSize > Symbol.VolumeInUnitsMax)
            {
                positionSize = Symbol.VolumeInUnitsMax;
            }

            return positionSize;
        }

        private void UpdateVisualizations()
        {
            // Clear old objects if there are too many
            if (_chartObjects.Count > 100)
            {
                CleanupOldVisualElements();
            }

            // Visualize market structure
            if (ShowMarketStructure)
            {
                VisualizeMarketStructure();
            }

            // Visualize order blocks
            if (ShowOrderBlocks && EnableOrderBlocks)
            {
                VisualizeOrderBlocks();
            }

            // Visualize fair value gaps
            if (ShowFairValueGaps && EnableFairValueGaps)
            {
                VisualizeFairValueGaps();
            }
        }

        private void VisualizeMarketStructure()
        {
            // Visualize swing highs and lows
            foreach (var swingHigh in _swingHighs.OrderByDescending(s => s.Time).Take(MaxVisualElements))
            {
                string name = $"SwingHigh_{swingHigh.Time.Ticks}";

                if (!_chartObjects.ContainsKey(name))
                {
                    var obj = Chart.DrawIcon(name, ChartIconType.UpTriangle, swingHigh.Time, swingHigh.Price, Color.Green);
                    _chartObjects[name] = obj;

                    // Add text label for HH/LH
                    string structureType = swingHigh.IsHigherHigh ? "HH" : "LH";
                    string textName = $"SwingHighText_{swingHigh.Time.Ticks}";
                    var textObj = Chart.DrawText(textName, structureType, swingHigh.Time, swingHigh.Price + (10 * Symbol.PipSize), Color.Green);
                    _chartObjects[textName] = textObj;

                    // Check for BOS (Break of Structure)
                    if (swingHigh.IsBroken)
                    {
                        string bosName = $"BOS_{swingHigh.Time.Ticks}";
                        var bosObj = Chart.DrawText(bosName, "BOS Short", swingHigh.Time, swingHigh.Price + (20 * Symbol.PipSize), Color.Red);
                        _chartObjects[bosName] = bosObj;

                        // Draw a line to show the break
                        string lineName = $"BOSLine_{swingHigh.Time.Ticks}";
                        var lineObj = Chart.DrawTrendLine(lineName, swingHigh.Time, swingHigh.Price,
                                Bars.OpenTimes.LastValue, swingHigh.Price,
                                Color.Red, 1, LineStyle.Dots);
                        _chartObjects[lineName] = lineObj;
                    }
                }
            }

            foreach (var swingLow in _swingLows.OrderByDescending(s => s.Time).Take(MaxVisualElements))
            {
                string name = $"SwingLow_{swingLow.Time.Ticks}";

                if (!_chartObjects.ContainsKey(name))
                {
                    var obj = Chart.DrawIcon(name, ChartIconType.DownTriangle, swingLow.Time, swingLow.Price, Color.Red);
                    _chartObjects[name] = obj;

                    // Add text label for LL/HL
                    string structureType = swingLow.IsLowerLow ? "LL" : "HL";
                    string textName = $"SwingLowText_{swingLow.Time.Ticks}";
                    var textObj = Chart.DrawText(textName, structureType, swingLow.Time, swingLow.Price - (10 * Symbol.PipSize), Color.Red);
                    _chartObjects[textName] = textObj;

                    // Check for BOS (Break of Structure)
                    if (swingLow.IsBroken)
                    {
                        string bosName = $"BOS_{swingLow.Time.Ticks}";
                        var bosObj = Chart.DrawText(bosName, "BOS Long", swingLow.Time, swingLow.Price - (20 * Symbol.PipSize), Color.Green);
                        _chartObjects[bosName] = bosObj;

                        // Draw a line to show the break
                        string lineName = $"BOSLine_{swingLow.Time.Ticks}";
                        var lineObj = Chart.DrawTrendLine(lineName, swingLow.Time, swingLow.Price,
                                                    Bars.OpenTimes.LastValue, swingLow.Price,
                                                    Color.Green, 1, LineStyle.Dots);
                        _chartObjects[lineName] = lineObj;
                    }
                }
            }
        }

        private void VisualizeOrderBlocks()
        {
            // Visualize order blocks
            foreach (var ob in _orderBlocks.Where(o => !o.IsMitigated).OrderByDescending(o => o.StartTime).Take(MaxVisualElements))
            {
                string name = $"OB_{ob.StartTime.Ticks}";

                if (!_chartObjects.ContainsKey(name))
                {
                    Color obColor = ob.Direction == TradeDirection.Buy ? Color.FromArgb(100, 0, 128, 0) : Color.FromArgb(100, 128, 0, 0);

                    // Draw rectangle for order block
                    var obj = Chart.DrawRectangle(name, ob.StartTime, ob.High,
                                                Bars.OpenTimes.LastValue, ob.Low,
                                                obColor, 1, LineStyle.Solid);
                    _chartObjects[name] = obj;

                    // Add text label
                    string textName = $"OBText_{ob.StartTime.Ticks}";
                    string obType = ob.Direction == TradeDirection.Buy ? "Bullish OB" : "Bearish OB";
                    var textObj = Chart.DrawText(textName, obType, ob.StartTime,
                                               ob.Direction == TradeDirection.Buy ? ob.Low - (5 * Symbol.PipSize) : ob.High + (5 * Symbol.PipSize),
                                               ob.Direction == TradeDirection.Buy ? Color.Green : Color.Red);
                    _chartObjects[textName] = textObj;
                }
            }
        }

        private void VisualizeFairValueGaps()
        {
            // Visualize fair value gaps
            foreach (var fvg in _fairValueGaps.Where(f => !f.IsFilled).OrderByDescending(f => f.StartTime).Take(MaxVisualElements))
            {
                string name = $"FVG_{fvg.StartTime.Ticks}";

                if (!_chartObjects.ContainsKey(name))
                {
                    Color fvgColor = fvg.Direction == TradeDirection.Buy ? Color.FromArgb(80, 0, 128, 0) : Color.FromArgb(80, 128, 0, 0);

                    // Draw rectangle for fair value gap
                    var obj = Chart.DrawRectangle(name, fvg.StartTime, fvg.High,
                                                Bars.OpenTimes.LastValue, fvg.Low,
                                                fvgColor, 1, LineStyle.Solid);
                    _chartObjects[name] = obj;

                    // Add text label
                    string textName = $"FVGText_{fvg.StartTime.Ticks}";
                    string fvgType = fvg.Direction == TradeDirection.Buy ? "Bullish FVG" : "Bearish FVG";
                    var textObj = Chart.DrawText(textName, fvgType, fvg.StartTime,
                                               fvg.Direction == TradeDirection.Buy ? fvg.Low - (5 * Symbol.PipSize) : fvg.High + (5 * Symbol.PipSize),
                                               fvg.Direction == TradeDirection.Buy ? Color.Green : Color.Red);
                    _chartObjects[textName] = textObj;
                }
            }
        }

        public void UpdateOrderBlockStatus(List<OrderBlock> orderBlocks, Bars bars, List<BreakerBlock> breakerBlocks)
        {
            foreach (var orderBlock in orderBlocks)
            {
                // Check if the order block has been mitigated by price action
                for (int i = 0; i < bars.Count; i++)
                {
                    DateTime barTime = bars.OpenTimes[i];

                    if (barTime > orderBlock.EndTime)
                    {
                        if (orderBlock.Direction == TradeDirection.Buy)
                        {
                            // For bullish order blocks, check if price has returned to the range
                            if (bars.LowPrices[i] <= orderBlock.High &&
                                bars.HighPrices[i] >= orderBlock.Low)
                            {
                                orderBlock.IsMitigated = true;
                                break;
                            }
                        }
                        else
                        {
                            // For bearish order blocks, check if price has returned to the range
                            if (bars.HighPrices[i] >= orderBlock.Low &&
                                bars.LowPrices[i] <= orderBlock.High)
                            {
                                orderBlock.IsMitigated = true;
                                break;
                            }
                        }
                    }
                }

                // Check if the order block has been converted to a breaker block
                if (!orderBlock.IsMitigated)
                {
                    foreach (var breakerBlock in breakerBlocks)
                    {
                        if (breakerBlock.OriginalOrderBlock == orderBlock)
                        {
                            orderBlock.IsMitigated = true;
                            break;
                        }
                    }
                }
            }
        }



        private void CleanupOldVisualElements()
        {
            // Keep only the most recent visual elements
            int maxToKeep = MaxVisualElements * 3; // Keep 3 times the max visual elements per type

            // Get all keys and sort by creation time (assuming keys contain timestamps)
            var keys = _chartObjects.Keys.OrderByDescending(k => k).Skip(maxToKeep).ToList();

            foreach (var key in keys)
            {
                Chart.RemoveObject(_chartObjects[key].Name);
                _chartObjects.Remove(key);
            }
        }

        private void OnPositionsOpened(PositionOpenedEventArgs args)
        {
            // Add to today's positions
            if (args.Position.SymbolName == Symbol.Name)
            {
                _todayPositions.Add(args.Position);
                Print($"Position opened: {args.Position.Label}, {args.Position.TradeType}, Entry: {args.Position.EntryPrice}, SL: {args.Position.StopLoss}, TP: {args.Position.TakeProfit}");
            }
        }

        private void OnPositionsClosed(PositionClosedEventArgs args)
        {
            if (args.Position.SymbolName == Symbol.Name)
            {
                Print($"Position closed: {args.Position.Label}, {args.Position.TradeType}, Profit: {args.Position.GrossProfit}, Pips: {args.Position.Pips}");
            }
        }

        private TimeFrame GetTimeFrame(string timeframeStr)
        {
            switch (timeframeStr)
            {
                case "Minute":
                    return TimeFrame.Minute;
                case "Minute3":
                    return TimeFrame.Minute3;
                case "Minute5":
                    return TimeFrame.Minute5;
                case "Minute15":
                    return TimeFrame.Minute15;
                case "Minute30":
                    return TimeFrame.Minute30;
                case "Hour":
                    return TimeFrame.Hour;
                case "Hour4":
                    return TimeFrame.Hour4;
                case "Daily":
                    return TimeFrame.Daily;
                case "Weekly":
                    return TimeFrame.Weekly;
                case "Monthly":
                    return TimeFrame.Monthly;
                default:
                    return TimeFrame.Minute5;
            }
        }
    }

    #region Helper Classes

    public enum TradeDirection
    {
        Buy,
        Sell
    }

    public enum TradingSession
    {
        Asian,
        London,
        NewYork,
        Overnight
    }

    public enum SetupType
    {
        OrderBlock,
        FairValueGap,
        BreakerBlock,
        LiquiditySweep,
        KillZone,
        BOSRetrace,
        SessionOpen
    }

    public class SwingPoint
    {
        public DateTime Time { get; set; }
        public double Price { get; set; }
        public int Index { get; set; }
        public bool IsHigherHigh { get; set; }
        public bool IsLowerLow { get; set; }
        public bool IsHigherLow { get; set; }
        public bool IsLowerHigh { get; set; }
        public bool IsBroken { get; set; }
    }

    public class MarketStructure
    {
        public string Trend { get; set; }
        public List<SwingPoint> HigherHighs { get; set; }
        public List<SwingPoint> LowerLows { get; set; }
        public List<SwingPoint> HigherLows { get; set; }
        public List<SwingPoint> LowerHighs { get; set; }
        public DateTime LastChangeTime { get; set; }
    }

    public class PriceZone
    {
        public double High { get; set; }
        public double Low { get; set; }
        public DateTime StartTime { get; set; }
        public DateTime EndTime { get; set; }
        public int Strength { get; set; }
    }

    public class OrderBlock : PriceZone
    {
        public TradeDirection Direction { get; set; }
        public bool IsMitigated { get; set; }
    }

    public class FairValueGap : PriceZone
    {
        public TradeDirection Direction { get; set; }
        public bool IsFilled { get; set; }
        public double GapSize { get; set; }
    }

    public class BreakerBlock : PriceZone
    {
        public TradeDirection Direction { get; set; }
        public OrderBlock OriginalOrderBlock { get; set; }
    }

    public class LiquidityLevel : PriceZone
    {
        public bool IsSwept { get; set; }
        public TradeDirection Direction { get; set; }
    }

    public class EntryOpportunity
    {
        public TradeDirection Direction { get; set; }
        public double EntryPrice { get; set; }
        public SetupType SetupType { get; set; }
        public int Strength { get; set; }
        public PriceZone Zone { get; set; }
        public bool IsAlignedWithHigherTimeframe { get; set; }
        public bool IsAlignedWithMiddleTimeframe { get; set; }
        public DateTime Time { get; set; }
        public string Description { get; set; }
    }

    public class TradeSignal
    {
        public TradeDirection Direction { get; set; }
        public double EntryPrice { get; set; }
        public double StopLoss { get; set; }
        public double TakeProfit { get; set; }
        public SetupType SetupType { get; set; }
        public int Strength { get; set; }
        public DateTime CreatedTime { get; set; }
        public bool IsActive { get; set; }
    }

    public class ICTAnalyzer
    {
        private Robot _robot;
        private Symbol _symbol;

        public ICTAnalyzer(Robot robot, Symbol symbol)
        {
            _robot = robot;
            _symbol = symbol;
        }

        public List<SwingPoint> IdentifySwingHighs(Bars bars, int lookback)
        {
            var swingHighs = new List<SwingPoint>();

            // Start from the lookback+1 bar to ensure we have enough bars to check
            for (int i = lookback + 1; i < bars.Count - lookback; i++)
            {
                bool isSwingHigh = true;

                // Check if this bar's high is higher than all bars in the lookback period
                for (int j = 1; j <= lookback; j++)
                {
                    if (bars.HighPrices[i] <= bars.HighPrices[i - j] ||
                        bars.HighPrices[i] <= bars.HighPrices[i + j])
                    {
                        isSwingHigh = false;
                        break;
                    }
                }

                if (isSwingHigh)
                {
                    // Create a new swing high
                    var swingHigh = new SwingPoint
                    {
                        Time = bars.OpenTimes[i],
                        Price = bars.HighPrices[i],
                        Index = i
                    };

                    // Check if it's a higher high or lower high
                    if (swingHighs.Count > 0)
                    {
                        SwingPoint previousHigh = swingHighs.OrderByDescending(s => s.Time).First();
                        swingHigh.IsHigherHigh = swingHigh.Price > previousHigh.Price;
                        swingHigh.IsLowerHigh = swingHigh.Price < previousHigh.Price;
                    }
                    else
                    {
                        // First swing high
                        swingHigh.IsHigherHigh = true;
                        swingHigh.IsLowerHigh = false;
                    }

                    // Check if this swing high is broken
                    swingHigh.IsBroken = IsSwingPointBroken(bars, swingHigh, true);

                    swingHighs.Add(swingHigh);
                }
            }

            return swingHighs;
        }

        public List<SwingPoint> IdentifySwingLows(Bars bars, int lookback)
        {
            var swingLows = new List<SwingPoint>();

            // Start from the lookback+1 bar to ensure we have enough bars to check
            for (int i = lookback + 1; i < bars.Count - lookback; i++)
            {
                bool isSwingLow = true;

                // Check if this bar's low is lower than all bars in the lookback period
                for (int j = 1; j <= lookback; j++)
                {
                    if (bars.LowPrices[i] >= bars.LowPrices[i - j] ||
                        bars.LowPrices[i] >= bars.LowPrices[i + j])
                    {
                        isSwingLow = false;
                        break;
                    }
                }

                if (isSwingLow)
                {
                    // Create a new swing low
                    var swingLow = new SwingPoint
                    {
                        Time = bars.OpenTimes[i],
                        Price = bars.LowPrices[i],
                        Index = i
                    };

                    // Check if it's a lower low or higher low
                    if (swingLows.Count > 0)
                    {
                        SwingPoint previousLow = swingLows.OrderByDescending(s => s.Time).First();
                        swingLow.IsLowerLow = swingLow.Price < previousLow.Price;
                        swingLow.IsHigherLow = swingLow.Price > previousLow.Price;
                    }
                    else
                    {
                        // First swing low
                        swingLow.IsLowerLow = true;
                        swingLow.IsHigherLow = false;
                    }

                    // Check if this swing low is broken
                    swingLow.IsBroken = IsSwingPointBroken(bars, swingLow, false);

                    swingLows.Add(swingLow);
                }
            }

            return swingLows;
        }

        private bool IsSwingPointBroken(Bars bars, SwingPoint swingPoint, bool isHigh)
        {
            // Check if price has broken through this swing point
            for (int i = swingPoint.Index + 1; i < bars.Count; i++)
            {
                if (isHigh && bars.HighPrices[i] > swingPoint.Price + (_symbol.PipSize * 5))
                {
                    return true;
                }
                else if (!isHigh && bars.LowPrices[i] < swingPoint.Price - (_symbol.PipSize * 5))
                {
                    return true;
                }
            }

            return false;
        }

        public MarketStructure AnalyzeMarketStructure(List<SwingPoint> swingHighs, List<SwingPoint> swingLows)
        {
            var structure = new MarketStructure
            {
                HigherHighs = swingHighs.Where(s => s.IsHigherHigh).ToList(),
                LowerLows = swingLows.Where(s => s.IsLowerLow).ToList(),
                HigherLows = swingLows.Where(s => s.IsHigherLow).ToList(),
                LowerHighs = swingHighs.Where(s => s.IsLowerHigh).ToList()
            };

            // Determine the current trend
            if (structure.HigherHighs.Count >= 2 && structure.HigherLows.Count >= 2)
            {
                structure.Trend = "Uptrend";

                // Find the last change time
                var lastHH = structure.HigherHighs.OrderByDescending(h => h.Time).FirstOrDefault();
                var lastHL = structure.HigherLows.OrderByDescending(l => l.Time).FirstOrDefault();

                if (lastHH != null && lastHL != null)
                {
                    structure.LastChangeTime = lastHH.Time > lastHL.Time ? lastHH.Time : lastHL.Time;
                }
            }
            else if (structure.LowerLows.Count >= 2 && structure.LowerHighs.Count >= 2)
            {
                structure.Trend = "Downtrend";

                // Find the last change time
                var lastLL = structure.LowerLows.OrderByDescending(l => l.Time).FirstOrDefault();
                var lastLH = structure.LowerHighs.OrderByDescending(h => h.Time).FirstOrDefault();

                if (lastLL != null && lastLH != null)
                {
                    structure.LastChangeTime = lastLL.Time > lastLH.Time ? lastLL.Time : lastLH.Time;
                }
            }
            else
            {
                structure.Trend = "Ranging";
            }

            return structure;
        }

        public List<EntryOpportunity> IdentifyMarketShifts(Bars bars, List<SwingPoint> swingHighs, List<SwingPoint> swingLows)
        {
            var marketShifts = new List<EntryOpportunity>();

            // Check for Break of Structure (BOS)
            // A break of structure occurs when price breaks above a significant swing high (bullish BOS)
            // or below a significant swing low (bearish BOS)

            // Get recent swing points
            var recentSwingHighs = swingHighs.OrderByDescending(s => s.Time).Take(3).ToList();
            var recentSwingLows = swingLows.OrderByDescending(s => s.Time).Take(3).ToList();

            double currentPrice = bars.ClosePrices.LastValue;

            // Check for bullish BOS
            foreach (var swingHigh in recentSwingHighs)
            {
                if (swingHigh.IsBroken && !swingHigh.IsHigherHigh)
                {
                    // This is a break of a lower high - bullish BOS
                    marketShifts.Add(new EntryOpportunity
                    {
                        Direction = TradeDirection.Buy,
                        EntryPrice = currentPrice,
                        SetupType = SetupType.BOSRetrace,
                        Strength = 80,
                        Time = bars.OpenTimes.LastValue,
                        Description = "Bullish Break of Structure (BOS)"
                    });
                    break;
                }
            }

            // Check for bearish BOS
            foreach (var swingLow in recentSwingLows)
            {
                if (swingLow.IsBroken && !swingLow.IsLowerLow)
                {
                    // This is a break of a higher low - bearish BOS
                    marketShifts.Add(new EntryOpportunity
                    {
                        Direction = TradeDirection.Sell,
                        EntryPrice = currentPrice,
                        SetupType = SetupType.BOSRetrace,
                        Strength = 80,
                        Time = bars.OpenTimes.LastValue,
                        Description = "Bearish Break of Structure (BOS)"
                    });
                    break;
                }
            }

            return marketShifts;
        }

        public List<BreakerBlock> IdentifyBreakerBlocks(Bars bars, List<OrderBlock> orderBlocks)
        {
            var breakerBlocks = new List<BreakerBlock>();

            foreach (var orderBlock in orderBlocks)
            {
                // Check if price has broken through the order block


                if (orderBlock.Direction == TradeDirection.Buy)
                {
                    // For bullish order blocks, check if price has broken below
                    for (int i = 0; i < bars.Count; i++)
                    {
                        DateTime barTime = bars.OpenTimes[i];

                        

                        if (barTime > orderBlock.EndTime)
                        {
                            if (bars.LowPrices[i] < orderBlock.Low)
                            {


                                // Create a breaker block
                                breakerBlocks.Add(new BreakerBlock
                                {
                                    Direction = TradeDirection.Sell, // Opposite of original
                                    High = orderBlock.High,
                                    Low = orderBlock.Low,
                                    StartTime = barTime,
                                    EndTime = bars.OpenTimes.LastValue,
                                    Strength = 75,
                                    OriginalOrderBlock = orderBlock
                                });

                                break;
                            }
                        }
                    }
                }
                else
                {
                    // For bearish order blocks, check if price has broken above
                    for (int i = 0; i < bars.Count; i++)
                    {
                        DateTime barTime = bars.OpenTimes[i];

                        if (barTime > orderBlock.EndTime)
                        {
                            if (bars.HighPrices[i] > orderBlock.High)
                            {


                                // Create a breaker block
                                breakerBlocks.Add(new BreakerBlock
                                {
                                    Direction = TradeDirection.Buy, // Opposite of original
                                    High = orderBlock.High,
                                    Low = orderBlock.Low,
                                    StartTime = barTime,
                                    EndTime = bars.OpenTimes.LastValue,
                                    Strength = 75,
                                    OriginalOrderBlock = orderBlock
                                });

                                break;
                            }
                        }
                    }
                }
            }

            return breakerBlocks;
        }

        public List<LiquidityLevel> IdentifyLiquidityLevels(Bars bars, List<SwingPoint> swingHighs, List<SwingPoint> swingLows)
        {
            var liquidityLevels = new List<LiquidityLevel>();

            // Add swing highs as liquidity levels (sell-side liquidity)
            foreach (var swingHigh in swingHighs.OrderByDescending(s => s.Time).Take(5))
            {
                liquidityLevels.Add(new LiquidityLevel
                {
                    High = swingHigh.Price + (_symbol.PipSize * 5),
                    Low = swingHigh.Price - (_symbol.PipSize * 5),
                    StartTime = swingHigh.Time,
                    EndTime = bars.OpenTimes.LastValue,
                    IsSwept = swingHigh.IsBroken,
                    Direction = TradeDirection.Sell,
                    Strength = 70
                });
            }

            // Add swing lows as liquidity levels (buy-side liquidity)
            foreach (var swingLow in swingLows.OrderByDescending(s => s.Time).Take(5))
            {
                liquidityLevels.Add(new LiquidityLevel
                {
                    High = swingLow.Price + (_symbol.PipSize * 5),
                    Low = swingLow.Price - (_symbol.PipSize * 5),
                    StartTime = swingLow.Time,
                    EndTime = bars.OpenTimes.LastValue,
                    IsSwept = swingLow.IsBroken,
                    Direction = TradeDirection.Buy,
                    Strength = 70
                });
            }

            return liquidityLevels;
        }

        public List<EntryOpportunity> IdentifyEntryOpportunities(
            Bars bars,
            MarketStructure marketStructure,
            List<OrderBlock> orderBlocks,
            List<FairValueGap> fairValueGaps,
            List<LiquidityLevel> liquidityLevels,
            List<BreakerBlock> breakerBlocks,
            bool isInKillZone)
        {
            var opportunities = new List<EntryOpportunity>();
            double currentPrice = bars.ClosePrices.LastValue;

            // Add opportunities from order blocks
            foreach (var ob in orderBlocks.Where(o => !o.IsMitigated).OrderByDescending(o => o.Strength).Take(3))
            {
                // Check if price is near the order block
                bool isPriceNearOrderBlock = false;

                if (ob.Direction == TradeDirection.Buy)
                {
                    // For bullish order blocks, check if price is near the bottom
                    isPriceNearOrderBlock = currentPrice >= ob.Low - (_symbol.PipSize * 10) &&
                                           currentPrice <= ob.High + (_symbol.PipSize * 5);
                }
                else
                {
                    // For bearish order blocks, check if price is near the top
                    isPriceNearOrderBlock = currentPrice <= ob.High + (_symbol.PipSize * 10) &&
                                           currentPrice >= ob.Low - (_symbol.PipSize * 5);
                }

                if (isPriceNearOrderBlock)
                {
                    // Create entry opportunity
                    opportunities.Add(new EntryOpportunity
                    {
                        Direction = ob.Direction,
                        EntryPrice = ob.Direction == TradeDirection.Buy ? ob.Low : ob.High,
                        SetupType = SetupType.OrderBlock,
                        Strength = ob.Strength,
                        Zone = ob,
                        Time = bars.OpenTimes.LastValue,
                        Description = ob.Direction == TradeDirection.Buy ? "Bullish Order Block" : "Bearish Order Block"
                    });
                }
            }

            // Add opportunities from fair value gaps
            foreach (var fvg in fairValueGaps.Where(f => !f.IsFilled).OrderByDescending(f => f.Strength).Take(3))
            {
                // Check if price is near the fair value gap
                bool isPriceNearFVG = false;

                if (fvg.Direction == TradeDirection.Buy)
                {
                    // For bullish FVGs, check if price is near the bottom
                    isPriceNearFVG = currentPrice >= fvg.Low - (_symbol.PipSize * 10) &&
                                    currentPrice <= fvg.High + (_symbol.PipSize * 5);
                }
                else
                {
                    // For bearish FVGs, check if price is near the top
                    isPriceNearFVG = currentPrice <= fvg.High + (_symbol.PipSize * 10) &&
                                    currentPrice >= fvg.Low - (_symbol.PipSize * 5);
                }

                if (isPriceNearFVG)
                {
                    // Create entry opportunity
                    opportunities.Add(new EntryOpportunity
                    {
                        Direction = fvg.Direction,
                        EntryPrice = fvg.Direction == TradeDirection.Buy ? fvg.Low : fvg.High,
                        SetupType = SetupType.FairValueGap,
                        Strength = fvg.Strength,
                        Zone = fvg,
                        Time = bars.OpenTimes.LastValue,
                        Description = fvg.Direction == TradeDirection.Buy ? "Bullish Fair Value Gap" : "Bearish Fair Value Gap"
                    });
                }
            }

            // Add opportunities from breaker blocks
            foreach (var bb in breakerBlocks.OrderByDescending(b => b.Strength).Take(3))
            {
                // Check if price is near the breaker block
                bool isPriceNearBreakerBlock = false;

                if (bb.Direction == TradeDirection.Buy)
                {
                    // For bullish breaker blocks, check if price is near the bottom
                    isPriceNearBreakerBlock = currentPrice >= bb.Low - (_symbol.PipSize * 10) &&
                                             currentPrice <= bb.High + (_symbol.PipSize * 5);
                }
                else
                {
                    // For bearish breaker blocks, check if price is near the top
                    isPriceNearBreakerBlock = currentPrice <= bb.High + (_symbol.PipSize * 10) &&
                                             currentPrice >= bb.Low - (_symbol.PipSize * 5);
                }

                if (isPriceNearBreakerBlock)
                {
                    // Create entry opportunity
                    opportunities.Add(new EntryOpportunity
                    {
                        Direction = bb.Direction,
                        EntryPrice = bb.Direction == TradeDirection.Buy ? bb.Low : bb.High,
                        SetupType = SetupType.BreakerBlock,
                        Strength = bb.Strength + 10, // Breaker blocks are stronger
                        Zone = bb,
                        Time = bars.OpenTimes.LastValue,
                        Description = bb.Direction == TradeDirection.Buy ? "Bullish Breaker Block" : "Bearish Breaker Block"
                    });
                }
            }

            // Add opportunities from liquidity sweeps
            foreach (var ll in liquidityLevels.Where(l => l.IsSwept).OrderByDescending(l => l.Strength).Take(3))
            {
                // Check if price has recently swept this level (within last 5 bars)
                bool hasRecentlySweep = false;

                for (int i = bars.Count - 1; i >= Math.Max(0, bars.Count - 5); i--)
                {
                    if (ll.Direction == TradeDirection.Buy)
                    {
                        // For buy-side liquidity, check if price has swept below
                        if (bars.LowPrices[i] < ll.Low)
                        {
                            hasRecentlySweep = true;
                            break;
                        }
                    }
                    else
                    {
                        // For sell-side liquidity, check if price has swept above
                        if (bars.HighPrices[i] > ll.High)
                        {
                            hasRecentlySweep = true;
                            break;
                        }
                    }
                }

                if (hasRecentlySweep)
                {
                    // Create entry opportunity
                    opportunities.Add(new EntryOpportunity
                    {
                        Direction = ll.Direction,
                        EntryPrice = currentPrice,
                        SetupType = SetupType.LiquiditySweep,
                        Strength = ll.Strength,
                        Zone = ll,
                        Time = bars.OpenTimes.LastValue,
                        Description = ll.Direction == TradeDirection.Buy ? "Bullish Liquidity Sweep" : "Bearish Liquidity Sweep"
                    });
                }
            }

            // Add kill zone opportunities if in a kill zone
            if (isInKillZone)
            {
                // Check market structure for trend direction
                string trend = marketStructure?.Trend ?? "Ranging";

                if (trend == "Uptrend")
                {
                    // In uptrend, look for bullish opportunities in kill zone
                    opportunities.Add(new EntryOpportunity
                    {
                        Direction = TradeDirection.Buy,
                        EntryPrice = currentPrice,
                        SetupType = SetupType.KillZone,
                        Strength = 65,
                        Time = bars.OpenTimes.LastValue,
                        Description = "Bullish Kill Zone Entry (London/NY Open)"
                    });
                }
                else if (trend == "Downtrend")
                {
                    // In downtrend, look for bearish opportunities in kill zone
                    opportunities.Add(new EntryOpportunity
                    {
                        Direction = TradeDirection.Sell,
                        EntryPrice = currentPrice,
                        SetupType = SetupType.KillZone,
                        Strength = 65,
                        Time = bars.OpenTimes.LastValue,
                        Description = "Bearish Kill Zone Entry (London/NY Open)"
                    });
                }
            }

            // Filter opportunities by strength
            var validOpportunities = opportunities
                .Where(e => e.Strength >= 50) // Minimum strength threshold
                .OrderByDescending(e => e.Strength)
                .ToList();

            return validOpportunities;
        }
    }

    public class SMCAnalyzer
    {
        private Robot _robot;
        private Symbol _symbol;


        public SMCAnalyzer(Robot robot, Symbol symbol)
        {
            _robot = robot;
            _symbol = symbol;
        }

        public List<OrderBlock> IdentifyOrderBlocks(Bars bars, int maxBarsBack)
        {
            var orderBlocks = new List<OrderBlock>();

            // Limit the number of bars to analyze
            int startBar = Math.Max(0, bars.Count - maxBarsBack);

            // Identify bullish order blocks
            for (int i = startBar; i < bars.Count - 1; i++)
            {
                // Look for a bearish candle
                if (bars.ClosePrices[i] < bars.OpenPrices[i])
                {
                    // Check if followed by bullish momentum
                    bool hasBullishMomentum = false;
                    int momentumCount = 0;

                    for (int j = i + 1; j < Math.Min(i + 6, bars.Count); j++)
                    {
                        if (bars.ClosePrices[j] > bars.OpenPrices[j] &&
                            bars.ClosePrices[j] > bars.ClosePrices[j - 1])
                        {
                            momentumCount++;
                        }
                    }

                    hasBullishMomentum = momentumCount >= 2;

                    if (hasBullishMomentum)
                    {
                        // Calculate order block strength
                        int strength = CalculateOrderBlockStrength(bars, i, true);

                        // Create bullish order block
                        orderBlocks.Add(new OrderBlock
                        {
                            Direction = TradeDirection.Buy,
                            High = bars.HighPrices[i],
                            Low = bars.LowPrices[i],
                            StartTime = bars.OpenTimes[i],
                            EndTime = bars.OpenTimes[i + 1],
                            Strength = strength,
                            IsMitigated = IsOrderBlockMitigated(bars, i, true)
                        });
                    }
                }
            }

            // Identify bearish order blocks
            for (int i = startBar; i < bars.Count - 1; i++)
            {
                // Look for a bullish candle
                if (bars.ClosePrices[i] > bars.OpenPrices[i])
                {
                    // Check if followed by bearish momentum
                    bool hasBearishMomentum = false;
                    int momentumCount = 0;

                    for (int j = i + 1; j < Math.Min(i + 6, bars.Count); j++)
                    {
                        if (bars.ClosePrices[j] < bars.OpenPrices[j] &&
                            bars.ClosePrices[j] < bars.ClosePrices[j - 1])
                        {
                            momentumCount++;
                        }
                    }

                    hasBearishMomentum = momentumCount >= 2;

                    if (hasBearishMomentum)
                    {
                        // Calculate order block strength
                        int strength = CalculateOrderBlockStrength(bars, i, false);

                        // Create bearish order block
                        orderBlocks.Add(new OrderBlock
                        {
                            Direction = TradeDirection.Sell,
                            High = bars.HighPrices[i],
                            Low = bars.LowPrices[i],
                            StartTime = bars.OpenTimes[i],
                            EndTime = bars.OpenTimes[i + 1],
                            Strength = strength,
                            IsMitigated = IsOrderBlockMitigated(bars, i, false)
                        });
                    }
                }
            }

            return orderBlocks;
        }

        private int CalculateOrderBlockStrength(Bars bars, int index, bool isBullish)
        {
            int strength = 50; // Base strength

            // Factor 1: Size of the candle
            double candleSize = Math.Abs(bars.HighPrices[index] - bars.LowPrices[index]) / _symbol.PipSize;
            if (candleSize > 20 * _symbol.PipSize)
            {
                strength += 10;
            }
            else if (candleSize > 10 * _symbol.PipSize)
            {
                strength += 5;
            }

            // Factor 2: Volume (if available)
            if (bars.TickVolumes != null)
            {
                double avgVolume = 0;
                int count = 0;

                for (int i = Math.Max(0, index - 10); i < index; i++)
                {
                    avgVolume += bars.TickVolumes[i];
                    count++;
                }

                avgVolume /= count;

                if (bars.TickVolumes[index] > avgVolume * 1.5)
                {
                    strength += 10;
                }
                else if (bars.TickVolumes[index] > avgVolume * 1.2)
                {
                    strength += 5;
                }
            }

            // Factor 3: Position in the trend
            // Check previous candles for trend direction
            int upCandles = 0;
            int downCandles = 0;

            for (int i = Math.Max(0, index - 10); i < index; i++)
            {
                if (bars.ClosePrices[i] > bars.OpenPrices[i])
                {
                    upCandles++;
                }
                else if (bars.ClosePrices[i] < bars.OpenPrices[i])
                {
                    downCandles++;
                }
            }

            // If bullish OB in downtrend or bearish OB in uptrend, it's a reversal OB (stronger)
            if ((isBullish && downCandles > upCandles) || (!isBullish && upCandles > downCandles))
            {
                strength += 15;
            }

            return Math.Min(strength, 100);
        }

        private bool IsOrderBlockMitigated(Bars bars, int index, bool isBullish)
        {
            // Check if price has returned to mitigate the order block
            for (int i = index + 1; i < bars.Count; i++)
            {
                if (isBullish)
                {
                    // For bullish order blocks, check if price has returned to the range
                    if (bars.LowPrices[i] <= bars.HighPrices[index] &&
                        bars.HighPrices[i] >= bars.LowPrices[index])
                    {
                        return true;
                    }
                }
                else
                {
                    // For bearish order blocks, check if price has returned to the range
                    if (bars.HighPrices[i] >= bars.LowPrices[index] &&
                        bars.LowPrices[i] <= bars.HighPrices[index])
                    {
                        return true;
                    }
                }
            }

            return false;
        }

        public List<FairValueGap> IdentifyFairValueGaps(Bars bars, int maxBarsBack)
        {
            var fairValueGaps = new List<FairValueGap>();

            // Limit the number of bars to analyze
            int startBar = Math.Max(0, bars.Count - maxBarsBack);

            // Identify bullish fair value gaps
            for (int i = startBar; i < bars.Count - 2; i++)
            {
                // Look for a gap between candles
                if (bars.LowPrices[i + 2] > bars.HighPrices[i])
                {
                    // This is a bullish fair value gap
                    double gapSize = (bars.LowPrices[i + 2] - bars.HighPrices[i]) / _symbol.PipSize;

                    // Only consider significant gaps
                    if (gapSize >= 3 * _symbol.PipSize)
                    {
                        // Calculate strength based on gap size
                        int strength = 50 + (int)Math.Min(30, gapSize);

                        // Create bullish fair value gap
                        fairValueGaps.Add(new FairValueGap
                        {
                            Direction = TradeDirection.Buy,
                            High = bars.LowPrices[i + 2],
                            Low = bars.HighPrices[i],
                            StartTime = bars.OpenTimes[i + 1],
                            EndTime = bars.OpenTimes[i + 2],
                            Strength = strength,
                            GapSize = gapSize,
                            IsFilled = IsFairValueGapFilled(bars, i, true, bars.LowPrices[i + 2], bars.HighPrices[i])
                        });
                    }
                }
            }

            // Identify bearish fair value gaps
            for (int i = startBar; i < bars.Count - 2; i++)
            {
                // Look for a gap between candles
                if (bars.HighPrices[i + 2] < bars.LowPrices[i])
                {
                    // This is a bearish fair value gap
                    double gapSize = (bars.LowPrices[i] - bars.HighPrices[i + 2]) / _symbol.PipSize;

                    // Only consider significant gaps
                    if (gapSize >= 3 * _symbol.PipSize)
                    {
                        // Calculate strength based on gap size
                        int strength = 50 + (int)Math.Min(30, gapSize);

                        // Create bearish fair value gap
                        fairValueGaps.Add(new FairValueGap
                        {
                            Direction = TradeDirection.Sell,
                            High = bars.LowPrices[i],
                            Low = bars.HighPrices[i + 2],
                            StartTime = bars.OpenTimes[i + 1],
                            EndTime = bars.OpenTimes[i + 2],
                            Strength = strength,
                            GapSize = gapSize,
                            IsFilled = IsFairValueGapFilled(bars, i, false, bars.LowPrices[i], bars.HighPrices[i + 2])
                        });
                    }
                }
            }

            return fairValueGaps;
        }

        private bool IsFairValueGapFilled(Bars bars, int index, bool isBullish, double high, double low)
        {
            // Check if price has filled the gap
            for (int i = index + 3; i < bars.Count; i++)
            {
                if (isBullish)
                {
                    // For bullish FVGs, check if price has moved down into the gap
                    if (bars.LowPrices[i] <= high && bars.LowPrices[i] >= low)
                    {
                        return true;
                    }
                }
                else
                {
                    // For bearish FVGs, check if price has moved up into the gap
                    if (bars.HighPrices[i] >= low && bars.HighPrices[i] <= high)
                    {
                        return true;
                    }
                }
            }

            return false;
        }
    }

    public class SessionAnalyzer
    {
        private Robot _robot;

        public SessionAnalyzer(Robot robot)
        {
            _robot = robot;
        }

        public Dictionary<string, PriceZone> IdentifySessionPatterns(Bars bars)
        {
            var sessionPatterns = new Dictionary<string, PriceZone>();

            // Identify London session high/low
            PriceZone londonSession = IdentifySessionRange(bars, 8, 12);
            if (londonSession != null)
            {
                sessionPatterns["London"] = londonSession;
            }

            // Identify New York session high/low
            PriceZone nySession = IdentifySessionRange(bars, 13, 17);
            if (nySession != null)
            {
                sessionPatterns["NewYork"] = nySession;
            }

            // Identify Asian session high/low
            PriceZone asianSession = IdentifySessionRange(bars, 0, 7);
            if (asianSession != null)
            {
                sessionPatterns["Asian"] = asianSession;
            }

            return sessionPatterns;
        }

        private PriceZone IdentifySessionRange(Bars bars, int startHourUtc, int endHourUtc)
        {
            double rangeHigh = double.MinValue;
            double rangeLow = double.MaxValue;
            DateTime startTime = DateTime.MinValue;
            DateTime endTime = DateTime.MinValue;

            // Find the most recent session
            for (int i = bars.Count - 1; i >= 0; i--)
            {
                DateTime barTime = bars.OpenTimes[i].ToUniversalTime();
                int hour = barTime.Hour;

                if (hour >= startHourUtc && hour < endHourUtc)
                {
                    // This bar is in the session
                    if (startTime == DateTime.MinValue)
                    {
                        // First bar in the session
                        startTime = barTime;
                    }

                    // Update range
                    rangeHigh = Math.Max(rangeHigh, bars.HighPrices[i]);
                    rangeLow = Math.Min(rangeLow, bars.LowPrices[i]);
                    endTime = barTime;
                }
                else if (startTime != DateTime.MinValue && hour < startHourUtc)
                {
                    // We've found the complete session
                    break;
                }
            }

            if (startTime != DateTime.MinValue && endTime != DateTime.MinValue)
            {
                return new PriceZone
                {
                    High = rangeHigh,
                    Low = rangeLow,
                    StartTime = startTime,
                    EndTime = endTime,
                    Strength = 60
                };
            }

            return null;
        }

        private bool IsSessionTrending(Bars bars, int startHourUtc, int endHourUtc, bool checkUptrend)
        {
            int trendingBars = 0;
            int totalBars = 0;

            // Find bars in the specified session
            for (int i = bars.Count - 1; i >= 0; i--)
            {
                DateTime barTime = bars.OpenTimes[i].ToUniversalTime();
                int hour = barTime.Hour;

                if (hour >= startHourUtc && hour < endHourUtc)
                {
                    totalBars++;

                    if (checkUptrend)
                    {
                        // Check for uptrend
                        if (bars.ClosePrices[i] > bars.OpenPrices[i])
                        {
                            trendingBars++;
                        }
                    }
                    else
                    {
                        // Check for downtrend
                        if (bars.ClosePrices[i] < bars.OpenPrices[i])
                        {
                            trendingBars++;
                        }
                    }
                }
            }

            // Consider trending if more than 60% of bars are in the trend direction
            return totalBars > 0 && (double)trendingBars / totalBars > 0.6;
        }
    }
    #endregion
}

