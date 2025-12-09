import React from 'react';
import { useDraggable } from '@dnd-kit/core';
import { CSS } from '@dnd-kit/utilities';
import { Star, TrendingUp, TrendingDown, Camera } from 'lucide-react';
import './GymFloatingToolbar.css';

const favoriteTools = [
    { id: 'long', icon: TrendingUp, label: 'Long' },
    { id: 'short', icon: TrendingDown, label: 'Short' },
    { id: 'screenshot', icon: Camera, label: 'Screenshot' },
];

export default function GymFloatingToolbar({ position, activeTool, onToolSelect }) {
    const { attributes, listeners, setNodeRef, transform } = useDraggable({
        id: 'gym-floating-toolbar',
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
            className="gym-floating-toolbar"
            {...listeners}
            {...attributes}
        >
            <div className="gym-floating-toolbar-header">
                <Star size={14} />
                <span>Favorites</span>
            </div>
            <div className="gym-floating-toolbar-tools">
                {favoriteTools.map(tool => (
                    <button
                        key={tool.id}
                        className={`gym-floating-tool-btn ${activeTool === tool.id ? 'active' : ''}`}
                        onClick={(e) => {
                            e.stopPropagation();
                            onToolSelect(tool.id);
                        }}
                        title={tool.label}
                    >
                        <tool.icon size={18} />
                    </button>
                ))}
            </div>
        </div>
    );
}
