/**
 * SMC Controls panel for toggling analysis overlays
 */
import React from 'react';
import '../../styles/SMCControls.css';

export default function SMCControls({ smcToggles, onToggleChange }) {
    const handleToggle = (key) => {
        onToggleChange({ ...smcToggles, [key]: !smcToggles[key] });
    };

    return (
        <div className="smc-controls">
            <div className="smc-controls-header">SMC Analysis</div>
            <div className="smc-controls-list">
                <label className="smc-control-item">
                    <input
                        type="checkbox"
                        checked={smcToggles.showSwings}
                        onChange={() => handleToggle('showSwings')}
                    />
                    <span>Swing Points</span>
                </label>

                <label className="smc-control-item">
                    <input
                        type="checkbox"
                        checked={smcToggles.showStructure}
                        onChange={() => handleToggle('showStructure')}
                    />
                    <span>Market Structure</span>
                </label>

                <label className="smc-control-item">
                    <input
                        type="checkbox"
                        checked={smcToggles.showOrderBlocks}
                        onChange={() => handleToggle('showOrderBlocks')}
                    />
                    <span>Order Blocks</span>
                </label>

                <label className="smc-control-item">
                    <input
                        type="checkbox"
                        checked={smcToggles.showFVG}
                        onChange={() => handleToggle('showFVG')}
                    />
                    <span>Fair Value Gaps</span>
                </label>

                <label className="smc-control-item">
                    <input
                        type="checkbox"
                        checked={smcToggles.showLiquidity}
                        onChange={() => handleToggle('showLiquidity')}
                    />
                    <span>Liquidity Zones</span>
                </label>
            </div>
        </div>
    );
}
