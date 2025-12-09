import React, { useState } from 'react';
import { TrendingUp, TrendingDown, Filter } from 'lucide-react';
import './TradeHistoryTable.css';

export default function TradeHistoryTable({ trades = [] }) {
    const [filter, setFilter] = useState('all'); // all, wins, losses, active

    // Map API data to component structure if needed
    const mappedTrades = trades.map(t => ({
        id: t.id,
        pair: t.pair,
        type: t.type,
        entry: t.entry_price || t.entry,
        exit: t.close_price || t.exit,
        rr: t.rr_achieved || t.rr,
        pnl: t.pnl,
        duration: t.duration || '-',
        date: t.signal_time ? new Date(t.signal_time).toLocaleDateString() : t.date,
        outcome: t.outcome || 'ACTIVE'
    }));

    const filteredTrades = mappedTrades.filter(trade => {
        if (filter === 'wins') return trade.pnl > 0;
        if (filter === 'losses') return trade.pnl < 0;
        if (filter === 'active') return trade.outcome === 'ACTIVE';
        return true;
    });

    return (
        <div className="trade-history-table">
            <div className="table-header">
                <h3>Trade History</h3>
                <div className="table-filters">
                    <button
                        className={`filter-btn ${filter === 'all' ? 'active' : ''}`}
                        onClick={() => setFilter('all')}
                    >
                        All ({mappedTrades.length})
                    </button>
                    <button
                        className={`filter-btn ${filter === 'wins' ? 'active' : ''}`}
                        onClick={() => setFilter('wins')}
                    >
                        Wins ({mappedTrades.filter(t => t.pnl > 0).length})
                    </button>
                    <button
                        className={`filter-btn ${filter === 'losses' ? 'active' : ''}`}
                        onClick={() => setFilter('losses')}
                    >
                        Losses ({mappedTrades.filter(t => t.pnl < 0).length})
                    </button>
                    <button
                        className={`filter-btn ${filter === 'active' ? 'active' : ''}`}
                        onClick={() => setFilter('active')}
                    >
                        Active ({mappedTrades.filter(t => t.outcome === 'ACTIVE').length})
                    </button>
                </div>
            </div>

            <div className="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>Date</th>
                            <th>Pair</th>
                            <th>Type</th>
                            <th>Entry</th>
                            <th>Exit</th>
                            <th>R:R</th>
                            <th>Duration</th>
                            <th>P&L</th>
                        </tr>
                    </thead>
                    <tbody>
                        {filteredTrades.map(trade => (
                            <tr key={trade.id} className={trade.pnl > 0 ? 'win' : trade.pnl < 0 ? 'loss' : 'active-row'}>
                                <td>{trade.date}</td>
                                <td className="pair-cell">{trade.pair}</td>
                                <td>
                                    <span className={`type-badge ${trade.type.toLowerCase()}`}>
                                        {trade.type === 'LONG' ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
                                        {trade.type}
                                    </span>
                                </td>
                                <td>{trade.entry ? trade.entry.toFixed(5) : '-'}</td>
                                <td>{trade.exit ? trade.exit.toFixed(5) : '-'}</td>
                                <td className={trade.rr > 0 ? 'positive' : trade.rr < 0 ? 'negative' : ''}>
                                    {trade.rr ? `${trade.rr.toFixed(2)}R` : '-'}
                                </td>
                                <td>{trade.duration}</td>
                                <td className={`pnl ${trade.pnl > 0 ? 'positive' : trade.pnl < 0 ? 'negative' : ''}`}>
                                    {trade.pnl !== null && trade.pnl !== undefined
                                        ? `${trade.pnl > 0 ? '+' : ''}$${trade.pnl.toFixed(2)}`
                                        : <span className="status-active">Active</span>}
                                </td>
                            </tr>
                        ))}
                        {filteredTrades.length === 0 && (
                            <tr>
                                <td colSpan="8" style={{ textAlign: 'center', padding: '2rem' }}>
                                    No trades found
                                </td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
