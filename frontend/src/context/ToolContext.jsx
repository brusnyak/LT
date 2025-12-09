import React, { createContext, useContext, useState, useEffect } from 'react';

const ToolContext = createContext();

export function ToolProvider({ children }) {
    const [activeTool, setActiveTool] = useState(null);

    // Favorites: Persisted to localStorage
    const [favoriteTools, setFavoriteTools] = useState(() => {
        const saved = localStorage.getItem('smc-fav-tools');
        // Default favorites
        return saved ? JSON.parse(saved) : ['cursor', 'long', 'short', 'screenshot', 'trendline', 'rect'];
    });

    const [lastUsedTools, setLastUsedTools] = useState([]);

    useEffect(() => {
        localStorage.setItem('smc-fav-tools', JSON.stringify(favoriteTools));
    }, [favoriteTools]);

    const toggleFavorite = (toolId) => {
        setFavoriteTools(prev => {
            if (prev.includes(toolId)) return prev.filter(t => t !== toolId);
            return [...prev, toolId];
        });
    };

    return (
        <ToolContext.Provider value={{
            activeTool,
            setActiveTool,
            favoriteTools,
            toggleFavorite,
            lastUsedTools
        }}>
            {children}
        </ToolContext.Provider>
    );
}

export function useTools() {
    return useContext(ToolContext);
}
