import React, { useState, useEffect } from 'react';
import { BarChart3, TrendingUp, TrendingDown, Clock, Target, Award, Calendar, Camera } from 'lucide-react';
import './GymAnalysisPanel.css';

export default function GymAnalysisPanel() {
    const [sessions, setSessions] = useState([]);
    const [selectedSession, setSelectedSession] = useState(null);
    const [sessionTrades, setSessionTrades] = useState([]);
    const [loading, setLoading] = useState(true);
    const [stats, setStats] = useState(null);

    // Load all sessions
    useEffect(() => {
        const loadSessions = async () => {
            setLoading(true);
            try {
                const resp = await fetch('http://localhost:9000/api/trainer/sessions');
                const data = await resp.json();
                setSessions(data);
            } catch (err) {
                console.error('Failed to load sessions:', err);
            } finally {
                setLoading(false);
            }
        };
        loadSessions();
    }, []);

    // Load session details when selected
    useEffect(() => {
        if (!selectedSession) return;

        const loadSessionDetails = async () => {
            try {
                const resp = await fetch(`http://localhost:9000/api/trainer/sessions/${selectedSession.id}`);
                const data = await resp.json();
                setSessionTrades(data.trades || []);
                calculateStats(data.trades || []);
            } catch (err) {
                console.error('Failed to load session details:', err);
            }
        };
        loadSessionDetails();
    }, [selectedSession]);

    const calculateStats = (trades) => {
        if (!trades.length) {
            setStats(null);
            return;
        }

        // Filter closed trades for performance stats
        const closedTrades = trades.filter(t => t.outcome && t.outcome !== 'OPEN' && t.outcome !== 'PENDING');

        // Win Rate
        const winCount = closedTrades.filter(t => t.outcome === 'TP_HIT' || t.pnl > 0).length;
        const lossCount = closedTrades.filter(t => t.outcome === 'SL_HIT' || t.pnl < 0).length;
        const winRate = closedTrades.length > 0 ? ((winCount / closedTrades.length) * 100) : 0;

        // PnL
        const totalPnL = closedTrades.reduce((sum, t) => sum + (t.pnl || 0), 0);

        // Account Growth
        const startBalance = selectedSession?.initial_balance || 50000;
        const growthPercent = (totalPnL / startBalance) * 100;

        // Calculate R:R distribution
        const rrValues = trades.map(t => {
            const risk = Math.abs(t.entry_price - t.sl_price);
            const reward = Math.abs(t.tp_price - t.entry_price);
            return (reward / risk);
        });

        const avgRR = rrValues.reduce((a, b) => a + b, 0) / rrValues.length;
        const maxRR = Math.max(...rrValues);
        const minRR = Math.min(...rrValues);

        // Count Long vs Short
        const longCount = trades.filter(t => t.type === 'LONG').length;
        const shortCount = trades.filter(t => t.type === 'SHORT').length;

        // Calculate durations
        const durations = trades
            .filter(t => t.close_time)
            .map(t => {
                const entry = new Date(t.entry_time);
                const exit = new Date(t.close_time);
                return (exit - entry) / 1000 / 60; // minutes
            });

        const avgDuration = durations.length > 0
            ? durations.reduce((a, b) => a + b, 0) / durations.length
            : 0;

        // Time-based analysis
        const hourCounts = new Array(24).fill(0);
        trades.forEach(t => {
            const hour = new Date(t.entry_time).getHours();
            hourCounts[hour]++;
        });

        setStats({
            totalTrades: trades.length,
            closedTrades: closedTrades.length, // Add this
            avgRR: avgRR.toFixed(2),
            maxRR: maxRR.toFixed(2),
            minRR: minRR.toFixed(2),
            longCount,
            shortCount,
            avgDuration: avgDuration.toFixed(0),
            rrDistribution: rrValues,
            hourCounts,
            totalPnL,
            winRate: winRate.toFixed(1),
            growthPercent: growthPercent.toFixed(2),
            initialBalance: startBalance
        });
    };

    const handleDeleteSession = async (sessionId, e) => {
        e.stopPropagation(); // Prevent card click

        if (!window.confirm('Are you sure you want to delete this session? This cannot be undone.')) {
            return;
        }

        try {
            await fetch(`http://localhost:9000/api/trainer/sessions/${sessionId}`, {
                method: 'DELETE',
            });

            // Reload sessions
            const resp = await fetch('http://localhost:9000/api/trainer/sessions');
            const data = await resp.json();
            setSessions(data);

            // If deleted session was selected, clear it
            if (selectedSession?.id === sessionId) {
                setSelectedSession(null);
            }
        } catch (err) {
            console.error('Failed to delete session:', err);
            alert('Failed to delete session');
        }
    };

    if (loading) {
        return <div className="gym-analysis-loading">Loading sessions...</div>;
    }

    // Filter out empty sessions
    const sessionsWithTrades = sessions.filter(s => s.total_trades > 0);

    if (!selectedSession) {
        return (
            <div className="gym-analysis-panel">
                <div className="analysis-header">
                    <h2>Gym Analysis</h2>
                    <p className="subtitle">Review your manual trading sessions</p>
                </div>

                <div className="sessions-grid">
                    {sessionsWithTrades.length === 0 ? (
                        <div className="empty-state">
                            <BarChart3 size={48} />
                            <h3>No Sessions Yet</h3>
                            <p>Start a session in the Gym tab to begin tracking your trades</p>
                        </div>
                    ) : (
                        sessionsWithTrades.map(session => (
                            <div
                                key={session.id}
                                className="session-card"
                                onClick={() => setSelectedSession(session)}
                            >
                                <div className="session-header">
                                    <h3>{session.name}</h3>
                                    <div className="session-actions">
                                        <span className="session-date">
                                            {new Date(session.created_at).toLocaleDateString()}
                                        </span>
                                        <button
                                            className="delete-btn"
                                            onClick={(e) => handleDeleteSession(session.id, e)}
                                            title="Delete session"
                                        >
                                            ×
                                        </button>
                                    </div>
                                </div>
                                <div className="session-stats">
                                    <div className="stat-item">
                                        <Target size={16} />
                                        <span>{session.total_trades} trades</span>
                                    </div>
                                    <div className="stat-item">
                                        <Calendar size={16} />
                                        <span>
                                            {new Date(session.start_date).toLocaleDateString()} - {new Date(session.end_date).toLocaleDateString()}
                                        </span>
                                    </div>
                                    <div className="stat-item">
                                        <TrendingUp size={16} />
                                        <span>${(session.total_pnl || 0).toFixed(2)}</span>
                                    </div>
                                </div>
                            </div>
                        ))
                    )}
                </div>
            </div>
        );
    }

    return (
        <div className="gym-analysis-panel">
            <div className="analysis-header">
                <button className="btn-back" onClick={() => setSelectedSession(null)}>
                    ← Back to Sessions
                </button>
                <div className="header-info">
                    <h2>{selectedSession.name}</h2>
                    <div className="header-badges">
                        <span className="badge">{sessionTrades.length} trades</span>
                        <span className={`badge ${stats?.growthPercent >= 0 ? 'profit' : 'loss'}`}>
                            {stats?.growthPercent > 0 ? '+' : ''}{stats?.growthPercent}% Growth
                        </span>
                        <span className="badge pnl">${stats?.totalPnL.toFixed(2)}</span>
                    </div>
                </div>
            </div>

            {stats && (
                <>
                    {/* Key Metrics */}
                    <div className="metrics-grid">
                        <div className="metric-card">
                            <div className="metric-icon">
                                <Target />
                            </div>
                            <div className="metric-content">
                                <span className="metric-label">Win Rate</span>
                                <span className={`metric-value ${Number(stats.winRate) >= 50 ? 'profit-text' : ''}`}>
                                    {stats.winRate}%
                                </span>
                            </div>
                        </div>
                        <div className="metric-card">
                            <div className="metric-icon">
                                <TrendingUp />
                            </div>
                            <div className="metric-content">
                                <span className="metric-label">Total PnL</span>
                                <span className={`metric-value ${stats.totalPnL >= 0 ? 'profit-text' : 'loss-text'}`}>
                                    ${stats.totalPnL.toFixed(2)}
                                </span>
                            </div>
                        </div>
                        <div className="metric-card">
                            <div className="metric-icon">
                                <Award />
                            </div>
                            <div className="metric-content">
                                <span className="metric-label">Avg R:R</span>
                                <span className="metric-value">1:{stats.avgRR}</span>
                            </div>
                        </div>
                        <div className="metric-card">
                            <div className="metric-icon">
                                <Clock />
                            </div>
                            <div className="metric-content">
                                <span className="metric-label">Avg Duration</span>
                                <span className="metric-value">{stats.avgDuration} min</span>
                            </div>
                        </div>
                    </div>

                    {/* Charts Row */}
                    <div className="charts-row">
                        {/* Long vs Short Pie Chart */}
                        <div className="chart-card">
                            <h3>Trade Direction</h3>
                            <div className="pie-chart">
                                <svg viewBox="0 0 200 200" width="200" height="200">
                                    {(() => {
                                        const total = stats.longCount + stats.shortCount;
                                        if (total === 0) return <circle cx="100" cy="100" r="80" fill="#333" />;

                                        const longPercent = (stats.longCount / total) * 100;
                                        const shortPercent = (stats.shortCount / total) * 100;
                                        const longAngle = (longPercent / 100) * 360;

                                        const getCoordinatesForPercent = (percent) => {
                                            const x = Math.cos(2 * Math.PI * percent);
                                            const y = Math.sin(2 * Math.PI * percent);
                                            return [x, y];
                                        };

                                        const [startX, startY] = getCoordinatesForPercent(0);
                                        const [endX, endY] = getCoordinatesForPercent(longPercent / 100);
                                        const largeArcFlag = longPercent > 50 ? 1 : 0;

                                        return (
                                            <>
                                                {/* If 100% one side, render full circle */}
                                                {longPercent === 100 && <circle cx="100" cy="100" r="80" fill="#26a69a" />}
                                                {shortPercent === 100 && <circle cx="100" cy="100" r="80" fill="#ef5350" />}

                                                {/* Else pie slices - FIX: SVG Arc path logic is tricky manually, simplified for 2 segments */}
                                                {longPercent > 0 && longPercent < 100 && (
                                                    <path
                                                        d={`M 100 100 L ${100 + 80} ${100} A 80 80 0 ${largeArcFlag} 1 ${100 + Math.cos(longAngle * Math.PI / 180) * 80} ${100 + Math.sin(longAngle * Math.PI / 180) * 80} Z`}
                                                        fill="#26a69a"
                                                    />
                                                )}
                                                {/* For short, just fill background circle and overlay long? Or similar. */}
                                                {/* Simplified approach: Just use conic-gradient CSS for pie chart, much easier than SVG path math in raw JS */}
                                            </>
                                        );
                                    })()}
                                    {/* Using CSS conic gradient instead for simplicity and robustness */}
                                    <foreignObject x="0" y="0" width="200" height="200">
                                        <div style={{
                                            width: '100%', height: '100%', borderRadius: '50%',
                                            background: `conic-gradient(#26a69a 0% ${stats.longCount / (stats.longCount + stats.shortCount || 1) * 100}%, #ef5350 0% 100%)`
                                        }}></div>
                                    </foreignObject>
                                    <circle cx="100" cy="100" r="50" fill="#1e222d" />
                                </svg>
                                <div className="pie-legend">
                                    <div className="legend-item">
                                        <span className="legend-color long"></span>
                                        <span>Long: {stats.longCount}</span>
                                    </div>
                                    <div className="legend-item">
                                        <span className="legend-color short"></span>
                                        <span>Short: {stats.shortCount}</span>
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* R:R Distribution Bar Chart */}
                        <div className="chart-card">
                            <h3>R:R Distribution</h3>
                            <div className="bar-chart">
                                {(() => {
                                    // Buckets: <1R, 1-2R, 2-3R, 3-4R, 4-5R, 5R+
                                    const buckets = [
                                        { min: 0, max: 1, label: '<1R' },
                                        { min: 1, max: 2, label: '1R' },
                                        { min: 2, max: 3, label: '2R' },
                                        { min: 3, max: 4, label: '3R' },
                                        { min: 4, max: 5, label: '4R' },
                                        { min: 5, max: Infinity, label: '5R+' },
                                    ];

                                    const counts = buckets.map(bucket =>
                                        stats.rrDistribution.filter(rr => rr >= bucket.min && rr < bucket.max).length
                                    );
                                    const maxCount = Math.max(...counts, 1);

                                    return buckets.map((bucket, i) => (
                                        <div key={i} className="bar-group">
                                            <div className="bar-container">
                                                <div
                                                    className="bar"
                                                    style={{ height: `${(counts[i] / maxCount) * 100}%` }}
                                                >
                                                    {counts[i] > 0 && <span className="bar-value">{counts[i]}</span>}
                                                </div>
                                            </div>
                                            <span className="bar-label">{bucket.label}</span>
                                        </div>
                                    ));
                                })()}
                            </div>
                        </div>

                        {/* Time Heatmap */}
                        <div className="chart-card">
                            <h3>Trading Hours</h3>
                            <div className="heatmap">
                                {stats.hourCounts.map((count, hour) => {
                                    const maxCount = Math.max(...stats.hourCounts);
                                    const intensity = maxCount > 0 ? count / maxCount : 0;
                                    return (
                                        <div
                                            key={hour}
                                            className="heatmap-cell"
                                            style={{
                                                background: `rgba(41, 98, 255, ${Math.max(0.1, intensity)})`,
                                                opacity: count > 0 ? 1 : 0.3
                                            }}
                                            title={`${hour}:00 - ${count} trades`}
                                        >
                                            {count > 0 && <span>{count}</span>}
                                        </div>
                                    );
                                })}
                            </div>
                            <div className="heatmap-labels">
                                <span>0h</span>
                                <span>6h</span>
                                <span>12h</span>
                                <span>18h</span>
                                <span>24h</span>
                            </div>
                        </div>
                    </div>

                    {/* Trade List */}
                    <div className="trades-section">
                        <h3>Trade History</h3>
                        <div className="trades-table">
                            <div className="table-header">
                                <span>#</span>
                                <span>Type</span>
                                <span>Outcome</span> {/* Added */}
                                <span>PnL</span>     {/* Added */}
                                <span>Entry</span>
                                <span>Stop Loss</span>
                                <span>Take Profit</span>
                                <span>R:R</span>
                                <span>Screenshot</span>
                                <span>Time Close</span>
                            </div>
                            {sessionTrades.map((trade, idx) => {
                                const risk = Math.abs(trade.entry_price - trade.sl_price);
                                const reward = Math.abs(trade.tp_price - trade.entry_price);
                                const rr = risk > 0 ? (reward / risk).toFixed(2) : '0';

                                // Calculate pips (assuming 5-digit pricing for forex)
                                const slPips = (risk * 10000).toFixed(1);
                                const tpPips = (reward * 10000).toFixed(1);

                                return (
                                    <div key={trade.id} className={`table-row ${trade.type.toLowerCase()}`}>
                                        <span>{idx + 1}</span>
                                        <span className="trade-type">{trade.type}</span>

                                        {/* Outcome */}
                                        <span className={`outcome-cell ${trade.outcome === 'TP_HIT' ? 'profit-text' :
                                                trade.outcome === 'SL_HIT' ? 'loss-text' : ''
                                            }`}>
                                            {trade.outcome?.replace('_HIT', '') || 'OPEN'}
                                        </span>

                                        {/* PnL */}
                                        <span className={`pnl-cell ${(trade.pnl || 0) > 0 ? 'profit-text' :
                                                (trade.pnl || 0) < 0 ? 'loss-text' : ''
                                            }`}>
                                            {trade.pnl ? `$${trade.pnl.toFixed(2)}` : '-'}
                                        </span>

                                        <span>{trade.entry_price.toFixed(5)}</span>
                                        <span className="price-pips">
                                            <div className="price">{trade.sl_price.toFixed(5)}</div>
                                            <div className="pips">({slPips} pips)</div>
                                        </span>
                                        <span className="price-pips">
                                            <div className="price">{trade.tp_price.toFixed(5)}</div>
                                            <div className="pips">({tpPips} pips)</div>
                                        </span>
                                        <span className="rr-value">{rr}R</span>
                                        <span className="trade-screenshot">
                                            {trade.screenshot_path ? (
                                                <a
                                                    href={`http://localhost:9000/${trade.screenshot_path}`}
                                                    target="_blank"
                                                    rel="noopener noreferrer"
                                                    title="View Screenshot"
                                                    className="screenshot-link"
                                                >
                                                    <Camera size={16} />
                                                </a>
                                            ) : (
                                                <span className="no-screenshot">-</span>
                                            )}
                                        </span>
                                        <span className="trade-time">
                                            {trade.close_time
                                                ? new Date(trade.close_time).toLocaleString('en-US', {
                                                    month: 'short',
                                                    day: 'numeric',
                                                    hour: '2-digit',
                                                    minute: '2-digit'
                                                })
                                                : 'Open'
                                            }
                                        </span>
                                    </div>
                                );
                            })}
                        </div>
                    </div>
                </>
            )}
        </div>
    );
}
