/**
 * Top navigation bar with pair selector and timeframe switcher
 */
import React from 'react';
import '../../styles/TopBar.css';

const TIMEFRAMES = ['M5', 'M15', 'M30', 'H1', 'H4', 'D1'];

export default function TopBar({ pair, timeframe, onPairChange, onTimeframeChange }) {
    return (
        <div className="top-bar">
            <div className="top-bar-left">
                <select
                    className="pair-selector"
                    value={pair}
                    onChange={(e) => onPairChange(e.target.value)}
                >
                    <option value="EURUSD">EURUSD</option>
                    <option value="GBPUSD">GBPUSD</option>
                    <option value="GBPJPY">GBPJPY</option>
                </select>
            </div>

            <div className="timeframe-switcher">
                {TIMEFRAMES.map((tf) => (
                    <button
                        key={tf}
                        className={`tf-button ${timeframe === tf ? 'active' : ''}`}
                        onClick={() => onTimeframeChange(tf)}
                    >
                        {tf}
                    </button>
                ))}
            </div>

            <div className="top-bar-right">
                {/* Starred tools will go here */}
                <div className="starred-tools">
                    <button title="Trend Line">📏</button>
                    <button title="Horizontal Line">──</button>
                    <button title="Rectangle">▭</button>
                </div>
            </div>
        </div>
    );
}
