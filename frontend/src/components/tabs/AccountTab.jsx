/**
 * Account Tab Component
 * Displays account stats and equity curve
 */
import React from 'react';
import './AccountTab.css';

function AccountTab({ journalData }) {
    if (!journalData || !journalData.account) {
        return (
            <div className="account-tab">
                <div className="tab-header">
                    <h2>💰 Account</h2>
                </div>
                <div className="tab-content">
                    <p>No account data available</p>
                </div>
            </div>
        );
    }

    const { account, stats } = journalData;

    const formatMoney = (amount) => `$${amount.toFixed(2)}`;
    const formatPercent = (value) => `${value.toFixed(2)}%`;

    return (
        <div className="account-tab">
            <div className="tab-header">
                <h2>💰 Account Overview</h2>
            </div>
            <div className="tab-content">
                {/* Account Balance Section */}
                <div className="stats-grid">
                    <div className="stat-card primary">
                        <div className="stat-label">Current Balance</div>
                        <div className="stat-value">{formatMoney(account.balance)}</div>
                        <div className="stat-change">
                            <span className={account.total_pnl >= 0 ? 'positive' : 'negative'}>
                                {account.total_pnl >= 0 ? '▲' : '▼'} {formatMoney(Math.abs(account.total_pnl))}
                            </span>
                        </div>
                    </div>

                    <div className="stat-card">
                        <div className="stat-label">Starting Balance</div>
                        <div className="stat-value">{formatMoney(account.starting_balance)}</div>
                    </div>

                    <div className="stat-card">
                        <div className="stat-label">Total P&L</div>
                        <div className={`stat-value ${account.total_pnl >= 0 ? 'positive' : 'negative'}`}>
                            {formatMoney(account.total_pnl)}
                        </div>
                    </div>

                    <div className="stat-card">
                        <div className="stat-label">Daily P&L</div>
                        <div className={`stat-value ${account.daily_pnl >= 0 ? 'positive' : 'negative'}`}>
                            {formatMoney(account.daily_pnl)}
                        </div>
                    </div>
                </div>

                {/* Trading Stats Section */}
                <div className="section">
                    <h3>Trading Statistics</h3>
                    <div className="stats-grid">
                        <div className="stat-card">
                            <div className="stat-label">Total Trades</div>
                            <div className="stat-value">{account.total_trades}</div>
                        </div>

                        <div className="stat-card">
                            <div className="stat-label">Win Rate</div>
                            <div className="stat-value positive">{formatPercent(account.win_rate)}</div>
                            <div className="stat-detail">
                                {account.winning_trades}W / {account.losing_trades}L
                            </div>
                        </div>

                        <div className="stat-card">
                            <div className="stat-label">Avg RR</div>
                            <div className="stat-value">{account.avg_rr.toFixed(2)}R</div>
                        </div>

                        <div className="stat-card">
                            <div className="stat-label">Max Drawdown</div>
                            <div className="stat-value negative">{formatPercent(account.max_drawdown)}</div>
                        </div>

                        <div className="stat-card">
                            <div className="stat-label">Active Trades</div>
                            <div className="stat-value">{account.active_trades}</div>
                        </div>

                        <div className="stat-card">
                            <div className="stat-label">Open Risk</div>
                            <div className="stat-value">{formatMoney(account.total_risk)}</div>
                        </div>
                    </div>
                </div>

                {/* Performance Breakdown */}
                <div className="section">
                    <h3>Performance Breakdown</h3>
                    <div className="stats-grid">
                        <div className="stat-card">
                            <div className="stat-label">Best Trade</div>
                            <div className="stat-value positive">
                                {stats.best_trade ? formatMoney(stats.best_trade) : '-'}
                            </div>
                        </div>

                        <div className="stat-card">
                            <div className="stat-label">Worst Trade</div>
                            <div className="stat-value negative">
                                {stats.worst_trade ? formatMoney(stats.worst_trade) : '-'}
                            </div>
                        </div>

                        <div className="stat-card">
                            <div className="stat-label">Max Consecutive Wins</div>
                            <div className="stat-value">{stats.max_consecutive_wins}</div>
                        </div>

                        <div className="stat-card">
                            <div className="stat-label">Max Consecutive Losses</div>
                            <div className="stat-value">{stats.max_consecutive_losses}</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default AccountTab;
