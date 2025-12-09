/**
 * Panel Toggles Component
 * 
 * Show/hide individual dashboard panels
 */
import React from 'react';
import { PANEL_CONFIG } from '../../config/layouts';
import { useSettings } from '../../context/SettingsContext';
import './PanelToggles.css';

export function PanelToggles() {
    const { currentLayout, togglePanel, isPanelVisible } = useSettings();

    const panels = Object.entries(currentLayout.panels || {});

    return (
        <div className="panel-toggles">
            <h3>Visible Panels</h3>
            <div className="toggle-list">
                {panels.map(([name, config]) => {
                    const panelInfo = PANEL_CONFIG[name] || {
                        name: formatPanelName(name),
                        icon: '📄',
                        description: ''
                    };

                    return (
                        <label key={name} className="toggle-item">
                            <div className="toggle-info">
                                <span className="toggle-icon">{panelInfo.icon}</span>
                                <div className="toggle-text">
                                    <span className="toggle-label">{panelInfo.name}</span>
                                    {panelInfo.description && (
                                        <span className="toggle-description">{panelInfo.description}</span>
                                    )}
                                </div>
                            </div>
                            <input
                                type="checkbox"
                                className="toggle-checkbox"
                                checked={isPanelVisible(name)}
                                onChange={() => togglePanel(name)}
                            />
                            <span className="toggle-slider"></span>
                        </label>
                    );
                })}
            </div>
        </div>
    );
}

function formatPanelName(name) {
    return name
        .replace(/_/g, ' ')
        .replace(/\b\w/g, l => l.toUpperCase());
}
