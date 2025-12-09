/**
 * Layout Preset Selector Component
 * 
 * Allows users to switch between predefined layout presets
 */
import React from 'react';
import { LAYOUT_PRESETS } from '../../config/layouts';
import { useSettings } from '../../context/SettingsContext';
import './LayoutPresetSelector.css';

export function LayoutPresetSelector() {
    const { currentPreset, loadPreset, hasCustomModifications } = useSettings();

    return (
        <div className="layout-preset-selector">
            <div className="preset-header">
                <h3>Layout Presets</h3>
                {hasCustomModifications() && (
                    <span className="custom-badge">Custom</span>
                )}
            </div>

            <div className="preset-grid">
                {Object.entries(LAYOUT_PRESETS).map(([key, preset]) => (
                    <button
                        key={key}
                        className={`preset-card ${currentPreset === key ? 'active' : ''}`}
                        onClick={() => loadPreset(key)}
                        title={preset.description}
                    >
                        <div className="preset-icon">
                            {getPresetIcon(key)}
                        </div>
                        <div className="preset-info">
                            <div className="preset-name">{preset.name}</div>
                            <div className="preset-description">{preset.description}</div>
                        </div>
                        {currentPreset === key && (
                            <div className="active-indicator">✓</div>
                        )}
                    </button>
                ))}
            </div>
        </div>
    );
}

function getPresetIcon(presetId) {
    const icons = {
        'range_4h': '📊',
        'mtf_30_1': '🎯',
        'multi_pair': '🌐',
        'minimal': '✨'
    };
    return icons[presetId] || '📐';
}
