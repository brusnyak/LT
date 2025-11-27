/**
 * Settings Tab Component
 * Configure journal and strategy settings
 */
import React, { useState } from 'react';
import './SettingsTab.css';

function SettingsTab({ settings, onSettingsChange }) {
    // Initialize from props or localStorage or defaults
    const [localSettings, setLocalSettings] = useState(() => {
        const saved = localStorage.getItem('smc_settings');
        if (saved) {
            return JSON.parse(saved);
        }
        return settings || {
            startingBalance: 50000,
            riskPercent: 0.5,
            targetRR: 2.0,
            timezone: 'UTC+1',
            showPositions: true
        };
    });

    const handleChange = (key, value) => {
        const updated = { ...localSettings, [key]: value };
        setLocalSettings(updated);
    };

    const handleSave = () => {
        localStorage.setItem('smc_settings', JSON.stringify(localSettings));
        if (onSettingsChange) {
            onSettingsChange(localSettings);
        }
        alert('Settings saved!');
    };

    return (
        <div className="settings-tab">
            <div className="tab-header">
                <h2>⚙️ Settings</h2>
            </div>
            <div className="tab-content">
                <div className="settings-section">
                    <h3>Account Configuration</h3>
                    <div className="setting-item">
                        <label>
                            Starting Balance ($)
                            <input
                                type="number"
                                value={localSettings.startingBalance}
                                onChange={(e) => handleChange('startingBalance', Number(e.target.value))}
                                min="1000"
                                step="1000"
                            />
                        </label>
                        <p className="setting-description">
                            Initial account balance for simulated trading
                        </p>
                    </div>

                    <div className="setting-item">
                        <label>
                            Risk Per Trade (%)
                            <input
                                type="number"
                                value={localSettings.riskPercent}
                                onChange={(e) => handleChange('riskPercent', Number(e.target.value))}
                                min="0.1"
                                max="5"
                                step="0.1"
                            />
                        </label>
                        <p className="setting-description">
                            Percentage of account balance to risk on each trade
                        </p>
                    </div>
                </div>

                <div className="settings-section">
                    <h3>Strategy Configuration</h3>
                    <div className="setting-item">
                        <label>
                            Target Risk-Reward (R)
                            <input
                                type="number"
                                value={localSettings.targetRR}
                                onChange={(e) => handleChange('targetRR', Number(e.target.value))}
                                min="1"
                                max="10"
                                step="0.5"
                            />
                        </label>
                        <p className="setting-description">
                            Target reward multiple (e.g., 2R = 2x risk)
                        </p>
                    </div>

                    <div className="setting-item">
                        <label>
                            Timezone
                            <select
                                value={localSettings.timezone}
                                onChange={(e) => handleChange('timezone', e.target.value)}
                            >
                                <option value="UTC">UTC</option>
                                <option value="UTC+1">UTC+1 (Frankfurt)</option>
                                <option value="UTC-5">UTC-5 (New York)</option>
                                <option value="UTC+8">UTC+8 (Singapore)</option>
                            </select>
                        </label>
                        <p className="setting-description">
                            Timezone for 4H range detection (currently: UTC+1)
                        </p>
                    </div>
                </div>

                <div className="settings-section">
                    <h3>Display Preferences</h3>
                    <div className="setting-item">
                        <label className="checkbox-label">
                            <input
                                type="checkbox"
                                checked={localSettings.showPositions !== false}
                                onChange={(e) => handleChange('showPositions', e.target.checked)}
                            />
                            Show Position Visualization
                        </label>
                        <p className="setting-description">
                            Display entry/SL/TP lines on charts
                        </p>
                    </div>
                </div>

                <div className="settings-actions">
                    <button className="btn-primary" onClick={handleSave}>
                        Save Settings
                    </button>
                    <button 
                        className="btn-secondary" 
                        onClick={() => setLocalSettings({
                            startingBalance: 50000,
                            riskPercent: 0.5,
                            targetRR: 2.0,
                            timezone: 'UTC+1'
                        })}
                    >
                        Reset to Defaults
                    </button>
                </div>
            </div>
        </div>
    );
}

export default SettingsTab;
