import React, { useState } from 'react';
import {
    MousePointer,
    TrendingUp,
    Minus,
    Square,
    Type,
    Trash2,
    MoreHorizontal
} from 'lucide-react';
import './GymTopBar.css';

/**
 * Universal Top Toolbar component.
 * Contains Timeframe selector, Pair selector, and Drawing Tools.
 */
export default function GymTopBar({
    timeframe,
    setTimeframe,
    pair,
    setPair,
    availablePairs,
    activeTool,
    onToolSelect,
    onStartSession,
    onEndSession,
    sessionName,
    disabled
}) {
    const drawingTools = [
        { id: 'cursor', icon: MousePointer, label: 'Cursor' },
        { id: 'trendline', icon: TrendingUp, label: 'Trendline' },
        { id: 'fib', icon: Minus, label: 'Fib Retracement' }, // Using Minus as placeholder
        { id: 'rect', icon: Square, label: 'Rectangle' },
        { id: 'text', icon: Type, label: 'Text' },
    ];

    return (
        <div className="gym-top-bar">
            {/* Left: Navigation & Controls */}
            <div className="gym-controls-group">
                <div className="pair-info">
                    <select
                        value={pair}
                        onChange={(e) => setPair(e.target.value)}
                        className="pair-select-minimal"
                        disabled={!!sessionName}
                    >
                        {availablePairs.map(p => (
                            <option key={p.value} value={p.value}>{p.label}</option>
                        ))}
                    </select>
                </div>

                <div className="timeframe-list">
                    {['M1', 'M5', 'M15', 'H1', 'H4', 'D'].map(tf => (
                        <button
                            key={tf}
                            className={`tf-item ${timeframe === tf ? 'active' : ''}`}
                            onClick={() => setTimeframe(tf)}
                        >
                            {tf}
                        </button>
                    ))}
                </div>
            </div>

            <div className="divider-vertical" />

            {/* Right: Session Controls */}
            <div className="gym-session-controls">
                {!sessionName ? (
                    <button className="btn-start-session" onClick={onStartSession}>
                        Start Session
                    </button>
                ) : (
                    <div className="session-active-controls">
                        <span className="session-status-badge">
                            {sessionName}
                        </span>
                        <button className="btn-end-session" onClick={() => window.confirm('End Session?') && onEndSession()}>
                            {/* Assuming onStartSession(null) or similar logic - wait, I need a callback for ending. 
                                The existing prop is onStartSession. 
                                I should check GymPage to see if startSession handles toggle or if I need `onEndSession`.
                                For now, I'll add `onEndSession` to props and usage.
                            */}
                            End
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
}
