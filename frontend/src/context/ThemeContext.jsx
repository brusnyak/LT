import React, { createContext, useContext, useState, useEffect } from 'react';

const ThemeContext = createContext();

export function ThemeProvider({ children }) {
    const [theme, setTheme] = useState(() => {
        return localStorage.getItem('smc-theme') || 'dark';
    });

    const [palette, setPalette] = useState(() => {
        return localStorage.getItem('smc-palette') || 'default';
    });

    useEffect(() => {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('smc-theme', theme);
    }, [theme]);

    useEffect(() => {
        document.documentElement.setAttribute('data-palette', palette);
        localStorage.setItem('smc-palette', palette);
    }, [palette]);

    const toggleTheme = () => {
        setTheme(prev => prev === 'dark' ? 'light' : 'dark');
    };

    const setPaletteValue = (newPalette) => {
        setPalette(newPalette);
    };

    return (
        <ThemeContext.Provider value={{ theme, toggleTheme, palette, setPalette: setPaletteValue }}>
            {children}
        </ThemeContext.Provider>
    );
}

export function useTheme() {
    return useContext(ThemeContext);
}
