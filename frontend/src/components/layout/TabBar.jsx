/**
 * Tab navigation bar
 */
import React from 'react';
import '../../styles/TabBar.css';

const TABS = [
    { id: 'chart', label: '📈 Chart', icon: '📈' },
    { id: 'backtest', label: '🎯 Backtest', icon: '🎯' },
    { id: 'journal', label: '📓 Journal', icon: '📓' },
    { id: 'settings', label: '⚙️ Settings', icon: '⚙️' },
];

export default function TabBar({ activeTab, onTabChange }) {
    return (
        <div className="tab-bar">
            {TABS.map((tab) => (
                <button
                    key={tab.id}
                    className={`tab-button ${activeTab === tab.id ? 'active' : ''}`}
                    onClick={() => onTabChange(tab.id)}
                >
                    <span className="tab-icon">{tab.icon}</span>
                    <span className="tab-label">{tab.label.replace(/^.+\s/, '')}</span>
                </button>
            ))}
        </div>
    );
}
