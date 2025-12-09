import React, { useState } from 'react';
import { Play, RotateCcw, Settings } from 'lucide-react';
import './BacktestConfig.css';

export default function BacktestConfig({ onRunBacktest }) {
    const [config, setConfig] = useState({
        strategy: 'range_4h',
        startDate: '2024-01-01',
        endDate: '2024-11-29',
        initialBalance: 50000,
        riskPerTrade: 0.5,
        minRR: 2.0,
        maxConcurrent: 2,
    });

    const handleChange = (key, value) => {
        setConfig(prev => ({ ...prev, [key]: value }));
    };

    return (
        <div className="backtest-config">
            <div className="config-header">
                <Settings size={18} />
                <h3>Backtest Configuration</h3>
            </div>

            <div className="config-form">
                <div className="form-group">
                    <label>Strategy</label>
                    <select
                        value={config.strategy}
                        onChange={(e) => handleChange('strategy', e.target.value)}
                    >
                        <option value="range_4h">4H Range (V1)</option>
                        <option value="mtf_30_1">MTF 30/1 (V2)</option>
                    </select>
                </div>

                <div className="form-row">
                    <div className="form-group">
                        <label>Start Date</label>
                        <input
                            type="date"
                            value={config.startDate}
                            onChange={(e) => handleChange('startDate', e.target.value)}
                        />
                    </div>
                    <div className="form-group">
                        <label>End Date</label>
                        <input
                            type="date"
                            value={config.endDate}
                            onChange={(e) => handleChange('endDate', e.target.value)}
                        />
                    </div>
                </div>

                <div className="form-row">
                    <div className="form-group">
                        <label>Initial Balance</label>
                        <input
                            type="number"
                            value={config.initialBalance}
                            onChange={(e) => handleChange('initialBalance', Number(e.target.value))}
                        />
                    </div>
                    <div className="form-group">
                        <label>Risk per Trade (%)</label>
                        <input
                            type="number"
                            step="0.1"
                            value={config.riskPerTrade}
                            onChange={(e) => handleChange('riskPerTrade', Number(e.target.value))}
                        />
                    </div>
                </div>

                <div className="form-row">
                    <div className="form-group">
                        <label>Min R:R</label>
                        <input
                            type="number"
                            step="0.1"
                            value={config.minRR}
                            onChange={(e) => handleChange('minRR', Number(e.target.value))}
                        />
                    </div>
                    <div className="form-group">
                        <label>Max Concurrent</label>
                        <input
                            type="number"
                            value={config.maxConcurrent}
                            onChange={(e) => handleChange('maxConcurrent', Number(e.target.value))}
                        />
                    </div>
                </div>

                <div className="config-actions">
                    <button className="btn btn-secondary">
                        <RotateCcw size={16} />
                        Reset
                    </button>
                    <button
                        className="btn btn-primary"
                        onClick={() => onRunBacktest && onRunBacktest(config)}
                    >
                        <Play size={16} />
                        Run Backtest
                    </button>
                </div>
            </div>
        </div>
    );
}
