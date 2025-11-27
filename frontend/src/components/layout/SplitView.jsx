/**
 * SplitView Component
 * Displays two synchronized charts (4H and 5M)
 */
import React from 'react';
import TradingViewChart from '../chart/TradingViewChart';
import './SplitView.css';

function SplitView({ 
    data4H, 
    data5M, 
    pair, 
    ranges, 
    signals,
    showPositions = true
}) {
    return (
        <div className="split-view">
            <div className="split-view-top">
                <div className="chart-label">4H - Context</div>
                <TradingViewChart
                    data={data4H}
                    pair={pair}
                    ranges={ranges}
                    signals={signals}
                    timeframe="4H"
                    showPositions={showPositions}
                />
            </div>
            <div className="split-view-bottom">
                <div className="chart-label">5M - Execution</div>
                <TradingViewChart
                    data={data5M}
                    pair={pair}
                    ranges={ranges}
                    signals={signals}
                    timeframe="5M"
                    showPositions={showPositions}
                />
            </div>
        </div>
    );
}

export default SplitView;
