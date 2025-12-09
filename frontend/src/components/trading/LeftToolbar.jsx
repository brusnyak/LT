import React, { useState } from 'react';
import {
    TrendingUp,
    Minus,
    Triangle,
    Circle,
    Type,
    Ruler,
    ChevronLeft,
    ChevronRight
} from 'lucide-react';
import './LeftToolbar.css';

const drawingTools = [
    { id: 'trendline', icon: TrendingUp, label: 'Trendline' },
    { id: 'hline', icon: Minus, label: 'Horizontal Line' },
    { id: 'fib', icon: Ruler, label: 'Fibonacci' },
    { id: 'triangle', icon: Triangle, label: 'Triangle' },
    { id: 'circle', icon: Circle, label: 'Circle' },
    { id: 'text', icon: Type, label: 'Text' },
];

export default function LeftToolbar() {
    const [isCollapsed, setIsCollapsed] = useState(false);
    const [activeTool, setActiveTool] = useState(null);

    return (
        <div className={`left-toolbar ${isCollapsed ? 'collapsed' : ''}`}>
            <div className="toolbar-header">
                <button
                    className="collapse-btn"
                    onClick={() => setIsCollapsed(!isCollapsed)}
                >
                    {isCollapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
                </button>
            </div>

            {!isCollapsed && (
                <div className="toolbar-tools">
                    {drawingTools.map(tool => (
                        <button
                            key={tool.id}
                            className={`tool-btn ${activeTool === tool.id ? 'active' : ''}`}
                            onClick={() => setActiveTool(tool.id)}
                            title={tool.label}
                        >
                            <tool.icon size={20} />
                            <span className="tool-label">{tool.label}</span>
                        </button>
                    ))}
                </div>
            )}
        </div>
    );
}
