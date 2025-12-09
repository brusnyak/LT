import React from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';
import './EnhancedEquityCurve.css';

export default function EnhancedEquityCurve({
    data = [],
    currentBalance = 50000,
    goal = 100000,
    dailyLossLimit = 48000,
    maxDrawdown = 45000
}) {
    // Use provided data or sample data
    const sampleData = data.length > 0 ? data : [
        { date: 'Start', equity: currentBalance }
    ];

    // Calculate Y-axis domain based on actual data range
    const getYDomain = () => {
        if (sampleData.length === 0) {
            return [currentBalance - 1000, currentBalance + 1000];
        }

        // Find min and max from data
        const values = sampleData.map(d => d.equity);
        const dataMin = Math.min(...values, dailyLossLimit, maxDrawdown);
        const dataMax = Math.max(...values, goal);

        // Add 5% buffer on each side
        const buffer = (dataMax - dataMin) * 0.05;

        return [
            Math.floor((dataMin - buffer) / 100) * 100, // Round to nearest 100
            Math.ceil((dataMax + buffer) / 100) * 100
        ];
    };

    const customTooltip = ({ active, payload }) => {
        if (active && payload && payload.length) {
            const value = payload[0].value;
            const startingBalance = sampleData[0]?.equity || currentBalance;
            const change = value - startingBalance;
            const changePercent = ((change / startingBalance) * 100).toFixed(2);

            return (
                <div className="enhanced-tooltip">
                    <p className="tooltip-date">{payload[0].payload.date}</p>
                    <p className="tooltip-balance">${value.toLocaleString()}</p>
                    <p className={`tooltip-change ${change >= 0 ? 'positive' : 'negative'}`}>
                        {change >= 0 ? '+' : ''}{change.toLocaleString()} ({changePercent}%)
                    </p>
                </div>
            );
        }
        return null;
    };

    const [yMin, yMax] = getYDomain();

    return (
        <div className="enhanced-equity-curve">
            <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={sampleData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
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
                        domain={[yMin, yMax]}
                        stroke="#787b86"
                        style={{ fontSize: '12px' }}
                        tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`}
                    />
                    <Tooltip content={customTooltip} />

                    {/* Goal Line */}
                    <ReferenceLine
                        y={goal}
                        stroke="#26a69a"
                        strokeDasharray="5 5"
                        strokeWidth={2}
                        label={{
                            value: `Goal: $${(goal / 1000).toFixed(0)}k`,
                            position: 'right',
                            fill: '#26a69a',
                            fontSize: 12
                        }}
                    />

                    {/* Daily Loss Limit */}
                    <ReferenceLine
                        y={dailyLossLimit}
                        stroke="#ff9800"
                        strokeDasharray="5 5"
                        strokeWidth={2}
                        label={{
                            value: `Daily Loss Limit`,
                            position: 'right',
                            fill: '#ff9800',
                            fontSize: 12
                        }}
                    />

                    {/* Max Drawdown */}
                    <ReferenceLine
                        y={maxDrawdown}
                        stroke="#ef5350"
                        strokeDasharray="5 5"
                        strokeWidth={2}
                        label={{
                            value: `Max DD: $${(maxDrawdown / 1000).toFixed(0)}k`,
                            position: 'right',
                            fill: '#ef5350',
                            fontSize: 12
                        }}
                    />

                    <Area
                        type="monotone"
                        dataKey="equity"
                        stroke="#2962ff"
                        strokeWidth={3}
                        fill="url(#equityGradient)"
                    />
                </AreaChart>
            </ResponsiveContainer>
        </div>
    );
}
