import React, { useState } from 'react';
import { useDraggable } from '@dnd-kit/core';
import { CSS } from '@dnd-kit/utilities';
import { Star, TrendingUp, Minus, Ruler } from 'lucide-react';
import './FloatingToolbar.css';

const starredTools = [
    { id: 'trendline', icon: TrendingUp, label: 'Trendline' },
    { id: 'hline', icon: Minus, label: 'H-Line' },
    { id: 'fib', icon: Ruler, label: 'Fib' },
];

function DraggableFloatingToolbar({ position }) {
    const { attributes, listeners, setNodeRef, transform } = useDraggable({
        id: 'floating-toolbar',
    });

    const style = {
        position: 'absolute',
        left: position?.x || 100,
        top: position?.y || 100,
        transform: transform ? CSS.Translate.toString(transform) : undefined,
        zIndex: 20,
    };

    return (
        <div
            ref={setNodeRef}
            style={style}
            className="floating-toolbar"
            {...listeners}
            {...attributes}
        >
            <div className="floating-toolbar-header">
                <Star size={14} />
                <span>Tools</span>
            </div>
            <div className="floating-toolbar-tools">
                {starredTools.map(tool => (
                    <button key={tool.id} className="floating-tool-btn" title={tool.label}>
                        <tool.icon size={18} />
                    </button>
                ))}
            </div>
        </div>
    );
}

export default DraggableFloatingToolbar;
