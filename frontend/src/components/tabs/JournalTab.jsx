/**
 * Journal Tab Component
 * Displays trade list with details
 */
import React from 'react';
import './JournalTab.css';

function JournalTab({ journalData }) {
    if (!journalData || !journalData.trades) {
        return (
            <div className="journal-tab">
                <div className="tab-header">
                    <h2>📓 Trade Journal</h2>
                </div>
                <div className="tab-content">
                    <p>No trade data available</p>
                </div>
            </div>
        );
    }

    const { trades, stats } = journalData;

    const formatPrice = (price) => price ? price.toFixed(5) : '-';
    const formatPnL = (pnl) => {
        if (!pnl) return '-';
        const sign = pnl >= 0 ? '+' : '';
        return `${sign}$${pnl.toFixed(2)}`;
    };
    const formatTime = (time) => {
        const date = new Date(time);
        return date.toLocaleString('en-US', {
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    return (
        <div className="journal-tab">
            <div className="tab-header">
                <h2>📓 Trade Journal</h2>
                <div className="quick-stats">
                    <div className="stat">
                        <span className="label">Win Rate:</span>
                        <span className="value">{stats.win_rate.toFixed(1)}%</span>
                    </div>
                    <div className="stat">
                        <span className="label">Avg RR:</span>
                        <span className="value">{stats.avg_rr.toFixed(2)}R</span>
                    </div>
                    <div className="stat">
                        <span className="label">Total P&L:</span>
                        <span className={`value ${stats.total_pnl >= 0 ? 'positive' : 'negative'}`}>
                            {formatPnL(stats.total_pnl)}
                        </span>
                    </div>
                </div>
            </div>
            <div className="tab-content">
                <div className="trades-table-container">
                    <table className="trades-table">
                        <thead>
                            <tr>
                                <th>#</th>
                                <th>Time</th>
                                <th>Type</th>
                                <th>Entry</th>
                                <th>SL</th>
                                <th>TP</th>
                                <th>Close</th>
                                <th>Outcome</th>
                                <th>P&L</th>
                                <th>RR</th>
                                <th>Balance</th>
                            </tr>
                        </thead>
                        <tbody>
                            {trades.map((trade) => (
                                <tr key={trade.id} className={`trade-row ${trade.outcome.toLowerCase()}`}>
                                    <td>{trade.id}</td>
                                    <td>{formatTime(trade.signal_time)}</td>
                                    <td>
                                        <span className={`type-badge ${trade.type.toLowerCase()}`}>
                                            {trade.type}
                                        </span>
                                    </td>
                                    <td>{formatPrice(trade.entry_price)}</td>
                                    <td className="sl">{formatPrice(trade.sl_price)}</td>
                                    <td className="tp">{formatPrice(trade.tp_price)}</td>
                                    <td>{formatPrice(trade.close_price)}</td>
                                    <td>
                                        <span className={`outcome-badge ${trade.outcome.toLowerCase()}`}>
                                            {trade.outcome}
                                        </span>
                                    </td>
                                    <td className={trade.pnl && trade.pnl >= 0 ? 'positive' : 'negative'}>
                                        {formatPnL(trade.pnl)}
                                    </td>
                                    <td>{trade.rr_achieved ? `${trade.rr_achieved.toFixed(1)}R` : '-'}</td>
                                    <td>${trade.balance_after ? trade.balance_after.toFixed(2) : trade.balance_before.toFixed(2)}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}

export default JournalTab;
