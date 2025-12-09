import React, { useState } from 'react';
import { Palette, Layout, Database, Monitor } from 'lucide-react';
import { useTheme } from '../context/ThemeContext';
import './SettingsPage.css';

export default function SettingsPage() {
    const { theme, toggleTheme, palette, setPalette } = useTheme();
    const [settings, setSettings] = useState({
        dataSource: 'csv',
        chartStyle: 'candlestick',
        defaultTimeframe: '5M',
        layoutPreset: 'default',
    });

    return (
        <div className="settings-page">
            {/* Theme Settings */}
            <div className="settings-section">
                <div className="section-header">
                    <Palette size={20} />
                    <h3>Theme & Appearance</h3>
                </div>

                <div className="setting-item">
                    <label>Color Scheme</label>
                    <div className="theme-options">
                        <button
                            className={`theme-btn ${theme === 'dark' ? 'active' : ''}`}
                            onClick={toggleTheme}
                        >
                            Dark Mode
                        </button>
                        <button
                            className={`theme-btn ${theme === 'light' ? 'active' : ''}`}
                            onClick={toggleTheme}
                        >
                            Light Mode
                        </button>
                    </div>
                </div>

                <div className="setting-item">
                    <label>Color Palette</label>
                    <select value={palette} onChange={(e) => setPalette(e.target.value)}>
                        <option value="default">Default (Blue)</option>
                        <option value="ocean">Ocean (Teal)</option>
                        <option value="midnight">Midnight (Purple)</option>
                        <option value="forest">Forest (Green)</option>
                    </select>
                </div>
            </div>

            {/* Layout Settings */}
            <div className="settings-section">
                <div className="section-header">
                    <Layout size={20} />
                    <h3>Layout Preferences</h3>
                </div>

                <div className="setting-item">
                    <label>Default Layout Preset</label>
                    <select
                        value={settings.layoutPreset}
                        onChange={(e) => setSettings({ ...settings, layoutPreset: e.target.value })}
                    >
                        <option value="default">Default</option>
                        <option value="focus">Focus (Chart Only)</option>
                        <option value="analysis">Analysis (Chart + Signals)</option>
                    </select>
                </div>

                <div className="setting-item">
                    <label>Panel Positions</label>
                    <div className="toggle-group">
                        <label className="toggle-item">
                            <input type="checkbox" defaultChecked />
                            <span>Show Left Toolbar</span>
                        </label>
                        <label className="toggle-item">
                            <input type="checkbox" defaultChecked />
                            <span>Show Signals Panel</span>
                        </label>
                        <label className="toggle-item">
                            <input type="checkbox" defaultChecked />
                            <span>Show Floating Toolbar</span>
                        </label>
                    </div>
                </div>
            </div>

            {/* Data Source */}
            <div className="settings-section">
                <div className="section-header">
                    <Database size={20} />
                    <h3>Data Source</h3>
                </div>

                <div className="setting-item">
                    <label>Primary Data Source</label>
                    <div className="radio-group">
                        <label className="radio-item">
                            <input
                                type="radio"
                                name="dataSource"
                                value="csv"
                                checked={settings.dataSource === 'csv'}
                                onChange={(e) => setSettings({ ...settings, dataSource: e.target.value })}
                            />
                            <span>CSV Files (Local)</span>
                        </label>
                        <label className="radio-item">
                            <input
                                type="radio"
                                name="dataSource"
                                value="ctrader"
                                checked={settings.dataSource === 'ctrader'}
                                onChange={(e) => setSettings({ ...settings, dataSource: e.target.value })}
                            />
                            <span>cTrader API (Live)</span>
                        </label>
                    </div>
                </div>
            </div>

            {/* Display Preferences */}
            <div className="settings-section">
                <div className="section-header">
                    <Monitor size={20} />
                    <h3>Display Preferences</h3>
                </div>

                <div className="setting-item">
                    <label>Chart Style</label>
                    <select
                        value={settings.chartStyle}
                        onChange={(e) => setSettings({ ...settings, chartStyle: e.target.value })}
                    >
                        <option value="candlestick">Candlestick</option>
                        <option value="line">Line</option>
                        <option value="area">Area</option>
                    </select>
                </div>

                <div className="setting-item">
                    <label>Default Timeframe</label>
                    <select
                        value={settings.defaultTimeframe}
                        onChange={(e) => setSettings({ ...settings, defaultTimeframe: e.target.value })}
                    >
                        <option value="1M">1 Minute</option>
                        <option value="5M">5 Minutes</option>
                        <option value="15M">15 Minutes</option>
                        <option value="1H">1 Hour</option>
                        <option value="4H">4 Hours</option>
                        <option value="D">Daily</option>
                    </select>
                </div>
            </div>

            <button className="btn btn-primary">Save Settings</button>
        </div>
    );
}
