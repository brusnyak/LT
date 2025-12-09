import React from 'react';
import { useSettings } from '../../context/SettingsContext';
import { LayoutPresetSelector } from '../settings/LayoutPresetSelector';
import { PanelToggles } from '../settings/PanelToggles';
import { OverlayToggles } from '../settings/OverlayToggles';
import './SettingsTab.css';

const SettingsTab = () => {
    const { resetToDefault, hasCustomModifications } = useSettings();

    return (
        <div className="settings-tab">
            <div className="settings-header">
                <h2>Dashboard Configuration</h2>
                {hasCustomModifications() && (
                    <button
                        className="reset-button"
                        onClick={resetToDefault}
                        title="Reset to default layout"
                    >
                        Reset Defaults
                    </button>
                )}
            </div>

            <div className="settings-section">
                <LayoutPresetSelector />
            </div>

            <div className="settings-grid">
                <div className="settings-column">
                    <PanelToggles />
                </div>
                <div className="settings-column">
                    <OverlayToggles />
                </div>
            </div>

            <div className="settings-section">
                <h3>System Info</h3>
                <div className="info-card">
                    <div className="info-row">
                        <span className="label">Version</span>
                        <span className="value">v2.1.0 (Phase 5)</span>
                    </div>
                    <div className="info-row">
                        <span className="label">Environment</span>
                        <span className="value">Development</span>
                    </div>
                    <div className="info-row">
                        <span className="label">Data Source</span>
                        <span className="value">CSV (100k bars)</span>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default SettingsTab;
