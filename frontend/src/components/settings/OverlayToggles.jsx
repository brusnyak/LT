/**
 * Overlay Toggles Component
 * 
 * Show/hide chart overlays (Order Blocks, Liquidity, etc.)
 */
import React from 'react';
import { OVERLAY_CONFIG } from '../../config/layouts';
import { useSettings } from '../../context/SettingsContext';
import './OverlayToggles.css';

export function OverlayToggles() {
    const { currentLayout, toggleOverlay, isOverlayEnabled } = useSettings();

    const overlays = Object.entries(currentLayout.overlays || {});

    return (
        <div className="overlay-toggles">
            <h3>Chart Overlays</h3>
            <div className="overlay-grid">
                {overlays.map(([name, enabled]) => {
                    const config = OVERLAY_CONFIG[name] || {
                        name: formatOverlayName(name),
                        icon: '•',
                        color: '#888',
                        description: ''
                    };

                    const isEnabled = isOverlayEnabled(name);

                    return (
                        <button
                            key={name}
                            className={`overlay-card ${isEnabled ? 'active' : ''}`}
                            onClick={() => toggleOverlay(name)}
                            style={{ '--overlay-color': config.color }}
                            title={config.description}
                        >
                            <div className="overlay-icon-wrapper">
                                <span className="overlay-icon">{config.icon}</span>
                            </div>
                            <span className="overlay-name">{config.name}</span>
                            <div className="overlay-status">
                                {isEnabled ? 'ON' : 'OFF'}
                            </div>
                        </button>
                    );
                })}
            </div>
        </div>
    );
}

function formatOverlayName(name) {
    return name
        .replace(/_/g, ' ')
        .replace(/\b\w/g, l => l.toUpperCase());
}
