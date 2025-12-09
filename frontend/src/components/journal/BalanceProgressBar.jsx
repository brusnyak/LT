import React from 'react';
import './BalanceProgressBar.css';

export default function BalanceProgressBar({ currentBalance = 50000, goal = 100000 }) {
    const startingBalance = goal / 1.08; // Assume 8% target, calculate starting balance
    const profitTarget = goal - startingBalance;
    const currentProfit = currentBalance - startingBalance;
    const profitProgress = Math.max(0, Math.min(100, (currentProfit / profitTarget) * 100));

    // Calculate tight range around current balance for visual display
    const range = {
        min: startingBalance,
        max: goal,
    };

    const visualProgress = ((currentBalance - range.min) / (range.max - range.min)) * 100;

    const formatCurrency = (value) => {
        if (value >= 1000000) return `$${(value / 1000000).toFixed(1)}M`;
        if (value >= 1000) return `$${(value / 1000).toFixed(1)}k`;
        return `$${value}`;
    };

    // Generate markers between starting balance and goal
    const numMarkers = 9;
    const markers = [];
    for (let i = 0; i <= numMarkers; i++) {
        const value = range.min + (range.max - range.min) * (i / numMarkers);
        markers.push(Math.round(value / 100) * 100); // Round to nearest 100
    }

    return (
        <div className="balance-progress-bar">
            <div className="progress-header">
                <div className="current-balance">
                    <span className="label">Current Balance</span>
                    <span className="value">${currentBalance.toLocaleString()}</span>
                </div>
                <div className="goal-info">
                    <span className="label">Goal</span>
                    <span className="value">${goal.toLocaleString()}</span>
                </div>
            </div>

            <div className="progress-track">
                <div className="progress-bar-container">
                    <div className="progress-bar-bg">
                        <div
                            className="progress-bar-fill"
                            style={{ width: `${visualProgress}%` }}
                        >
                            <div className="progress-indicator">
                                <div className="indicator-dot"></div>
                                <div className="indicator-label">
                                    ${currentBalance.toLocaleString()}
                                </div>
                            </div>
                        </div>
                    </div>
                    <div className="progress-markers">
                        {markers.map((marker) => (
                            <div
                                key={marker}
                                className={`marker ${Math.abs(marker - currentBalance) < 100 ? 'current' : ''}`}
                                style={{ left: `${((marker - range.min) / (range.max - range.min)) * 100}%` }}
                            >
                                <div className="marker-dot"></div>
                                <span className="marker-label">{formatCurrency(marker)}</span>
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            <div className="progress-stats">
                <div className="stat">
                    <span className="stat-label">Profit Progress</span>
                    <span className="stat-value">{profitProgress.toFixed(1)}%</span>
                </div>
                <div className="stat">
                    <span className="stat-label">Remaining</span>
                    <span className="stat-value">${Math.max(0, goal - currentBalance).toLocaleString()}</span>
                </div>
            </div>
        </div>
    );
}
