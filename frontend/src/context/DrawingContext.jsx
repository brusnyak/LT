import React, { createContext, useContext, useState, useEffect } from 'react';

const DrawingContext = createContext();

export function DrawingProvider({ children }) {
    const [drawings, setDrawings] = useState([]);
    const [selectedDrawingId, setSelectedDrawingId] = useState(null);

    // Save/Load could be added here later

    const addDrawing = (drawing) => {
        setDrawings(prev => [...prev, { ...drawing, id: crypto.randomUUID(), createdAt: Date.now() }]);
    };

    const updateDrawing = (id, updates) => {
        setDrawings(prev => prev.map(d => d.id === id ? { ...d, ...updates } : d));
    };

    const removeDrawing = (id) => {
        setDrawings(prev => prev.filter(d => d.id !== id));
    };

    const clearDrawings = () => {
        setDrawings([]);
    };

    return (
        <DrawingContext.Provider value={{
            drawings,
            addDrawing,
            updateDrawing,
            removeDrawing,
            clearDrawings,
            selectedDrawingId,
            setSelectedDrawingId
        }}>
            {children}
        </DrawingContext.Provider>
    );
}

export function useDrawings() {
    return useContext(DrawingContext);
}
