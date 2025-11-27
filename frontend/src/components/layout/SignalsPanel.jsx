/**
 * SignalsPanel Component
 * Displays signals/positions in the right panel
 */
import React from 'react';
import './SignalsPanel.css';

function SignalsPanel({ signals }) {
    if (!signals || signals.length === 0) {
        return (
            <div className="signals-panel">
                <div className="panel-header">Signals</div>
                <div className="panel-content">
                    <div className="signal-item">No signals</div>
                </div>
            </div>
        );
    }

    const formatPrice = (price) => price ? price.toFixed(5) : '-';
    const formatTime = (time) => {
        const date = new Date(time);
        return date.toLocaleString('en-US', {
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    const getRR = (signal) => {
        const risk = Math.abs(signal.price - signal.sl);
        const reward = Math.abs(signal.tp - signal.price);
        return (reward / risk).toFixed(1);
    };

    return (
        <div className="signals-panel">
            <div className="panel-header">
                Signals ({signals.length})
            </div>
            <div className="panel-content">
                {signals.map((signal, index) => (
                    <div 
                        key={index} 
                        className={`signal-card ${signal.type.toLowerCase()} ${signal.status.toLowerCase()}`}
                    >
                        <div className="signal-type-badge">
                            {signal.type}
                        </div>
                        <div className="signal-details">
                            <div className="signal-row">
                                <span className="label">Entry:</span>
                                <span className="value">{formatPrice(signal.price)}</span>
                            </div>
                            <div className="signal-row">
                                <span className="label">SL:</span>
                                <span className="value sl">{formatPrice(signal.sl)}</span>
                            </div>
                            <div className="signal-row">
                                <span className="label">TP:</span>
                                <span className="value tp">{formatPrice(signal.tp)}</span>
                            </div>
                            <div className="signal-row">
                                <span className="label">RR:</span>
                                <span className="value">1:{getRR(signal)}</span>
                            </div>
                            <div className="signal-row">
                                <span className="label">Status:</span>
                                <span className={`value status-${signal.status.toLowerCase()}`}>
                                    {signal.status}
                                    {signal.outcome && ` (${signal.outcome})`}
                                </span>
                            </div>
                            <div className="signal-time">
                                {formatTime(signal.time)}
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}

export default SignalsPanel;
