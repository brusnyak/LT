import React from 'react';
import { TrendingUp, TrendingDown, Minus, Square, Type, Camera, Trash2 } from 'lucide-react';
import './DrawingToolbar.css';

/**
 * Unified drawing toolbar for Gym and Trading pages
 * Provides position drawing, lines, zones, text, and screenshot tools
 */
export default function DrawingToolbar({
    activeTool,
    onToolSelect,
    onClear,
    onScreenshot,
    disabled = false
}) {
    const tools = [
        { id: 'long', icon: TrendingUp, label: 'Long Position', color: '#26a69a' },
        { id: 'short', icon: TrendingDown, label: 'Short Position', color: '#ef5350' },
        { id: 'line', icon: Minus, label: 'Draw Line', color: '#42a5f5' },
        { id: 'zone', icon: Square, label: 'Draw Zone', color: '#ab47bc' },
        { id: 'text', icon: Type, label: 'Add Text', color: '#ffa726' },
    ];

    return (
        <div className="drawing-toolbar">
            <div className="toolbar-section">
                <span className="toolbar-label">Drawing Tools:</span>
                <div className="tool-buttons">
                    {tools.map(tool => (
                        <button
                            key={tool.id}
                            className={`tool-btn ${activeTool === tool.id ? 'active' : ''}`}
                            onClick={() => onToolSelect(activeTool === tool.id ? null : tool.id)}
                            disabled={disabled}
                            title={tool.label}
                            style={{
                                '--tool-color': tool.color,
                                borderColor: activeTool === tool.id ? tool.color : 'transparent'
                            }}
                        >
                            <tool.icon size={18} />
                            <span className="tool-label">{tool.label.split(' ')[0]}</span>
                        </button>
                    ))}
                </div>
            </div>

            <div className="toolbar-section">
                <button
                    className="tool-btn action-btn"
                    onClick={onScreenshot}
                    disabled={disabled}
                    title="Take Screenshot"
                >
                    <Camera size={18} />
                    <span className="tool-label">Screenshot</span>
                </button>
                <button
                    className="tool-btn action-btn danger"
                    onClick={onClear}
                    disabled={disabled}
                    title="Clear All Drawings"
                >
                    <Trash2 size={18} />
                    <span className="tool-label">Clear</span>
                </button>
            </div>

            {activeTool && (
                <div className="toolbar-hint">
                    {activeTool === 'long' && '📈 Click to mark: Entry → SL → TP → Exit'}
                    {activeTool === 'short' && '📉 Click to mark: Entry → SL → TP → Exit'}
                    {activeTool === 'line' && '➖ Click two points to draw a line'}
                    {activeTool === 'zone' && '⬜ Click two corners to draw a zone'}
                    {activeTool === 'text' && '📝 Click to add text annotation'}
                </div>
            )}
        </div>
    );
}
