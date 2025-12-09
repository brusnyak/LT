import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart, ReferenceLine } from 'recharts';
import './EquityCurve.css';

export default function EquityCurve({ data = [] }) {
    // Sample data structure if empty
    const sampleData = data.length > 0 ? data : [
        { date: 'Day 1', equity: 50000 },
        { date: 'Day 2', equity: 50200 },
        { date: 'Day 3', equity: 50800 },
        { date: 'Day 4', equity: 51200 },
        { date: 'Day 5', equity: 52000 },
    ];

    const customTooltip = ({ active, payload }) => {
        if (active && payload && payload.length) {
            return (
                <div className="custom-tooltip">
                    <p className="tooltip-label">{payload[0].payload.date}</p>
                    <p className="tooltip-value">
                        ${payload[0].value.toLocaleString()}
                    </p>
                </div>
            );
        }
        return null;
    };

    return (
        <div className="equity-curve">
            <div className="chart-header">
                <h3>Equity Curve</h3>
                <span className="chart-subtitle">Account Balance Over Time</span>
            </div>
            <ResponsiveContainer width="100%" height={300}>
                <AreaChart data={sampleData}>
                    <defs>
                        <linearGradient id="equityGradient" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#2962ff" stopOpacity={0.3} />
                            <stop offset="95%" stopColor="#2962ff" stopOpacity={0} />
                        </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#2a2e39" />
                    <XAxis
                        dataKey="date"
                        stroke="#787b86"
                        style={{ fontSize: '12px' }}
                    />
                    <YAxis
                        stroke="#787b86"
                        style={{ fontSize: '12px' }}
                        tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`}
                    />
                    <Tooltip content={customTooltip} />
                    <Area
                        type="monotone"
                        dataKey="equity"
                        stroke="#2962ff"
                        strokeWidth={2}
                        fill="url(#equityGradient)"
                    />
                    <ReferenceLine y={54000} label="Profit Target" stroke="#00c853" strokeDasharray="3 3" />
                    <ReferenceLine y={44000} label="Max DD" stroke="#ff1744" strokeDasharray="3 3" />
                </AreaChart>
            </ResponsiveContainer>
        </div>
    );
}
