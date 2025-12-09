import React from 'react';
import { Box, Layers, TrendingUp, Droplet, Zap } from 'lucide-react';
import { useSettings } from '../../context/SettingsContext';
import './ChartOverlayControls.css';

const overlayOptions = [
    { id: 'signals', icon: Zap, label: 'Signals' },
    { id: 'order_blocks', icon: Box, label: 'Order Blocks' },
    { id: 'liquidity', icon: Droplet, label: 'Liquidity' },
    { id: 'structure', icon: TrendingUp, label: 'Structure' },
    { id: 'fvgs', icon: Layers, label: 'FVGs' },
];

export default function ChartOverlayControls() {
    const { isOverlayEnabled, toggleOverlay } = useSettings();

    return (
        <div className="chart-overlay-controls">
            <div className="controls-header">Overlays</div>
            <div className="controls-list">
                {overlayOptions.map(option => (
                    <label key={option.id} className="control-item">
                        <input
                            type="checkbox"
                            checked={isOverlayEnabled(option.id)}
                            onChange={() => toggleOverlay(option.id)}
                        />
                        <option.icon size={14} />
                        <span>{option.label}</span>
                    </label>
                ))}
            </div>
        </div>
    );
}
