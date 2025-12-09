import React, { useState } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { useTools } from '../../context/ToolContext';
import {
    LayoutDashboard,
    LineChart,
    BookOpen,
    FlaskConical,
    Dumbbell,
    MousePointer2,
    TrendingUp,
    TrendingDown,
    Eraser,
    PenTool,
    Minus,
    Ruler,
    Triangle,
    Circle,
    Type
} from 'lucide-react';
import './TabBar.css';

const NAV_ITEMS = [
    { path: '/', label: 'Home', icon: LayoutDashboard },
    { path: '/trade', label: 'Signals', icon: LineChart },
    { path: '/journal', label: 'Journal', icon: BookOpen },
    { path: '/backtest', label: 'Backtest', icon: FlaskConical },
    { path: '/gym', label: 'Gym', icon: Dumbbell },
];

const DRAWING_TOOLS = [
    { id: 'cursor', icon: MousePointer2, label: 'Cursor' },
    { id: 'long', icon: TrendingUp, label: 'Long Position', color: '#4caf50' },
    { id: 'short', icon: TrendingDown, label: 'Short Position', color: '#f44336' },
    { id: 'trendline', icon: PenTool, label: 'Trendline' },
    { id: 'hline', icon: Minus, label: 'Horizontal Line' },
    { id: 'fib', icon: Ruler, label: 'Fibonacci' },
    { id: 'triangle', icon: Triangle, label: 'Triangle' },
    { id: 'circle', icon: Circle, label: 'Circle' },
    { id: 'text', icon: Type, label: 'Text' },
    { id: 'eraser', icon: Eraser, label: 'Eraser' },
];

export default function TabBar() {
    const location = useLocation();
    const showDrawingTools = location.pathname === '/trade' || location.pathname === '/backtest' || location.pathname === '/gym';
    const { activeTool, setActiveTool } = useTools();

    return (
        <nav className="tab-bar">
            <div className="nav-section">
                {NAV_ITEMS.map((item) => (
                    <NavLink
                        key={item.path}
                        to={item.path}
                        className={({ isActive }) => `tab-item ${isActive ? 'active' : ''}`}
                        title={item.label}
                    >
                        <div className="tab-icon">
                            <item.icon size={20} strokeWidth={1.5} />
                        </div>
                    </NavLink>
                ))}
            </div>

            {showDrawingTools && (
                <>
                    <div className="divider-horizontal" />
                    <div className="tools-section">
                        {DRAWING_TOOLS.map((tool) => (
                            <button
                                key={tool.id}
                                className={`tab-item tool-btn ${activeTool === tool.id ? 'active' : ''}`}
                                onClick={() => setActiveTool(activeTool === tool.id ? null : tool.id)}
                                title={tool.label}
                            >
                                <div className="tab-icon">
                                    <tool.icon
                                        size={18}
                                        strokeWidth={1.5}
                                        color={tool.color || 'currentColor'}
                                    />
                                </div>
                            </button>
                        ))}
                    </div>
                </>
            )}
        </nav>
    );
}
