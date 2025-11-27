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

        // Risk Management Parameters
        [Parameter("Max Daily Drawdown %", DefaultValue = 2.0)]
        public double MaxDailyDrawdownPercent { get; set; }

        [Parameter("Max Position Size %", DefaultValue = 1.0)]
        public double MaxPositionSizePercent { get; set; }

        [Parameter("Max Open Positions", DefaultValue = 2)]
        public int MaxOpenPositions { get; set; }

        [Parameter("Daily Profit Target %", DefaultValue = 3.0)]
        public double DailyProfitTargetPercent { get; set; }

        [Parameter("Risk-Reward Ratio", DefaultValue = 2.0)]
        public double MinRiskRewardRatio { get; set; }

        // Timeframe Parameters
        [Parameter("Higher Timeframe", DefaultValue = "Daily")]
        public string HigherTimeframeStr { get; set; }

        [Parameter("Middle Timeframe", DefaultValue = "Hour")]
        public string MiddleTimeframeStr { get; set; }

        [Parameter("Lower Timeframe", DefaultValue = "Minute5")]
        public string LowerTimeframeStr { get; set; }

        // ICT Strategy Parameters
        [Parameter("Enable Order Blocks", DefaultValue = true)]
        public bool EnableOrderBlocks { get; set; }

        [Parameter("Enable Fair Value Gaps", DefaultValue = true)]
        public bool EnableFairValueGaps { get; set; }

        [Parameter("Enable Liquidity Sweeps", DefaultValue = true)]
        public bool EnableLiquiditySweeps { get; set; }

        [Parameter("Enable Breaker Blocks", DefaultValue = true)]
        public bool EnableBreakerBlocks { get; set; }

        [Parameter("Enable Market Structure", DefaultValue = true)]
        public bool EnableMarketStructure { get; set; }

        [Parameter("Enable Kill Zones", DefaultValue = true)]
        public bool EnableKillZones { get; set; }

        // Technical Indicators
        [Parameter("EMA Fast Period", DefaultValue = 8)]
        public int EmaFastPeriod { get; set; }

        [Parameter("EMA Medium Period", DefaultValue = 21)]
        public int EmaMediumPeriod { get; set; }

        [Parameter("EMA Slow Period", DefaultValue = 50)]
        public int EmaSlowPeriod { get; set; }

        [Parameter("ATR Period", DefaultValue = 14)]
        public int AtrPeriod { get; set; }

        [Parameter("RSI Period", DefaultValue = 14)]
        public int RsiPeriod { get; set; }

        [Parameter("Bollinger Bands Period", DefaultValue = 20)]
        public int BollingerBandsPeriod { get; set; }

        [Parameter("Bollinger Bands Deviation", DefaultValue = 2.0)]
        public double BollingerBandsDeviation { get; set; }

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

        #endregion

        protected override void OnStart()
        {
            // Initialize timeframes
            _higherTimeframe = GetTimeFrame(HigherTimeframeStr);
            _middleTimeframe = GetTimeFrame(MiddleTimeframeStr);
            _lowerTimeframe = GetTimeFrame(LowerTimeframeStr);

            // Initialize bars
            _higherTimeframeBars = MarketData.GetBars(_higherTimeframe);
            _middleTimeframeBars = MarketData.GetBars(_middleTimeframe);
            _lowerTimeframeBars = MarketData.GetBars(_lowerTimeframe);

            // Initialize technical indicators
            _emaFast = Indicators.MovingAverage(_lowerTimeframeBars.ClosePrices, EmaFastPeriod, MovingAverageType.Exponential);
            _emaMedium = Indicators.MovingAverage(_lowerTimeframeBars.ClosePrices, EmaMediumPeriod, MovingAverageType.Exponential);
            _emaSlow = Indicators.MovingAverage(_lowerTimeframeBars.ClosePrices, EmaSlowPeriod, MovingAverageType.Exponential);
            _atr = Indicators.AverageTrueRange(_lowerTimeframeBars, AtrPeriod);
            _rsi = Indicators.RelativeStrengthIndex(_lowerTimeframeBars.ClosePrices, RsiPeriod);
            _bollingerBands = Indicators.BollingerBands(_lowerTimeframeBars.ClosePrices, BollingerBandsPeriod, BollingerBandsDeviation);

            // Initialize risk management
            _initialBalance = Account.Balance;
            _dailyHighBalance = _initialBalance;
            _dailyStartBalance = _initialBalance;
            _currentTradingDay = Server.Time.Date;
            _todayPositions = new List<Position>();
            _dailyPnL = 0;

            // Initialize analyzers
            _ictAnalyzer = new ICTAnalyzer(this);
            _smcAnalyzer = new SMCAnalyzer(this);
            _sessionAnalyzer = new SessionAnalyzer(this);

            // Initialize data structures
            _swingHighs = new List<SwingPoint>();
            _swingLows = new List<SwingPoint>();
            _orderBlocks = new List<OrderBlock>();
            _fairValueGaps = new List<FairValueGap>();
            _breakerBlocks = new List<BreakerBlock>();
            _liquidityLevels = new List<LiquidityLevel>();
            _activeSignals = new List<TradeSignal>();

            // Subscribe to events
            Positions.Opened += OnPositionOpened;
            Positions.Closed += OnPositionClosed;

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

            // Check risk management limits
            if (!CheckRiskLimits())
            {
                return;
            }

            // Update session information
            UpdateSessionInfo();

            // Only process during market hours
            if (!_isInTradingWindow && !_isInKillZone)
            {
                return;
            }
        }

        protected override void OnBar()
        {
            // Only analyze on new bar of the lowest timeframe
            if (Bars.TimeFrame == _lowerTimeframe)
            {
                // Perform multi-timeframe analysis
                PerformMultiTimeframeAnalysis();

                // Generate and process signals
                ProcessSignals();
            }
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
            _dailyPnL = 0;

            // Calculate unrealized P&L from open positions
            foreach (var position in Positions)
            {
                _dailyPnL += position.NetProfit;
            }

            // Update daily high balance
            if (Account.Balance + _dailyPnL > _dailyHighBalance)
            {
                _dailyHighBalance = Account.Balance + _dailyPnL;
            }
        }

        private bool CheckRiskLimits()
        {
            // Check daily drawdown
            double currentDrawdown = (_dailyHighBalance - (Account.Balance + _dailyPnL)) / _dailyHighBalance * 100;
            if (currentDrawdown >= MaxDailyDrawdownPercent)
            {
                Print($"Daily drawdown limit reached: {currentDrawdown:F2}%");
                return false;
            }

            // Check daily profit target
            double dailyProfit = ((Account.Balance + _dailyPnL) - _dailyStartBalance) / _dailyStartBalance * 100;
            if (dailyProfit >= DailyProfitTargetPercent)
            {
                Print($"Daily profit target reached: {dailyProfit:F2}%");
                return false;
            }

            // Check max open positions
            if (Positions.Count >= MaxOpenPositions)
            {
                return false;
            }

            return true;
        }

        private void UpdateSessionInfo()
        {
            // Determine current session
            _currentSession = GetCurrentSession(Server.Time);

            // Check if in kill zone
            _isInKillZone = IsInKillZone(Server.Time);

            // Check if in trading window
            _isInTradingWindow = IsInTradingWindow(Server.Time);
        }

        private void PerformMultiTimeframeAnalysis()
        {
            // Clear previous analysis data
            _swingHighs.Clear();
            _swingLows.Clear();
            _orderBlocks.Clear();
            _fairValueGaps.Clear();
            _breakerBlocks.Clear();
            _liquidityLevels.Clear();

            // Analyze higher timeframe for bias and key levels
            AnalyzeHigherTimeframe();

            // Analyze middle timeframe for zones of interest
            AnalyzeMiddleTimeframe();

            // Analyze lower timeframe for entry opportunities
            AnalyzeLowerTimeframe();
        }

        private void AnalyzeHigherTimeframe()
        {
            // Get higher timeframe data
            int barsCount = Math.Min(500, _higherTimeframeBars.Count);

            // Identify market structure
            _marketStructure = _ictAnalyzer.IdentifyMarketStructure(_higherTimeframeBars, barsCount);

            // Identify swing points
            var swingPoints = _ictAnalyzer.FindSwingPoints(_higherTimeframeBars, barsCount);
            _swingHighs.AddRange(swingPoints.SwingHighs);
            _swingLows.AddRange(swingPoints.SwingLows);

            // Identify key levels
            var keyLevels = _ictAnalyzer.IdentifyKeyLevels(_higherTimeframeBars, _swingHighs, _swingLows);

            // Identify order blocks
            if (EnableOrderBlocks)
            {
                var orderBlocks = _smcAnalyzer.IdentifyOrderBlocks(_higherTimeframeBars, barsCount);
                _orderBlocks.AddRange(orderBlocks);
            }

            // Identify fair value gaps
            if (EnableFairValueGaps)
            {
                var fairValueGaps = _smcAnalyzer.IdentifyFairValueGaps(_higherTimeframeBars, barsCount);
                _fairValueGaps.AddRange(fairValueGaps);
            }

            Print($"Higher TF Analysis: Market Structure: {_marketStructure}, Swing Highs: {_swingHighs.Count}, Swing Lows: {_swingLows.Count}");
        }

        private void AnalyzeMiddleTimeframe()
        {
            // Get middle timeframe data
            int barsCount = Math.Min(500, _middleTimeframeBars.Count);

            // Identify liquidity levels
            if (EnableLiquiditySweeps)
            {
                var liquidityLevels = _ictAnalyzer.IdentifyLiquidityLevels(_middleTimeframeBars, _swingHighs, _swingLows);
                _liquidityLevels.AddRange(liquidityLevels);
            }

            // Identify breaker blocks
            if (EnableBreakerBlocks)
            {
                var breakerBlocks = _ictAnalyzer.IdentifyBreakerBlocks(_middleTimeframeBars, _orderBlocks);
                _breakerBlocks.AddRange(breakerBlocks);
            }

            // Identify session-based patterns
            var sessionPatterns = _sessionAnalyzer.IdentifySessionPatterns(_middleTimeframeBars);

            Print($"Middle TF Analysis: Liquidity Levels: {_liquidityLevels.Count}, Breaker Blocks: {_breakerBlocks.Count}");
        }

        private void AnalyzeLowerTimeframe()
        {
            // Get lower timeframe data
            int barsCount = Math.Min(500, _lowerTimeframeBars.Count);


            // Identify market shifts (BOS, CHoCH)
            var marketShifts = _ictAnalyzer.IdentifyMarketShifts(_lowerTimeframeBars, _swingHighs, _swingLows);

            // Identify entry opportunities
            var entryOpportunities = _ictAnalyzer.IdentifyEntryOpportunities(
                _lowerTimeframeBars,
                _marketStructure,
                _orderBlocks,
                _fairValueGaps,
                _liquidityLevels,
                _breakerBlocks,
                _isInKillZone
            );

            // Check for confirmation from technical indicators
            foreach (var entry in entryOpportunities)
            {
                entry.Strength = AdjustSignalStrengthWithIndicators(entry);
            }

            Print($"Lower TF Analysis: Market Shifts: {marketShifts.Count}, Entry Opportunities: {entryOpportunities.Count}");

            // Generate signals from entry opportunities
            GenerateSignals(entryOpportunities);
        }

        private double AdjustSignalStrengthWithIndicators(EntryOpportunity entry)
        {
            double strength = entry.Strength;
            int index = _lowerTimeframeBars.Count - 1;

            // Check trend alignment with EMAs
            bool emaTrend = false;
            if (entry.Direction == TradeDirection.Buy)
            {
                emaTrend = _emaFast[index] > _emaMedium[index] && _emaMedium[index] > _emaSlow[index];
            }
            else
            {
                emaTrend = _emaFast[index] < _emaMedium[index] && _emaMedium[index] < _emaSlow[index];
            }

            if (emaTrend)
            {
                strength += 10;
            }

            // Check RSI
            if (entry.Direction == TradeDirection.Buy && _rsi[index] < 30)
            {
                strength += 10; // Oversold condition for buy
            }
            else if (entry.Direction == TradeDirection.Sell && _rsi[index] > 70)
            {
                strength += 10; // Overbought condition for sell
            }

            // Check Bollinger Bands
            if (entry.Direction == TradeDirection.Buy && _lowerTimeframeBars.ClosePrices[index] < _bollingerBands.Bottom[index])
            {
                strength += 10; // Price below lower band for buy
            }
            else if (entry.Direction == TradeDirection.Sell && _lowerTimeframeBars.ClosePrices[index] > _bollingerBands.Top[index])
            {
                strength += 10; // Price above upper band for sell
            }

            // Boost strength if in kill zone
            if (_isInKillZone)
            {
                strength += 15;
            }

            return strength;
        }

        private void GenerateSignals(List<EntryOpportunity> entryOpportunities)
        {
            // Filter opportunities by strength
            var validOpportunities = entryOpportunities
                .Where(e => e.Strength >= 50) // Minimum strength threshold
                .OrderByDescending(e => e.Strength)
                .ToList();

            foreach (var opportunity in validOpportunities)
            {
                // Calculate stop loss and take profit
                double stopLoss = CalculateStopLoss(opportunity);
                double takeProfit = CalculateTakeProfit(opportunity, stopLoss);

                // Calculate risk-reward ratio
                double riskPips = Math.Abs(opportunity.EntryPrice - stopLoss) / Symbol.PipSize;
                double rewardPips = Math.Abs(takeProfit - opportunity.EntryPrice) / Symbol.PipSize;
                double riskRewardRatio = rewardPips / riskPips;

                // Only consider trades with minimum risk-reward ratio
                if (riskRewardRatio >= MinRiskRewardRatio)
                {
                    // Create trade signal
                    var signal = new TradeSignal
                    {
                        Symbol = Symbol.Name,
                        Direction = opportunity.Direction,
                        EntryPrice = opportunity.EntryPrice,
                        StopLoss = stopLoss,
                        TakeProfit = takeProfit,
                        RiskRewardRatio = riskRewardRatio,
                        Strength = opportunity.Strength,
                        SetupType = opportunity.SetupType,
                        TimeFrame = _lowerTimeframe.ToString(),
                        CreatedTime = Server.Time
                    };

                    _activeSignals.Add(signal);

                    Print($"Generated Signal: {signal.Direction} {Symbol.Name} at {signal.EntryPrice}, SL: {signal.StopLoss}, TP: {signal.TakeProfit}, R:R: {signal.RiskRewardRatio:F2}, Strength: {signal.Strength}");
                }
            }
        }

        private double CalculateStopLoss(EntryOpportunity opportunity)
        {
            double stopLoss = 0;
            double atrValue = _atr[_lowerTimeframeBars.Count - 1];

            // Different stop loss calculation based on setup type
            switch (opportunity.SetupType)
            {
                case SetupType.OrderBlock:
                    // Place stop loss beyond the order block
                    if (opportunity.Direction == TradeDirection.Buy)
                    {
                        stopLoss = opportunity.Zone.Low - (atrValue * 0.5);
                    }
                    else
                    {
                        stopLoss = opportunity.Zone.High + (atrValue * 0.5);
                    }
                    break;

                case SetupType.FairValueGap:
                    // Place stop loss beyond the fair value gap
                    if (opportunity.Direction == TradeDirection.Buy)
                    {
                        stopLoss = opportunity.Zone.Low - (atrValue * 0.3);
                    }
                    else
                    {
                        stopLoss = opportunity.Zone.High + (atrValue * 0.3);
                    }
                    break;

                case SetupType.BreakerBlock:
                    // Place stop loss beyond the breaker block
                    if (opportunity.Direction == TradeDirection.Buy)
                    {
                        stopLoss = opportunity.Zone.Low - (atrValue * 0.5);
                    }
                    else
                    {
                        stopLoss = opportunity.Zone.High + (atrValue * 0.5);
                    }
                    break;

                case SetupType.LiquiditySweep:
                    // Place stop loss beyond the swept level
                    if (opportunity.Direction == TradeDirection.Buy)
                    {
                        stopLoss = opportunity.Zone.Low - (atrValue * 0.7);
                    }
                    else
                    {
                        stopLoss = opportunity.Zone.High + (atrValue * 0.7);
                    }
                    break;

                default:
                    // Default to ATR-based stop loss
                    if (opportunity.Direction == TradeDirection.Buy)
                    {
                        stopLoss = opportunity.EntryPrice - (atrValue * 1.5);
                    }
                    else
                    {
                        stopLoss = opportunity.EntryPrice + (atrValue * 1.5);
                    }
                    break;
            }

            return stopLoss;
        }

        private double CalculateTakeProfit(EntryOpportunity opportunity, double stopLoss)
        {
            double takeProfit = 0;
            double riskAmount = Math.Abs(opportunity.EntryPrice - stopLoss);

            // Find optimal take profit based on key levels
            if (opportunity.Direction == TradeDirection.Buy)
            {
                // Find the nearest resistance level above entry
                double nearestResistance = FindNearestKeyLevel(opportunity.EntryPrice, true);

                // Ensure minimum risk-reward ratio
                double minTakeProfit = opportunity.EntryPrice + (riskAmount * MinRiskRewardRatio);

                // Use the further of the two
                takeProfit = Math.Max(nearestResistance, minTakeProfit);
            }
            else
            {
                // Find the nearest support level below entry
                double nearestSupport = FindNearestKeyLevel(opportunity.EntryPrice, false);

                // Ensure minimum risk-reward ratio
                double minTakeProfit = opportunity.EntryPrice - (riskAmount * MinRiskRewardRatio);

                // Use the further of the two
                takeProfit = Math.Min(nearestSupport, minTakeProfit);
            }

            return takeProfit;
        }

        private double FindNearestKeyLevel(double price, bool above)
        {
            double nearestLevel = above ? double.MaxValue : 0;

            // Check swing points
            foreach (var swing in above ? _swingHighs : _swingLows)
            {
                if (above && swing.Price > price && swing.Price < nearestLevel)
                {
                    nearestLevel = swing.Price;
                }
                else if (!above && swing.Price < price && swing.Price > nearestLevel)
                {
                    nearestLevel = swing.Price;
                }
            }

            // If no level found, use ATR-based level
            if (nearestLevel == (above ? double.MaxValue : 0))
            {
                double atrValue = _atr[_lowerTimeframeBars.Count - 1];
                nearestLevel = above ? price + (atrValue * 3) : price - (atrValue * 3);
            }

            return nearestLevel;
        }

        private void ProcessSignals()
        {
            // Process active signals
            foreach (var signal in _activeSignals.ToList())
            {
                // Check if signal is expired
                if (Server.Time.Subtract(signal.CreatedTime).TotalHours > 24)
                {
                    _activeSignals.Remove(signal);
                    continue;
                }

                // Check if we should execute the signal
                if (ShouldExecuteSignal(signal))
                {
                    ExecuteSignal(signal);
                    _activeSignals.Remove(signal);
                }
            }
        }

        private bool ShouldExecuteSignal(TradeSignal signal)
        {
            // Check if price is near entry level
            double currentPrice = signal.Direction == TradeDirection.Buy ? Symbol.Ask : Symbol.Bid;
            double entryThreshold = Symbol.PipSize * 5; // 5 pips threshold

            if (Math.Abs(currentPrice - signal.EntryPrice) <= entryThreshold)
            {
                // Check if we have any open positions for this symbol
                if (Positions.Find(Symbol.Name).Count > 0)
                {
                    return false;
                }

                // Check if we're in a kill zone (if enabled)
                if (EnableKillZones && !_isInKillZone && !_isInTradingWindow)
                {
                    return false;
                }

                // Check time between signals
                if (Server.Time.Subtract(_lastSignalTime).TotalMinutes < 30)
                {
                    return false;
                }

                return true;
            }

            return false;
        }

        private void ExecuteSignal(TradeSignal signal)
        {
            // Calculate position size
            double positionSize = CalculatePositionSize(signal.EntryPrice, signal.StopLoss);

            // Execute the trade
            TradeResult result;
            if (signal.Direction == TradeDirection.Buy)
            {
                result = ExecuteMarketOrder(TradeType.Buy, Symbol, positionSize, "ICT_" + signal.SetupType, signal.StopLoss, signal.TakeProfit);
            }
            else
            {
                result = ExecuteMarketOrder(TradeType.Sell, Symbol, positionSize, "ICT_" + signal.SetupType, signal.StopLoss, signal.TakeProfit);
            }

            if (result.IsSuccessful)
            {
                Print($"Executed {signal.Direction} trade for {Symbol.Name} at {result.Position.EntryPrice}, SL: {result.Position.StopLoss}, TP: {result.Position.TakeProfit}, Size: {positionSize}");
                _lastSignalTime = Server.Time;
            }
            else
            {
                Print($"Failed to execute trade: {result.Error}");
            }
        }

        private double CalculatePositionSize(double entryPrice, double stopLoss)
        {
            // Calculate risk amount
            double accountRiskPercent = MaxPositionSizePercent;
            double accountRiskAmount = Account.Balance * (accountRiskPercent / 100);

            // Calculate pip risk
            double pipRisk = Math.Abs(entryPrice - stopLoss) / Symbol.PipSize;

            // Calculate position size
            double positionSize = accountRiskAmount / (pipRisk * Symbol.PipValue);

            // Round to standard lot size
            positionSize = Math.Floor(positionSize / Symbol.VolumeInUnitsStep) * Symbol.VolumeInUnitsStep;

            // Ensure minimum and maximum position size
            positionSize = Math.Max(positionSize, Symbol.VolumeInUnitsMin);
            positionSize = Math.Min(positionSize, Symbol.VolumeInUnitsMax);

            return positionSize;
        }

        private void OnPositionOpened(Position position)
        {
            if (position.SymbolName == Symbol.Name)
            {
                _todayPositions.Add(position);
                Print($"Position opened: {position.Label}, Entry: {position.EntryPrice}, SL: {position.StopLoss}, TP: {position.TakeProfit}");
            }
        }

        private void OnPositionClosed(Position position)
        {
            if (position.SymbolName == Symbol.Name)
            {
                Print($"Position closed: {position.Label}, Profit: {position.NetProfit}, Pips: {position.Pips}");

                // Update daily P&L
                UpdateDailyPnL();
            }
        }

        private TimeFrame GetTimeFrame(string timeframeStr)
        {
            switch (timeframeStr.ToLower())
            {
                case "minute1":
                case "m1":
                    return TimeFrame.Minute;
                case "minute5":
                case "m5":
                    return TimeFrame.Minute5;
                case "minute15":
                case "m15":
                    return TimeFrame.Minute15;
                case "minute30":
                case "m30":
                    return TimeFrame.Minute30;
                case "hour":
                case "h1":
                    return TimeFrame.Hour;
                case "hour4":
                case "h4":
                    return TimeFrame.Hour4;
                case "daily":
                case "d1":
                    return TimeFrame.Daily;
                case "weekly":
                case "w1":
                    return TimeFrame.Weekly;
                default:
                    return TimeFrame.Hour;
            }
        }

        private TradingSession GetCurrentSession(DateTime time)
        {
            // Convert to UTC
            DateTime utcTime = time.ToUniversalTime();
            int hour = utcTime.Hour;

            // Define session times in UTC
            if (hour >= 0 && hour < 7)
            {
                return TradingSession.Asian;
            }
            else if (hour >= 7 && hour < 13)
            {
                return TradingSession.London;
            }
            else if (hour >= 13 && hour < 17)
            {
                return TradingSession.LondonNewYork;
            }
            else if (hour >= 17 && hour < 22)
            {
                return TradingSession.NewYork;
            }
            else
            {
                return TradingSession.Sydney;
            }
        }

        private bool IsInKillZone(DateTime time)
        {
            if (!EnableKillZones)
                return false;

            // Convert to UTC
            DateTime utcTime = time.ToUniversalTime();
            int hour = utcTime.Hour;
            int minute = utcTime.Minute;

            // London open (7:00-9:00 UTC)
            if (hour >= 7 && hour < 9)
                return true;

            // New York open (13:00-15:00 UTC)
            if (hour >= 13 && hour < 15)
                return true;

            // London close / NY midday (15:00-17:00 UTC)
            if (hour >= 15 && hour < 17)
                return true;

            return false;
        }

        private bool IsInTradingWindow(DateTime time)
        {
            // Convert to UTC
            DateTime utcTime = time.ToUniversalTime();
            int hour = utcTime.Hour;

            // Main trading hours (London and NY sessions)
            if (hour >= 7 && hour < 21)
                return true;

            return false;
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
        LondonNewYork,
        Sydney
    }

    public enum MarketStructure
    {
        Uptrend,
        Downtrend,
        Consolidation,
        Unknown
    }

    public enum SetupType
    {
        OrderBlock,
        FairValueGap,
        BreakerBlock,
        LiquiditySweep,
        BreakOfStructure,
        ChangeOfCharacter,
        KillZone
    }

    public class SwingPoint
    {
        public int Index { get; set; }
        public double Price { get; set; }
        public DateTime Time { get; set; }
        public bool IsHigh { get; set; }
        public int Strength { get; set; }
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
        public bool IsTested { get; set; }
    }

    public class LiquidityLevel : PriceZone
    {
        public TradeDirection Direction { get; set; }
        public bool IsSwept { get; set; }
    }

    public class EntryOpportunity
    {
        public TradeDirection Direction { get; set; }
        public double EntryPrice { get; set; }
        public PriceZone Zone { get; set; }
        public SetupType SetupType { get; set; }
        public double Strength { get; set; }
    }

    public class TradeSignal
    {
        public string Symbol { get; set; }
        public TradeDirection Direction { get; set; }
        public double EntryPrice { get; set; }
        public double StopLoss { get; set; }
        public double TakeProfit { get; set; }
        public double RiskRewardRatio { get; set; }
        public double Strength { get; set; }
        public SetupType SetupType { get; set; }
        public string TimeFrame { get; set; }
        public DateTime CreatedTime { get; set; }
    }

    #endregion

    #region Analyzer Classes

    public class ICTAnalyzer
    {
        private Robot _robot;

        public ICTAnalyzer(Robot robot)
        {
            _robot = robot;
        }

        public MarketStructure IdentifyMarketStructure(Bars bars, int barsCount)
        {
            // Get recent bars
            int lookback = Math.Min(barsCount, 100);

            // Calculate EMAs for trend determination
            var ema50 = _robot.Indicators.MovingAverage(bars.ClosePrices, 50, MovingAverageType.Exponential);
            var ema200 = _robot.Indicators.MovingAverage(bars.ClosePrices, 200, MovingAverageType.Exponential);

            int bullishBars = 0;
            int bearishBars = 0;

            // Count bullish and bearish bars
            for (int i = bars.Count - lookback; i < bars.Count; i++)
            {
                if (bars.ClosePrices[i] > bars.OpenPrices[i])
                {
                    bullishBars++;
                }
                else if (bars.ClosePrices[i] < bars.OpenPrices[i])
                {
                    bearishBars++;
                }
            }

            // Check if price is above/below EMAs
            bool priceAboveEma50 = bars.ClosePrices[bars.Count - 1] > ema50[ema50.Count - 1];
            bool priceAboveEma200 = bars.ClosePrices[bars.Count - 1] > ema200[ema200.Count - 1];
            bool ema50AboveEma200 = ema50[ema50.Count - 1] > ema200[ema200.Count - 1];

            // Determine market structure
            if (priceAboveEma50 && priceAboveEma200 && ema50AboveEma200 && bullishBars > bearishBars)
            {
                return MarketStructure.Uptrend;
            }
            else if (!priceAboveEma50 && !priceAboveEma200 && !ema50AboveEma200 && bearishBars > bullishBars)
            {
                return MarketStructure.Downtrend;
            }
            else if (Math.Abs(bullishBars - bearishBars) < lookback * 0.2)
            {
                return MarketStructure.Consolidation;
            }
            else
            {
                return MarketStructure.Unknown;
            }
        }

        public (List<SwingPoint> SwingHighs, List<SwingPoint> SwingLows) FindSwingPoints(Bars bars, int barsCount)
        {
            var swingHighs = new List<SwingPoint>();
            var swingLows = new List<SwingPoint>();

            // Minimum number of bars to look left and right
            int lookAround = 3;

            // Start from the oldest bar we want to analyze
            for (int i = bars.Count - barsCount + lookAround; i < bars.Count - lookAround; i++)
            {
                // Check for swing high
                bool isSwingHigh = true;
                for (int j = 1; j <= lookAround; j++)
                {
                    if (bars.HighPrices[i] <= bars.HighPrices[i - j] || bars.HighPrices[i] <= bars.HighPrices[i + j])
                    {
                        isSwingHigh = false;
                        break;
                    }
                }

                if (isSwingHigh)
                {
                    swingHighs.Add(new SwingPoint
                    {
                        Index = i,
                        Price = bars.HighPrices[i],
                        Time = bars.OpenTimes[i],
                        IsHigh = true,
                        Strength = CalculateSwingStrength(bars, i, true)
                    });
                }

                // Check for swing low
                bool isSwingLow = true;
                for (int j = 1; j <= lookAround; j++)
                {
                    if (bars.LowPrices[i] >= bars.LowPrices[i - j] || bars.LowPrices[i] >= bars.LowPrices[i + j])
                    {
                        isSwingLow = false;
                        break;
                    }
                }

                if (isSwingLow)
                {
                    swingLows.Add(new SwingPoint
                    {
                        Index = i,
                        Price = bars.LowPrices[i],
                        Time = bars.OpenTimes[i],
                        IsHigh = false,
                        Strength = CalculateSwingStrength(bars, i, false)
                    });
                }
            }

            return (swingHighs, swingLows);
        }

        private int CalculateSwingStrength(Bars bars, int index, bool isHigh)
        {
            int strength = 0;

            // Calculate strength based on how many bars the swing point is higher/lower than
            int lookAround = 10;
            for (int j = 1; j <= lookAround; j++)
            {
                if (index - j >= 0)
                {
                    if (isHigh && bars.HighPrices[index] > bars.HighPrices[index - j])
                    {
                        strength++;
                    }
                    else if (!isHigh && bars.LowPrices[index] < bars.LowPrices[index - j])
                    {
                        strength++;
                    }
                }

                if (index + j < bars.Count)
                {
                    if (isHigh && bars.HighPrices[index] > bars.HighPrices[index + j])
                    {
                        strength++;
                    }
                    else if (!isHigh && bars.LowPrices[index] < bars.LowPrices[index + j])
                    {
                        strength++;
                    }
                }
            }

            return strength;
        }

        public List<PriceZone> IdentifyKeyLevels(Bars bars, List<SwingPoint> swingHighs, List<SwingPoint> swingLows)
        {
            var keyLevels = new List<PriceZone>();

            // Add swing highs as resistance levels
            foreach (var swingHigh in swingHighs)
            {
                if (swingHigh.Strength >= 10) // Only consider strong swing points
                {
                    keyLevels.Add(new PriceZone
                    {
                        High = swingHigh.Price + (bars.SymbolInfo.PipSize * 5),
                        Low = swingHigh.Price - (bars.SymbolInfo.PipSize * 5),
                        StartTime = swingHigh.Time,
                        EndTime = bars.OpenTimes[bars.Count - 1],
                        Strength = swingHigh.Strength
                    });
                }
            }

            // Add swing lows as support levels
            foreach (var swingLow in swingLows)
            {
                if (swingLow.Strength >= 10) // Only consider strong swing points
                {
                    keyLevels.Add(new PriceZone
                    {
                        High = swingLow.Price + (bars.SymbolInfo.PipSize * 5),
                        Low = swingLow.Price - (bars.SymbolInfo.PipSize * 5),
                        StartTime = swingLow.Time,
                        EndTime = bars.OpenTimes[bars.Count - 1],
                        Strength = swingLow.Strength
                    });
                }
            }

            return keyLevels;
        }

        public List<LiquidityLevel> IdentifyLiquidityLevels(Bars bars, List<SwingPoint> swingHighs, List<SwingPoint> swingLows)
        {
            var liquidityLevels = new List<LiquidityLevel>();

            // Add liquidity above swing highs (stop losses from short positions)
            foreach (var swingHigh in swingHighs)
            {
                if (swingHigh.Strength >= 15) // Only consider very strong swing points for liquidity
                {
                    liquidityLevels.Add(new LiquidityLevel
                    {
                        High = swingHigh.Price + (bars.SymbolInfo.PipSize * 10),
                        Low = swingHigh.Price,
                        StartTime = swingHigh.Time,
                        EndTime = bars.OpenTimes[bars.Count - 1],
                        Strength = swingHigh.Strength,
                        Direction = TradeDirection.Sell,
                        IsSwept = IsLiquiditySwept(bars, swingHigh, true)
                    });
                }
            }

            // Add liquidity below swing lows (stop losses from long positions)
            foreach (var swingLow in swingLows)
            {
                if (swingLow.Strength >= 15) // Only consider very strong swing points for liquidity
                {
                    liquidityLevels.Add(new LiquidityLevel
                    {
                        High = swingLow.Price,
                        Low = swingLow.Price - (bars.SymbolInfo.PipSize * 10),
                        StartTime = swingLow.Time,
                        EndTime = bars.OpenTimes[bars.Count - 1],
                        Strength = swingLow.Strength,
                        Direction = TradeDirection.Buy,
                        IsSwept = IsLiquiditySwept(bars, swingLow, false)
                    });
                }
            }

            return liquidityLevels;
        }

        private bool IsLiquiditySwept(Bars bars, SwingPoint swingPoint, bool isHigh)
        {
            // Check if price has swept the liquidity level
            for (int i = swingPoint.Index + 1; i < bars.Count; i++)
            {
                if (isHigh && bars.HighPrices[i] > swingPoint.Price + (bars.SymbolInfo.PipSize * 5))
                {
                    return true;
                }
                else if (!isHigh && bars.LowPrices[i] < swingPoint.Price - (bars.SymbolInfo.PipSize * 5))
                {
                    return true;
                }
            }

            return false;
        }

        public List<BreakerBlock> IdentifyBreakerBlocks(Bars bars, List<OrderBlock> orderBlocks)
        {
            var breakerBlocks = new List<BreakerBlock>();

            foreach (var orderBlock in orderBlocks)
            {
                // Check if the order block has been broken and then retested
                bool broken = false;
                bool retested = false;

                for (int i = bars.Count - 1; i >= 0; i--)
                {
                    if (bars.OpenTimes[i] < orderBlock.EndTime)
                        break;

                    if (!broken)
                    {
                        // Check if price has broken through the order block
                        if (orderBlock.Direction == TradeDirection.Buy && bars.LowPrices[i] < orderBlock.Low)
                        {
                            broken = true;
                        }
                        else if (orderBlock.Direction == TradeDirection.Sell && bars.HighPrices[i] > orderBlock.High)
                        {
                            broken = true;
                        }
                    }
                    else if (!retested)
                    {
                        // Check if price has retested the order block
                        if (orderBlock.Direction == TradeDirection.Buy && bars.HighPrices[i] > orderBlock.High)
                        {
                            retested = true;
                        }
                        else if (orderBlock.Direction == TradeDirection.Sell && bars.LowPrices[i] < orderBlock.Low)
                        {
                            retested = true;
                        }
                    }
                }

                // If the order block has been broken and retested, it's a breaker block
                if (broken && retested)
                {
                    breakerBlocks.Add(new BreakerBlock
                    {
                        High = orderBlock.High,
                        Low = orderBlock.Low,
                        StartTime = orderBlock.StartTime,
                        EndTime = orderBlock.EndTime,
                        Strength = orderBlock.Strength,
                        Direction = orderBlock.Direction == TradeDirection.Buy ? TradeDirection.Sell : TradeDirection.Buy,
                        IsTested = true
                    });
                }
            }

            return breakerBlocks;
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
            double currentPrice = bars.ClosePrices[bars.Count - 1];

            // Determine bias based on market structure
            TradeDirection bias = TradeDirection.Buy;
            if (marketStructure == MarketStructure.Uptrend)
            {
                bias = TradeDirection.Buy;
            }
            else if (marketStructure == MarketStructure.Downtrend)
            {
                bias = TradeDirection.Sell;
            }

            // Check for order block opportunities
            foreach (var ob in orderBlocks)
            {
                // Only consider fresh order blocks (not mitigated)
                if (!ob.IsMitigated)
                {
                    // Check if price is near the order block
                    bool isPriceNear = false;

                    if (ob.Direction == TradeDirection.Buy && currentPrice <= ob.High && currentPrice >= ob.Low)
                    {
                        isPriceNear = true;
                    }
                    else if (ob.Direction == TradeDirection.Sell && currentPrice >= ob.Low && currentPrice <= ob.High)
                    {
                        isPriceNear = true;
                    }

                    if (isPriceNear)
                    {
                        // Create entry opportunity
                        opportunities.Add(new EntryOpportunity
                        {
                            Direction = ob.Direction,
                            EntryPrice = ob.Direction == TradeDirection.Buy ? ob.Low : ob.High,
                            Zone = ob,
                            SetupType = SetupType.OrderBlock,
                            Strength = ob.Strength + (ob.Direction == bias ? 20 : 0) + (isInKillZone ? 15 : 0)
                        });
                    }
                }
            }

            // Check for fair value gap opportunities
            foreach (var fvg in fairValueGaps)
            {
                // Only consider unfilled fair value gaps
                if (!fvg.IsFilled)
                {
                    // Check if price is near the fair value gap
                    bool isPriceNear = false;

                    if (fvg.Direction == TradeDirection.Buy && currentPrice <= fvg.High + (bars.SymbolInfo.PipSize * 10) && currentPrice >= fvg.Low - (bars.SymbolInfo.PipSize * 10))
                    {
                        isPriceNear = true;
                    }
                    else if (fvg.Direction == TradeDirection.Sell && currentPrice >= fvg.Low - (bars.SymbolInfo.PipSize * 10) && currentPrice <= fvg.High + (bars.SymbolInfo.PipSize * 10))
                    {
                        isPriceNear = true;
                    }

                    if (isPriceNear)
                    {
                        // Create entry opportunity
                        opportunities.Add(new EntryOpportunity
                        {
                            Direction = fvg.Direction,
                            EntryPrice = fvg.Direction == TradeDirection.Buy ? fvg.Low : fvg.High,
                            Zone = fvg,
                            SetupType = SetupType.FairValueGap,
                            Strength = 50 + (int)(fvg.GapSize / bars.SymbolInfo.PipSize) + (fvg.Direction == bias ? 20 : 0) + (isInKillZone ? 15 : 0)
                        });
                    }
                }
            }

            // Check for breaker block opportunities
            foreach (var bb in breakerBlocks)
            {
                // Check if price is near the breaker block
                bool isPriceNear = false;

                if (bb.Direction == TradeDirection.Buy && currentPrice <= bb.High + (bars.SymbolInfo.PipSize * 10) && currentPrice >= bb.Low - (bars.SymbolInfo.PipSize * 10))
                {
                    isPriceNear = true;
                }
                else if (bb.Direction == TradeDirection.Sell && currentPrice >= bb.Low - (bars.SymbolInfo.PipSize * 10) && currentPrice <= bb.High + (bars.SymbolInfo.PipSize * 10))
                {
                    isPriceNear = true;
                }

                if (isPriceNear)
                {
                    // Create entry opportunity
                    opportunities.Add(new EntryOpportunity
                    {
                        Direction = bb.Direction,
                        EntryPrice = bb.Direction == TradeDirection.Buy ? bb.Low : bb.High,
                        Zone = bb,
                        SetupType = SetupType.BreakerBlock,
                        Strength = bb.Strength + (bb.Direction == bias ? 20 : 0) + (isInKillZone ? 15 : 0)
                    });
                }
            }

            // Check for liquidity sweep opportunities
            foreach (var ll in liquidityLevels)
            {
                // Only consider swept liquidity levels
                if (ll.IsSwept)
                {
                    // Check if price is near the liquidity level
                    bool isPriceNear = false;

                    if (ll.Direction == TradeDirection.Buy && currentPrice <= ll.High + (bars.SymbolInfo.PipSize * 15) && currentPrice >= ll.Low)
                    {
                        isPriceNear = true;
                    }
                    else if (ll.Direction == TradeDirection.Sell && currentPrice >= ll.Low && currentPrice <= ll.High + (bars.SymbolInfo.PipSize * 15))
                    {
                        isPriceNear = true;
                    }

                    if (isPriceNear)
                    {
                        // Create entry opportunity
                        opportunities.Add(new EntryOpportunity
                        {
                            Direction = ll.Direction,
                            EntryPrice = ll.Direction == TradeDirection.Buy ? ll.Low : ll.High,
                            Zone = ll,
                            SetupType = SetupType.LiquiditySweep,
                            Strength = ll.Strength + (ll.Direction == bias ? 20 : 0) + (isInKillZone ? 15 : 0)
                        });
                    }
                }
            }

            // Check for kill zone specific opportunities
            if (isInKillZone)
            {
                // Add kill zone specific setups
                // For example, London Breakout during London open kill zone

                // Get the current session high and low
                double sessionHigh = double.MinValue;
                double sessionLow = double.MaxValue;

                for (int i = bars.Count - 1; i >= Math.Max(0, bars.Count - 20); i--)
                {
                    sessionHigh = Math.Max(sessionHigh, bars.HighPrices[i]);
                    sessionLow = Math.Min(sessionLow, bars.LowPrices[i]);
                }

                // Check for breakout opportunities
                if (currentPrice > sessionHigh - (bars.SymbolInfo.PipSize * 5))
                {
                    opportunities.Add(new EntryOpportunity
                    {
                        Direction = TradeDirection.Buy,
                        EntryPrice = sessionHigh,
                        Zone = new PriceZone
                        {
                            High = sessionHigh + (bars.SymbolInfo.PipSize * 10),
                            Low = sessionHigh - (bars.SymbolInfo.PipSize * 5),
                            StartTime = bars.OpenTimes[bars.Count - 20],
                            EndTime = bars.OpenTimes[bars.Count - 1],
                            Strength = 70
                        },
                        SetupType = SetupType.KillZone,
                        Strength = 70 + (TradeDirection.Buy == bias ? 20 : 0)
                    });
                }
                else if (currentPrice < sessionLow + (bars.SymbolInfo.PipSize * 5))
                {
                    opportunities.Add(new EntryOpportunity
                    {
                        Direction = TradeDirection.Sell,
                        EntryPrice = sessionLow,
                        Zone = new PriceZone
                        {
                            High = sessionLow + (bars.SymbolInfo.PipSize * 5),
                            Low = sessionLow - (bars.SymbolInfo.PipSize * 10),
                            StartTime = bars.OpenTimes[bars.Count - 20],
                            EndTime = bars.OpenTimes[bars.Count - 1],
                            Strength = 70
                        },
                        SetupType = SetupType.KillZone,
                        Strength = 70 + (TradeDirection.Sell == bias ? 20 : 0)
                    });
                }
            }

            return opportunities;
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

            double currentPrice = bars.ClosePrices[bars.Count - 1];

            // Check for bullish BOS
            foreach (var swingHigh in recentSwingHighs)
            {
                if (currentPrice > swingHigh.Price && swingHigh.Strength >= 15)
                {
                    marketShifts.Add(new EntryOpportunity
                    {
                        Direction = TradeDirection.Buy,
                        EntryPrice = currentPrice,
                        Zone = new PriceZone
                        {
                            High = swingHigh.Price + (bars.SymbolInfo.PipSize * 15),
                            Low = swingHigh.Price - (bars.SymbolInfo.PipSize * 5),
                            StartTime = swingHigh.Time,
                            EndTime = bars.OpenTimes[bars.Count - 1],
                            Strength = swingHigh.Strength
                        },
                        SetupType = SetupType.BreakOfStructure,
                        Strength = 60 + swingHigh.Strength
                    });
                    break;
                }
            }

            // Check for bearish BOS
            foreach (var swingLow in recentSwingLows)
            {
                if (currentPrice < swingLow.Price && swingLow.Strength >= 15)
                {
                    marketShifts.Add(new EntryOpportunity
                    {
                        Direction = TradeDirection.Sell,
                        EntryPrice = currentPrice,
                        Zone = new PriceZone
                        {
                            High = swingLow.Price + (bars.SymbolInfo.PipSize * 5),
                            Low = swingLow.Price - (bars.SymbolInfo.PipSize * 15),
                            StartTime = swingLow.Time,
                            EndTime = bars.OpenTimes[bars.Count - 1],
                            Strength = swingLow.Strength
                        },
                        SetupType = SetupType.BreakOfStructure,
                        Strength = 60 + swingLow.Strength
                    });
                    break;
                }
            }

            // Check for Change of Character (CHoCH)
            // A change of character occurs when price creates a higher low after a downtrend (bullish CHoCH)
            // or a lower high after an uptrend (bearish CHoCH)

            // Need at least 2 swing points to identify CHoCH
            if (recentSwingLows.Count >= 2)
            {
                // Check for bullish CHoCH (higher low)
                if (recentSwingLows[0].Price > recentSwingLows[1].Price)
                {
                    marketShifts.Add(new EntryOpportunity
                    {
                        Direction = TradeDirection.Buy,
                        EntryPrice = currentPrice,
                        Zone = new PriceZone
                        {
                            High = recentSwingLows[0].Price + (bars.SymbolInfo.PipSize * 10),
                            Low = recentSwingLows[0].Price - (bars.SymbolInfo.PipSize * 5),
                            StartTime = recentSwingLows[0].Time,
                            EndTime = bars.OpenTimes[bars.Count - 1],
                            Strength = recentSwingLows[0].Strength
                        },
                        SetupType = SetupType.ChangeOfCharacter,
                        Strength = 55 + recentSwingLows[0].Strength
                    });
                }
            }

            if (recentSwingHighs.Count >= 2)
            {
                // Check for bearish CHoCH (lower high)
                if (recentSwingHighs[0].Price < recentSwingHighs[1].Price)
                {
                    marketShifts.Add(new EntryOpportunity
                    {
                        Direction = TradeDirection.Sell,
                        EntryPrice = currentPrice,
                        Zone = new PriceZone
                        {
                            High = recentSwingHighs[0].Price + (bars.SymbolInfo.PipSize * 5),
                            Low = recentSwingHighs[0].Price - (bars.SymbolInfo.PipSize * 10),
                            StartTime = recentSwingHighs[0].Time,
                            EndTime = bars.OpenTimes[bars.Count - 1],
                            Strength = recentSwingHighs[0].Strength
                        },
                        SetupType = SetupType.ChangeOfCharacter,
                        Strength = 55 + recentSwingHighs[0].Strength
                    });
                }
            }

            return marketShifts;
        }
    }

    public class SMCAnalyzer
    {
        private Robot _robot;

        public SMCAnalyzer(Robot robot)
        {
            _robot = robot;
        }

        public List<OrderBlock> IdentifyOrderBlocks(Bars bars, int barsCount)
        {
            var orderBlocks = new List<OrderBlock>();

            // Start from the oldest bar we want to analyze
            for (int i = bars.Count - barsCount; i < bars.Count - 1; i++)
            {
                // Check for bullish order block (BOB)
                // A bearish candle followed by strong bullish momentum
                if (bars.ClosePrices[i] < bars.OpenPrices[i]) // Bearish candle
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

                        // Check if the order block has been mitigated
                        bool isMitigated = IsOrderBlockMitigated(bars, i, true);

                        orderBlocks.Add(new OrderBlock
                        {
                            High = bars.HighPrices[i],
                            Low = bars.LowPrices[i],
                            StartTime = bars.OpenTimes[i],
                            EndTime = bars.OpenTimes[i + 1],
                            Strength = strength,
                            Direction = TradeDirection.Buy,
                            IsMitigated = isMitigated
                        });
                    }
                }

                // Check for bearish order block (BOB)
                // A bullish candle followed by strong bearish momentum
                if (bars.ClosePrices[i] > bars.OpenPrices[i]) // Bullish candle
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

                        // Check if the order block has been mitigated
                        bool isMitigated = IsOrderBlockMitigated(bars, i, false);

                        orderBlocks.Add(new OrderBlock
                        {
                            High = bars.HighPrices[i],
                            Low = bars.LowPrices[i],
                            StartTime = bars.OpenTimes[i],
                            EndTime = bars.OpenTimes[i + 1],
                            Strength = strength,
                            Direction = TradeDirection.Sell,
                            IsMitigated = isMitigated
                        });
                    }
                }
            }

            return orderBlocks;
        }

        private int CalculateOrderBlockStrength(Bars bars, int index, bool isBullish)
        {
            int strength = 50; // Base strength

            // Adjust strength based on candle size
            double candleSize = Math.Abs(bars.HighPrices[index] - bars.LowPrices[index]) / bars.SymbolInfo.PipSize;

            if (candleSize > 20) // Large candle
            {
                strength += 10;
            }
            else if (candleSize < 5) // Small candle
            {
                strength -= 10;
            }

            // Adjust strength based on volume (if available)
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

                if (bars.TickVolumes[index] > avgVolume * 1.5) // High volume
                {
                    strength += 15;
                }
                else if (bars.TickVolumes[index] < avgVolume * 0.5) // Low volume
                {
                    strength -= 15;
                }
            }

            // Adjust strength based on momentum after the order block
            int momentumCount = 0;

            for (int j = index + 1; j < Math.Min(index + 6, bars.Count); j++)
            {
                if (isBullish && bars.ClosePrices[j] > bars.OpenPrices[j] &&
                    bars.ClosePrices[j] > bars.ClosePrices[j - 1])
                {
                    momentumCount++;
                }
                else if (!isBullish && bars.ClosePrices[j] < bars.OpenPrices[j] &&
                    bars.ClosePrices[j] < bars.ClosePrices[j - 1])
                {
                    momentumCount++;
                }
            }

            strength += momentumCount * 5;

            return strength;
        }

        private bool IsOrderBlockMitigated(Bars bars, int index, bool isBullish)
        {
            // Check if price has returned to the order block and mitigated it
            for (int i = index + 1; i < bars.Count; i++)
            {
                if (isBullish && bars.LowPrices[i] <= bars.LowPrices[index])
                {
                    return true;
                }
                else if (!isBullish && bars.HighPrices[i] >= bars.HighPrices[index])
                {
                    return true;
                }
            }

            return false;
        }

        public List<FairValueGap> IdentifyFairValueGaps(Bars bars, int barsCount)
        {
            var fairValueGaps = new List<FairValueGap>();

            // Start from the oldest bar we want to analyze
            for (int i = bars.Count - barsCount + 1; i < bars.Count - 1; i++)
            {
                // Check for bullish FVG
                // Low of current candle > High of previous candle
                if (bars.LowPrices[i] > bars.HighPrices[i - 1])
                {
                    // Calculate gap size
                    double gapSize = bars.LowPrices[i] - bars.HighPrices[i - 1];

                    // Check if the gap has been filled
                    bool isFilled = IsFairValueGapFilled(bars, i, true);

                    fairValueGaps.Add(new FairValueGap
                    {
                        High = bars.LowPrices[i],
                        Low = bars.HighPrices[i - 1],
                        StartTime = bars.OpenTimes[i - 1],
                        EndTime = bars.OpenTimes[i],
                        Strength = 50 + (int)(gapSize / bars.SymbolInfo.PipSize),
                        Direction = TradeDirection.Buy,
                        IsFilled = isFilled,
                        GapSize = gapSize
                    });
                }

                // Check for bearish FVG
                // High of current candle < Low of previous candle
                if (bars.HighPrices[i] < bars.LowPrices[i - 1])
                {
                    // Calculate gap size
                    double gapSize = bars.LowPrices[i - 1] - bars.HighPrices[i];

                    // Check if the gap has been filled
                    bool isFilled = IsFairValueGapFilled(bars, i, false);

                    fairValueGaps.Add(new FairValueGap
                    {
                        High = bars.LowPrices[i - 1],
                        Low = bars.HighPrices[i],
                        StartTime = bars.OpenTimes[i - 1],
                        EndTime = bars.OpenTimes[i],
                        Strength = 50 + (int)(gapSize / bars.SymbolInfo.PipSize),
                        Direction = TradeDirection.Sell,
                        IsFilled = isFilled,
                        GapSize = gapSize
                    });
                }
            }

            return fairValueGaps;
        }

        private bool IsFairValueGapFilled(Bars bars, int index, bool isBullish)
        {
            // Check if price has returned to the fair value gap and filled it
            for (int i = index + 1; i < bars.Count; i++)
            {
                if (isBullish && bars.LowPrices[i] <= bars.HighPrices[index - 1])
                {
                    return true;
                }
                else if (!isBullish && bars.HighPrices[i] >= bars.LowPrices[index - 1])
                {
                    return true;
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

        public List<EntryOpportunity> IdentifySessionPatterns(Bars bars)
        {
            var patterns = new List<EntryOpportunity>();

            // Identify London session opening range
            var londonOpenRange = IdentifySessionOpeningRange(bars, 7, 9); // 7-9 UTC

            // Identify New York session opening range
            var nyOpenRange = IdentifySessionOpeningRange(bars, 13, 15); // 13-15 UTC

            // Check for London Breakout pattern
            if (londonOpenRange != null)
            {
                // Check if price is near the range boundaries
                double currentPrice = bars.ClosePrices[bars.Count - 1];

                if (currentPrice >= londonOpenRange.High - (bars.SymbolInfo.PipSize * 5))
                {
                    patterns.Add(new EntryOpportunity
                    {
                        Direction = TradeDirection.Buy,
                        EntryPrice = londonOpenRange.High,
                        Zone = londonOpenRange,
                        SetupType = SetupType.KillZone,
                        Strength = 65
                    });
                }
                else if (currentPrice <= londonOpenRange.Low + (bars.SymbolInfo.PipSize * 5))
                {
                    patterns.Add(new EntryOpportunity
                    {
                        Direction = TradeDirection.Sell,
                        EntryPrice = londonOpenRange.Low,
                        Zone = londonOpenRange,
                        SetupType = SetupType.KillZone,
                        Strength = 65
                    });
                }
            }

            // Check for NY Reversal pattern
            if (nyOpenRange != null)
            {
                // Check if London session was trending and NY session is reversing
                bool londonUptrend = IsSessionTrending(bars, 7, 13, true);
                bool londonDowntrend = IsSessionTrending(bars, 7, 13, false);

                double currentPrice = bars.ClosePrices[bars.Count - 1];

                if (londonUptrend && currentPrice <= nyOpenRange.Low + (bars.SymbolInfo.PipSize * 5))
                {
                    patterns.Add(new EntryOpportunity
                    {
                        Direction = TradeDirection.Sell,
                        EntryPrice = nyOpenRange.Low,
                        Zone = nyOpenRange,
                        SetupType = SetupType.KillZone,
                        Strength = 70
                    });
                }
                else if (londonDowntrend && currentPrice >= nyOpenRange.High - (bars.SymbolInfo.PipSize * 5))
                {
                    patterns.Add(new EntryOpportunity
                    {
                        Direction = TradeDirection.Buy,
                        EntryPrice = nyOpenRange.High,
                        Zone = nyOpenRange,
                        SetupType = SetupType.KillZone,
                        Strength = 70
                    });
                }
            }

            return patterns;
        }

        private PriceZone IdentifySessionOpeningRange(Bars bars, int startHourUtc, int endHourUtc)
        {
            double rangeHigh = double.MinValue;
            double rangeLow = double.MaxValue;
            DateTime startTime = DateTime.MinValue;
            DateTime endTime = DateTime.MinValue;

            // Find the most recent session opening range
            for (int i = bars.Count - 1; i >= 0; i--)
            {
                DateTime barTime = bars.OpenTimes[i].ToUniversalTime();
                int hour = barTime.Hour;

                if (hour >= startHourUtc && hour < endHourUtc)
                {
                    // This bar is within the session opening hours
                    rangeHigh = Math.Max(rangeHigh, bars.HighPrices[i]);
                    rangeLow = Math.Min(rangeLow, bars.LowPrices[i]);

                    if (startTime == DateTime.MinValue)
                    {
                        endTime = bars.OpenTimes[i];
                    }

                    startTime = bars.OpenTimes[i];
                }
                else if (hour < startHourUtc && rangeHigh != double.MinValue)
                {
                    // We've found the complete session range
                    break;
                }
            }

            if (rangeHigh != double.MinValue && rangeLow != double.MaxValue)
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

                    if (checkUptrend && bars.ClosePrices[i] > bars.OpenPrices[i])
                    {
                        trendingBars++;
                    }
                    else if (!checkUptrend && bars.ClosePrices[i] < bars.OpenPrices[i])
                    {
                        trendingBars++;
                    }
                }
                else if (hour < startHourUtc && totalBars > 0)
                {
                    // We've found all bars in the session
                    break;
                }
            }

            // Consider trending if at least 60% of bars are in the trend direction
            return totalBars > 0 && (double)trendingBars / totalBars >= 0.6;
        }
    }

    #endregion
}


