import React from 'react';
import { TrendingUp, TrendingDown, Minus, Square, Type, Camera, Trash2, Move } from 'lucide-react';
import './GymToolsSidebar.css';

/**
 * Left sidebar with drawing tools (matches Trading page layout)
 */
export default function GymToolsSidebar({
    activeTool,
    onToolSelect,
    disabled = false
}) {
    const tools = [
        { id: 'select', icon: Move, label: 'Select', section: 'cursor' },
        { id: 'long', icon: TrendingUp, label: 'Long Position', section: 'positions' },
        { id: 'short', icon: TrendingDown, label: 'Short Position', section: 'positions' },
        { id: 'line', icon: Minus, label: 'Trendline', section: 'drawing' },
        { id: 'zone', icon: Square, label: 'Rectangle', section: 'drawing' },
        { id: 'text', icon: Type, label: 'Text', section: 'drawing' },
        { id: 'screenshot', icon: Camera, label: 'Screenshot', section: 'actions' },
        { id: 'clear', icon: Trash2, label: 'Clear All', section: 'actions' },
    ];

    const handleToolClick = (toolId) => {
        if (toolId === 'screenshot' || toolId === 'clear') {
            // These are action tools, not toggle tools
            onToolSelect(toolId);
        } else {
            // Toggle selection
            onToolSelect(activeTool === toolId ? null : toolId);
        }
    };

    return (
        <div className="gym-tools-sidebar">
            {tools.map(tool => (
                <button
                    key={tool.id}
                    className={`sidebar-tool-btn ${activeTool === tool.id ? 'active' : ''} ${tool.section}`}
                    onClick={() => handleToolClick(tool.id)}
                    disabled={disabled}
                    title={tool.label}
                >
                    <tool.icon size={20} />
                </button>
            ))}
        </div>
    );
}
