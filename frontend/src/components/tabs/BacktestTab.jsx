import React, { useState, useEffect } from 'react';
import './BacktestTab.css';
import TradingViewChart from '../chart/TradingViewChart';

function BacktestTab({ candleData, onRunBacktest }) {
    const [activeSubTab, setActiveSubTab] = useState('visuals');
    const [results, setResults] = useState([]);
    const [loading, setLoading] = useState(false);
    const [codeContent, setCodeContent] = useState('Loading code...');

    // Fetch code content (mock for now, or fetch from API if we expose it)
    useEffect(() => {
        // In a real app, we'd fetch this from the backend
        setCodeContent(`
def analyze_5m_signals(df_5m: pd.DataFrame, ranges: list[RangeLevel], 
                       use_dynamic_tp: bool = True,
                       use_swing_filter: bool = True,
                       use_trend_filter: bool = True,
                       min_rr: float = 1.5) -> list[Signal]:
    """
    Detects signals on 5M data based on 4H ranges.
    Signal: Breakout (Close outside) -> Re-entry (Close inside).
    Also calculates position close based on TP/SL hits.
    """
    # ... (Strategy Logic) ...
        `);
    }, []);

    const handleRunBacktest = async () => {
        setLoading(true);
        try {
            const response = await fetch('http://localhost:9000/api/backtest/run');
            const data = await response.json();
            setResults(data);
        } catch (error) {
            console.error("Backtest failed:", error);
            alert("Failed to run backtest");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="backtest-tab">
            <div className="backtest-main">
                <div className="backtest-header">
                    <h2>🧪 Backtest Lab</h2>
                    <div className="sub-tabs">
                        <button
                            className={`sub-tab-btn ${activeSubTab === 'code' ? 'active' : ''}`}
                            onClick={() => setActiveSubTab('code')}
                        >
                            Code (range_4h.py)
                        </button>
                        <button
                            className={`sub-tab-btn ${activeSubTab === 'visuals' ? 'active' : ''}`}
                            onClick={() => setActiveSubTab('visuals')}
                        >
                            Visuals
                        </button>
                    </div>
                </div>

                <div className="backtest-content">
                    {activeSubTab === 'code' ? (
                        <div className="code-view">
                            <pre>{codeContent}</pre>
                        </div>
                    ) : (
                        <div className="visuals-view">
                            {/* Reuse the chart component but maybe with specific backtest data if available */}
                            {candleData && candleData.length > 0 ? (
                                <TradingViewChart
                                    data={candleData}
                                    ranges={[]} // We could pass ranges here if we had them in context
                                    signals={[]} // We could pass signals here
                                />
                            ) : (
                                <div style={{ padding: 20, color: '#888' }}>No chart data available</div>
                            )}
                        </div>
                    )}
                </div>
            </div>

            <div className="backtest-sidebar">
                <div className="sidebar-header">
                    <h3>Comparison Results</h3>
                    <button
                        className="run-btn"
                        onClick={handleRunBacktest}
                        disabled={loading}
                    >
                        {loading ? 'Running...' : '▶ Run Backtest'}
                    </button>
                </div>

                <table className="comparison-table">
                    <thead>
                        <tr>
                            <th>Version</th>
                            <th>WR</th>
                            <th>RR</th>
                            <th>DD</th>
                            <th>PnL</th>
                        </tr>
                    </thead>
                    <tbody>
                        {results.map((res) => (
                            <tr key={res.id}>
                                <td className="version-name">{res.name.split(':')[0]}</td>
                                <td className={res.win_rate >= 60 ? 'positive' : ''}>
                                    {res.win_rate.toFixed(1)}%
                                </td>
                                <td>{res.avg_rr.toFixed(2)}R</td>
                                <td className={res.max_dd < 4 ? 'positive' : 'negative'}>
                                    {res.max_dd.toFixed(2)}%
                                </td>
                                <td className={res.total_pnl >= 0 ? 'positive' : 'negative'}>
                                    ${res.total_pnl.toFixed(0)}
                                </td>
                            </tr>
                        ))}
                        {results.length === 0 && !loading && (
                            <tr>
                                <td colSpan="5" style={{ textAlign: 'center', color: '#666' }}>
                                    Click Run to start backtest
                                </td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
}

export default BacktestTab;
