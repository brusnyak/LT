import React, { useState, useEffect } from 'react';
import { BarChart3, Dumbbell, TestTube, Settings } from 'lucide-react';
import { fetchTrades, clearTrades, fetchChallenge } from '../services/api';
import BalanceProgressBar from '../components/journal/BalanceProgressBar';
import EnhancedEquityCurve from '../components/journal/EnhancedEquityCurve';
import StatCard from '../components/journal/StatCard';
import TradeHistoryTable from '../components/journal/TradeHistoryTable';
import GymAnalysisPanel from '../components/gym/GymAnalysisPanel';
import { useMarket } from '../context/MarketContext';
import './JournalPage.css';

export default function JournalPage() {
    const [journalData, setJournalData] = useState(null);
    const [challengeData, setChallengeData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [viewMode, setViewMode] = useState('journal'); // 'journal', 'gym', 'prop', 'backtest'
    const { pair } = useMarket();

    useEffect(() => {
        const loadJournal = async () => {
            setLoading(true);
            try {
                // Fetch challenge data for balances and targets
                const challenge = await fetchChallenge(1);
                setChallengeData(challenge);

                // Fetch trades from database
                const trades = await fetchTrades(1, pair);

                // Calculate metrics from trades
                const closedTrades = trades.filter(t =>
                    ['TP_HIT', 'SL_HIT', 'MANUAL_CLOSE'].includes(t.outcome)
                );

                const winningTrades = closedTrades.filter(t => t.outcome === 'TP_HIT');
                const losingTrades = closedTrades.filter(t => t.outcome === 'SL_HIT');

                // Calculate actual balance from trades
                const actualBalance = closedTrades.length > 0
                    ? closedTrades[closedTrades.length - 1].balance_after || challenge.current_balance
                    : challenge.current_balance;

                const extended_metrics = {
                    win_rate: closedTrades.length > 0
                        ? (winningTrades.length / closedTrades.length) * 100
                        : 0,
                    avg_rr: closedTrades.length > 0
                        ? closedTrades.reduce((sum, t) => sum + (t.rr_achieved || 0), 0) / closedTrades.length
                        : 0,
                    final_balance: actualBalance,
                    max_drawdown_pct: 0, // TODO: Calculate from equity curve
                    avg_sl_pips: 0,
                    avg_tp_pips: 0,
                    winning_trades: winningTrades.length,
                    losing_trades: losingTrades.length
                };

                setJournalData({
                    trades: trades,
                    extended_metrics: extended_metrics,
                    equity_curve: [] // TODO: Calculate equity curve from trades
                });
            } catch (error) {
                console.error("Failed to load journal:", error);
            } finally {
                setLoading(false);
            }
        };
        loadJournal();
    }, [pair]);

    if (loading) {
        return <div className="loading-container">Loading Journal...</div>;
    }

    const stats = journalData?.extended_metrics || {};
    const trades = journalData?.trades || [];

    // Build equity curve from trade history
    const buildEquityCurve = () => {
        if (!challengeData || trades.length === 0) return [];

        let balance = challengeData.starting_balance;
        const curve = [{ date: 'Start', equity: balance }];

        // Get closed trades sorted by close time
        const closedTrades = trades
            .filter(t => t.close_time && t.pnl !== null)
            .sort((a, b) => new Date(a.close_time) - new Date(b.close_time));

        closedTrades.forEach(trade => {
            balance += trade.pnl;
            curve.push({
                date: new Date(trade.close_time).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
                equity: balance
            });
        });

        return curve;
    };

    const equityData = buildEquityCurve();

    // Use challenge data for balances and targets
    const currentBalance = challengeData?.current_balance || stats.final_balance || 50000;
    const startingBalance = challengeData?.starting_balance || 50000;
    const profitTargetPct = challengeData?.profit_target || 8; // percentage
    const profitTargetAmount = startingBalance * (profitTargetPct / 100);
    const goal = startingBalance + profitTargetAmount; // Target balance to reach
    const dailyLossLimit = startingBalance * (1 - (challengeData?.daily_loss_limit || 7) / 100);
    const maxDrawdown = startingBalance * (1 - (challengeData?.max_drawdown || 12) / 100);

    const handleClearHistory = async () => {
        if (!window.confirm('Are you sure you want to clear all trade history? This cannot be undone.')) {
            return;
        }

        try {
            await clearTrades(1);  // Clear all trades for challenge_id = 1
            alert('✅ Trade history cleared successfully');
            // Reload journal
            window.location.reload();
        } catch (err) {
            console.error('Failed to clear history:', err);
            alert('❌ Failed to clear history');
        }
    };

    return (
        <div className="journal-page-new">
            {/* Header with Mode Toggle */}
            <div className="journal-header-new">
                <h1>Trading Journal</h1>
                <div className="mode-toggle">
                    <button
                        className={`mode-btn ${viewMode === 'journal' ? 'active' : ''}`}
                        onClick={() => setViewMode('journal')}
                    >
                        <BarChart3 size={18} />
                        <span>Journal</span>
                    </button>
                    <button
                        className={`mode-btn ${viewMode === 'gym' ? 'active' : ''}`}
                        onClick={() => setViewMode('gym')}
                    >
                        <Dumbbell size={18} />
                        <span>Gym Analysis</span>
                    </button>
                    <button
                        className={`mode-btn ${viewMode === 'prop' ? 'active' : ''}`}
                        onClick={() => setViewMode('prop')}
                        disabled
                    >
                        <Settings size={18} />
                        <span>Prop Challenge</span>
                    </button>
                    <button
                        className={`mode-btn ${viewMode === 'backtest' ? 'active' : ''}`}
                        onClick={() => setViewMode('backtest')}
                        disabled
                    >
                        <TestTube size={18} />
                        <span>Backtest</span>
                    </button>
                </div>
            </div>

            {viewMode === 'gym' ? (
                <GymAnalysisPanel />
            ) : (
                <>
                    {/* Balance Progress Bar */}
                    <div className="balance-section">
                        <BalanceProgressBar
                            currentBalance={currentBalance}
                            goal={goal}
                        />
                    </div>

                    {/* Main Content: 70/30 Split */}
                    <div className="main-content-split">
                        {/* Left: Equity Chart (70%) */}
                        <div className="equity-section">
                            <div className="section-header">
                                <h2>Equity Curve</h2>
                                <div className="chart-controls">
                                    <button className="chart-btn">1M</button>
                                    <button className="chart-btn active">3M</button>
                                    <button className="chart-btn">6M</button>
                                    <button className="chart-btn">1Y</button>
                                    <button className="chart-btn">All</button>
                                </div>
                            </div>
                            <EnhancedEquityCurve
                                data={equityData}
                                currentBalance={currentBalance}
                                goal={goal}
                                dailyLossLimit={dailyLossLimit}
                                maxDrawdown={maxDrawdown}
                            />
                        </div>

                        {/* Right: Metrics (30%) */}
                        <div className="metrics-section">
                            <h2>Performance Metrics</h2>
                            <div className="metrics-cards">
                                <div className="metric-card-compact">
                                    <span className="metric-label">Win Rate</span>
                                    <span className="metric-value">{(stats.win_rate || 0).toFixed(1)}%</span>
                                    <span className="metric-subtitle">{stats.winning_trades || 0}W - {stats.losing_trades || 0}L</span>
                                </div>
                                <div className="metric-card-compact">
                                    <span className="metric-label">Avg R:R</span>
                                    <span className="metric-value">{(stats.avg_rr || 0).toFixed(2)}</span>
                                    <span className="metric-subtitle">Target: 2.0</span>
                                </div>
                                <div className="metric-card-compact">
                                    <span className="metric-label">Avg SL</span>
                                    <span className="metric-value">{(stats.avg_sl_pips || 0).toFixed(1)}</span>
                                    <span className="metric-subtitle">pips</span>
                                </div>
                                <div className="metric-card-compact">
                                    <span className="metric-label">Avg TP</span>
                                    <span className="metric-value">{(stats.avg_tp_pips || 0).toFixed(1)}</span>
                                    <span className="metric-subtitle">pips</span>
                                </div>
                                <div className="metric-card-compact">
                                    <span className="metric-label">Max DD</span>
                                    <span className="metric-value">{(stats.max_drawdown_pct || 0).toFixed(1)}%</span>
                                    <span className="metric-subtitle">Limit: 12%</span>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Trade History */}
                    <div className="trade-history-section">
                        <div className="section-header">
                            <h2>Trade History</h2>
                            <div className="history-controls">
                                <button className="history-btn">This Month</button>
                                <button className="history-btn">Previous</button>
                                <button className="history-btn">Next</button>
                                <button
                                    className="history-btn danger"
                                    onClick={handleClearHistory}
                                >
                                    Clear History
                                </button>
                            </div>
                        </div>
                        <TradeHistoryTable trades={trades} />
                    </div>
                </>
            )}
        </div>
    );
}
