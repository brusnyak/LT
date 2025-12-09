import React from 'react';
import './ConfirmTradeModal.css';

export default function ConfirmTradeModal({ trade, onConfirm, onCancel }) {
    if (!trade) return null;

    const risk = Math.abs(trade.entry - trade.sl);
    const reward = Math.abs(trade.tp - trade.entry);
    const rr = (reward / risk).toFixed(2);

    return (
        <div className="modal-overlay" onClick={onCancel}>
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
                <div className="modal-header">
                    <h3>Confirm Trade</h3>
                    <button className="modal-close" onClick={onCancel}>×</button>
                </div>

                <div className="modal-body">
                    <div className={`trade-type-badge ${trade.type.toLowerCase()}`}>
                        {trade.type}
                    </div>

                    <div className="trade-details">
                        <div className="detail-row">
                            <span className="label">Entry:</span>
                            <span className="value">{trade.entry.toFixed(5)}</span>
                        </div>
                        <div className="detail-row">
                            <span className="label">Stop Loss:</span>
                            <span className="value">{trade.sl.toFixed(5)}</span>
                        </div>
                        <div className="detail-row">
                            <span className="label">Take Profit:</span>
                            <span className="value">{trade.tp.toFixed(5)}</span>
                        </div>
                        <div className="detail-row highlight">
                            <span className="label">Risk:Reward:</span>
                            <span className="value">1:{rr}</span>
                        </div>
                        <div className="detail-row">
                            <span className="label">Entry Time:</span>
                            <span className="value time">
                                {new Date(trade.entryTime).toLocaleString()}
                            </span>
                        </div>
                        {trade.exitTime && (
                            <div className="detail-row">
                                <span className="label">Exit Time:</span>
                                <span className="value time">
                                    {new Date(trade.exitTime).toLocaleString()}
                                </span>
                            </div>
                        )}
                    </div>
                </div>

                <div className="modal-footer">
                    <button className="btn-cancel" onClick={onCancel}>
                        Cancel
                    </button>
                    <button className="btn-confirm" onClick={onConfirm}>
                        Confirm Trade
                    </button>
                </div>
            </div>
        </div>
    );
}
