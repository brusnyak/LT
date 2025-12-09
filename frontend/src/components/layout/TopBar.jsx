import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import {
    Settings,
    User,
    Sun,
    Moon
} from 'lucide-react';
import { useTheme } from '../../context/ThemeContext';
import { useMarket } from '../../context/MarketContext';
// import { useTools } from '../../context/ToolContext'; // Removing unused import
import './TopBar.css';

export default function TopBar() {
    const { theme, toggleTheme } = useTheme();
    const { timeframe, setTimeframe, dataSource, setDataSource } = useMarket();
    // const { activeTool, setActiveTool } = useTools(); // Removed
    const location = useLocation();

    return (
        <header className="top-bar">
            <div className="top-bar-left">
                <NavLink to="/" className="logo">SMC</NavLink>
                <div className="divider"></div>
                <span className="badge">Forex</span>
            </div>

            <div className="top-bar-center">
                {(location.pathname === '/trade' || location.pathname === '/backtest') && (
                    <div className="timeframe-selector">
                        {['1M', '5M', '15M', '1H', '4H', 'D'].map(tf => (
                            <button
                                key={tf}
                                className={`tf-btn ${timeframe === tf ? 'active' : ''}`}
                                onClick={() => setTimeframe(tf)}
                            >
                                {tf}
                            </button>
                        ))}
                    </div>
                )}

                <div className="divider"></div>

                <div className="divider"></div>

                <div className="data-source-toggle">
                    <button
                        className={`source-btn ${dataSource === 'csv' ? 'active' : ''}`}
                        onClick={() => setDataSource('csv')}
                        title="Use Historical CSV Data"
                    >
                        History
                    </button>
                    <button
                        className={`source-btn ${dataSource === 'ctrader' ? 'active' : ''}`}
                        onClick={() => setDataSource('ctrader')}
                        title="Use Live cTrader Data"
                    >
                        Live
                    </button>
                </div>
            </div>

            <div className="top-bar-right">

                <div className="divider"></div>

                <div className="actions">
                    <button className="icon-btn" onClick={toggleTheme}>
                        {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
                    </button>
                    <NavLink to="/settings" className="icon-btn">
                        <Settings size={18} />
                    </NavLink>
                    <NavLink to="/account" className="icon-btn profile-btn">
                        <User size={18} />
                    </NavLink>
                </div>
            </div>
        </header >
    );
}
