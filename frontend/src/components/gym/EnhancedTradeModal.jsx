import React, { useState } from 'react';
import { CheckCircle, XCircle, MinusCircle, Camera } from 'lucide-react';
import { formatPrice, formatRR } from '../../utils/pairFormatting';
import './EnhancedTradeModal.css';

/**
 * Enhanced trade confirmation modal
 * Shows trade details, outcome selection, notes, and screenshot preview
 */
export default function EnhancedTradeModal({
    trade,
    pair,
    onConfirm,
    onCancel,
    onScreenshot
}) {
    const [notes, setNotes] = useState('');
    const [screenshotTaken, setScreenshotTaken] = useState(false);

    const handleScreenshot = async () => {
        if (onScreenshot) {
            await onScreenshot();
            setScreenshotTaken(true);
        }
    };

    const handleConfirm = () => {
        onConfirm({
            ...trade,
            notes: notes.trim() || null
        });
    };

    // Calculate duration
    const duration = trade.exitTime && trade.entryTime
        ? Math.round((new Date(trade.exitTime) - new Date(trade.entryTime)) / 1000 / 60)
        : 0;

    const hours = Math.floor(duration / 60);
    const minutes = duration % 60;
    const durationStr = hours > 0 ? `${hours}h ${minutes}m` : `${minutes}m`;

    return (
        <div className="modal-overlay" onClick={onCancel}>
            <div className="enhanced-trade-modal" onClick={(e) => e.stopPropagation()}>
                <div className="modal-header">
                    <h3>Confirm Trade</h3>
                    <button className="modal-close" onClick={onCancel}>×</button>
                </div>

                <div className="modal-body">
                    {/* Trade Type Badge */}
                    <div className={`trade-type-badge ${trade.type.toLowerCase()}`}>
                        {trade.type}
                    </div>

                    {/* Trade Details */}
                    <div className="trade-details-grid">
                        <div className="detail-group">
                            <label>Entry</label>
                            <div className="detail-value">
                                {formatPrice(trade.entry, pair)}
                                <span className="detail-time">
                                    {new Date(trade.entryTime).toLocaleString()}
                                </span>
                            </div>
                        </div>

                        <div className="detail-group">
                            <label>Exit</label>
                            <div className="detail-value">
                                {formatPrice(trade.exit, pair)}
                                <span className="detail-time">
                                    {new Date(trade.exitTime).toLocaleString()}
                                </span>
                            </div>
                        </div>

                        <div className="detail-group">
                            <label>Stop Loss</label>
                            <div className="detail-value">{formatPrice(trade.sl, pair)}</div>
                        </div>

                        <div className="detail-group">
                            <label>Take Profit</label>
                            <div className="detail-value">{formatPrice(trade.tp, pair)}</div>
                        </div>

                        <div className="detail-group">
                            <label>Duration</label>
                            <div className="detail-value">{durationStr}</div>
                        </div>

                        <div className="detail-group">
                            <label>R:R Ratio</label>
                            <div className="detail-value">1:{formatRR(trade.rr)}</div>
                        </div>
                    </div>

                    {/* Outcome Display */}
                    <div className="outcome-section">
                        <label>Outcome (Auto-detected)</label>
                        <div className={`outcome-badge ${trade.outcome.toLowerCase()}`}>
                            {trade.outcome === 'WIN' && <CheckCircle size={20} />}
                            {trade.outcome === 'LOSS' && <XCircle size={20} />}
                            {trade.outcome === 'BE' && <MinusCircle size={20} />}
                            <span>{trade.outcome}</span>
                        </div>
                        <div className={`pnl-display ${trade.pnl >= 0 ? 'positive' : 'negative'}`}>
                            PnL: {trade.pnl >= 0 ? '+' : ''}{formatPrice(trade.pnl, pair)}
                        </div>
                    </div>

                    {/* Notes */}
                    <div className="notes-section">
                        <label>Notes (Optional)</label>
                        <textarea
                            placeholder="Describe your trading logic, setup, or key observations..."
                            value={notes}
                            onChange={(e) => setNotes(e.target.value)}
                            rows={4}
                        />
                    </div>

                    {/* Screenshot */}
                    <div className="screenshot-section">
                        <button
                            className={`screenshot-btn ${screenshotTaken ? 'taken' : ''}`}
                            onClick={handleScreenshot}
                        >
                            <Camera size={18} />
                            {screenshotTaken ? 'Screenshot Captured ✓' : 'Take Screenshot'}
                        </button>
                        {screenshotTaken && (
                            <span className="screenshot-hint">
                                Screenshot will be saved with trade
                            </span>
                        )}
                    </div>
                </div>

                <div className="modal-footer">
                    <button className="btn-cancel" onClick={onCancel}>
                        Cancel
                    </button>
                    <button className="btn-confirm" onClick={handleConfirm}>
                        Save Trade
                    </button>
                </div>
            </div>
        </div>
    );
}
