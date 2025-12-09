import React from 'react';
import { TrendingUp, TrendingDown } from 'lucide-react';
import './StatCard.css';

export default function StatCard({ title, value, subtitle, trend, icon: Icon }) {
    const isPositive = trend > 0;

    return (
        <div className="stat-card">
            <div className="stat-card-header">
                <span className="stat-title">{title}</span>
                {Icon && (
                    <div className="stat-icon">
                        <Icon size={18} />
                    </div>
                )}
            </div>
            <div className="stat-value">{value}</div>
            {subtitle && <div className="stat-subtitle">{subtitle}</div>}
            {trend !== undefined && (
                <div className={`stat-trend ${isPositive ? 'positive' : 'negative'}`}>
                    {isPositive ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
                    <span>{Math.abs(trend).toFixed(1)}%</span>
                </div>
            )}
        </div>
    );
}
