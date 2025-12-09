import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
    LineChart,
    BookOpen,
    FlaskConical,
    ArrowRight,
    TrendingUp,
    Activity
} from 'lucide-react';
import { fetchStatsSummary } from '../services/api';
import './Home.css';

export default function Home() {
    const [stats, setStats] = useState({
        win_rate: 0,
        avg_rr: 0,
        total_trades: 0
    });
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const loadStats = async () => {
            try {
                const data = await fetchStatsSummary();
                setStats(data);
            } catch (error) {
                console.error('Failed to load stats:', error);
            } finally {
                setLoading(false);
            }
        };
        loadStats();
    }, []);

    return (
        <div className="home-container">
            {/* Hero Section */}
            <section className="hero-section">
                <div className="hero-content">
                    <h1 className="hero-title">
                        Professional <span className="text-accent">SMC</span> Trading Environment
                    </h1>
                    <p className="hero-subtitle">
                        Institutional-grade analysis, automated journal, and advanced backtesting.
                        All in one platform.
                    </p>
                    <div className="hero-actions">
                        <Link to="/trade" className="btn btn-primary btn-lg">
                            Resume Trading <ArrowRight size={20} />
                        </Link>
                        <Link to="/journal" className="btn btn-secondary btn-lg">
                            View Journal
                        </Link>
                    </div>
                </div>
            </section>

            {/* Quick Stats (Dashboard Element) */}
            <section className="stats-section">
                <div className="stat-card">
                    <div className="stat-icon"><TrendingUp size={24} /></div>
                    <div className="stat-info">
                        <span className="stat-label">Win Rate</span>
                        <span className="stat-value">
                            {loading ? '...' : `${stats.win_rate.toFixed(1)}%`}
                        </span>
                    </div>
                </div>
                <div className="stat-card">
                    <div className="stat-icon"><Activity size={24} /></div>
                    <div className="stat-info">
                        <span className="stat-label">Avg R:R</span>
                        <span className="stat-value">
                            {loading ? '...' : stats.avg_rr.toFixed(1)}
                        </span>
                    </div>
                </div>
                <div className="stat-card">
                    <div className="stat-icon"><LineChart size={24} /></div>
                    <div className="stat-info">
                        <span className="stat-label">Trades (MTD)</span>
                        <span className="stat-value">
                            {loading ? '...' : stats.total_trades}
                        </span>
                    </div>
                </div>
            </section>

            {/* Feature Grid */}
            <section className="features-section">
                <Link to="/trade" className="feature-card">
                    <div className="feature-icon"><LineChart size={32} /></div>
                    <h3>Smart Analysis</h3>
                    <p>Real-time SMC structure, order blocks, and liquidity zones detection.</p>
                </Link>

                <Link to="/journal" className="feature-card">
                    <div className="feature-icon"><BookOpen size={32} /></div>
                    <h3>Automated Journal</h3>
                    <p>Track every trade with automated metrics and performance insights.</p>
                </Link>

                <Link to="/backtest" className="feature-card">
                    <div className="feature-icon"><FlaskConical size={32} /></div>
                    <h3>Backtest Engine</h3>
                    <p>Validate strategies with historical data and instant replay.</p>
                </Link>
            </section>
        </div>
    );
}
