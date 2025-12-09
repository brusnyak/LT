import React from 'react';
import { useDraggable } from '@dnd-kit/core';
import { CSS } from '@dnd-kit/utilities';
import {
    Star,
    TrendingUp,
    TrendingDown,
    Camera,
    Minus,
    Triangle,
    Circle,
    Type,
    Ruler,
    MousePointer2
} from 'lucide-react';
import { useTools } from '../../context/ToolContext';
import './UniversalFloatingToolbar.css';

// Map of all possible tools to icons (should match GymPage/TradingPage/TabBar definitions)
const TOOL_DEFINITIONS = {
    cursor: { icon: MousePointer2, label: 'Cursor' },
    long: { icon: TrendingUp, label: 'Long Position' },
    short: { icon: TrendingDown, label: 'Short Position' },
    screenshot: { icon: Camera, label: 'Screenshot' },
    trendline: { icon: TrendingUp, label: 'Trendline' }, // Reusing icon for example, usually a line
    hline: { icon: Minus, label: 'Horz Line' },
    fib: { icon: Ruler, label: 'Fibonacci' },
    triangle: { icon: Triangle, label: 'Triangle' },
    circle: { icon: Circle, label: 'Circle' },
    text: { icon: Type, label: 'Text' },
};

export default function UniversalFloatingToolbar({ position, onToolSelect }) {
    const { activeTool, favoriteTools } = useTools();

    const { attributes, listeners, setNodeRef, transform } = useDraggable({
        id: 'universal-floating-toolbar',
    });

    const style = {
        position: 'absolute',
        left: position?.x || 100,
        top: position?.y || 100,
        transform: transform ? CSS.Translate.toString(transform) : undefined,
        zIndex: 50,
    };

    return (
        <div
            ref={setNodeRef}
            style={style}
            className="universal-floating-toolbar"
            {...listeners}
            {...attributes}
        >
            <div className="toolbar-header">
                <Star size={12} fill="currentColor" />
                <span className="toolbar-title">Tools</span>
            </div>

            <div className="toolbar-grid">
                {favoriteTools.map(toolId => {
                    const def = TOOL_DEFINITIONS[toolId] || { icon: Star, label: toolId };
                    const isActive = activeTool === toolId;

                    return (
                        <button
                            key={toolId}
                            className={`tool-btn ${isActive ? 'active' : ''}`}
                            onClick={(e) => {
                                e.stopPropagation(); // Prevent drag start
                                onToolSelect(toolId);
                            }}
                            title={def.label}
                            onPointerDown={(e) => e.stopPropagation()} // Important for button clicks inside draggable
                        >
                            <def.icon size={18} strokeWidth={1.5} />
                        </button>
                    );
                })}
            </div>
            {/* Optional: Add "Edit favorites" button or drag handle if needed */}
        </div>
    );
}
