/**
 * Settings Context
 * 
 * Manages UI layout configuration with localStorage persistence
 */
import React, { createContext, useContext, useState, useEffect } from 'react';
import { LAYOUT_PRESETS, DEFAULT_LAYOUT, validateLayout, getPreset } from '../config/layouts';

export const SettingsContext = createContext();

const STORAGE_KEYS = {
    LAYOUT: 'smc_current_layout',
    CUSTOM_OVERRIDES: 'smc_custom_overrides',
    LAST_PRESET: 'smc_last_preset'
};

export function SettingsProvider({ children }) {
    // Load from localStorage or use default
    const [currentPreset, setCurrentPreset] = useState(() => {
        const saved = localStorage.getItem(STORAGE_KEYS.LAST_PRESET);
        return saved || DEFAULT_LAYOUT;
    });

    const [currentLayout, setCurrentLayout] = useState(() => {
        const saved = localStorage.getItem(STORAGE_KEYS.LAYOUT);
        if (saved) {
            try {
                const parsed = JSON.parse(saved);
                if (validateLayout(parsed)) {
                    return parsed;
                }
            } catch (e) {
                console.error('Failed to parse saved layout:', e);
            }
        }
        return getPreset(DEFAULT_LAYOUT);
    });

    const [customOverrides, setCustomOverrides] = useState(() => {
        const saved = localStorage.getItem(STORAGE_KEYS.CUSTOM_OVERRIDES);
        if (saved) {
            try {
                return JSON.parse(saved);
            } catch (e) {
                console.error('Failed to parse custom overrides:', e);
            }
        }
        return {};
    });

    // Save to localStorage whenever settings change
    useEffect(() => {
        localStorage.setItem(STORAGE_KEYS.LAYOUT, JSON.stringify(currentLayout));
    }, [currentLayout]);

    useEffect(() => {
        localStorage.setItem(STORAGE_KEYS.CUSTOM_OVERRIDES, JSON.stringify(customOverrides));
    }, [customOverrides]);

    useEffect(() => {
        localStorage.setItem(STORAGE_KEYS.LAST_PRESET, currentPreset);
    }, [currentPreset]);

    /**
     * Load a preset layout
     */
    const loadPreset = (presetId) => {
        const preset = getPreset(presetId);
        setCurrentLayout(preset);
        setCurrentPreset(presetId);
        setCustomOverrides({});
    };

    /**
     * Toggle panel visibility
     */
    const togglePanel = (panelName) => {
        setCurrentLayout(prev => {
            const newLayout = { ...prev };
            if (!newLayout.panels[panelName]) {
                newLayout.panels[panelName] = { visible: true, order: 99 };
            } else {
                newLayout.panels[panelName] = {
                    ...newLayout.panels[panelName],
                    visible: !newLayout.panels[panelName].visible
                };
            }
            return newLayout;
        });

        // Mark as custom
        setCustomOverrides(prev => ({
            ...prev,
            panels: { ...prev.panels, [panelName]: true }
        }));
    };

    /**
     * Toggle overlay visibility
     */
    const toggleOverlay = (overlayName) => {
        setCurrentLayout(prev => ({
            ...prev,
            overlays: {
                ...prev.overlays,
                [overlayName]: !prev.overlays[overlayName]
            }
        }));

        // Mark as custom
        setCustomOverrides(prev => ({
            ...prev,
            overlays: { ...prev.overlays, [overlayName]: true }
        }));
    };

    /**
     * Check if panel is visible
     */
    const isPanelVisible = (panelName) => {
        return currentLayout.panels[panelName]?.visible ?? false;
    };

    /**
     * Check if overlay is enabled
     */
    const isOverlayEnabled = (overlayName) => {
        return currentLayout.overlays[overlayName] ?? false;
    };

    /**
     * Reset to default layout
     */
    const resetToDefault = () => {
        loadPreset(DEFAULT_LAYOUT);
    };

    /**
     * Check if current layout has custom modifications
     */
    const hasCustomModifications = () => {
        return Object.keys(customOverrides).length > 0;
    };

    const value = {
        currentLayout,
        currentPreset,
        customOverrides,
        loadPreset,
        togglePanel,
        toggleOverlay,
        isPanelVisible,
        isOverlayEnabled,
        resetToDefault,
        hasCustomModifications
    };

    return (
        <SettingsContext.Provider value={value}>
            {children}
        </SettingsContext.Provider>
    );
}

/**
 * Hook to use settings context
 */
export const useSettings = () => {
    const context = useContext(SettingsContext);
    if (!context) {
        throw new Error('useSettings must be used within a SettingsProvider');
    }
    return context;
};
