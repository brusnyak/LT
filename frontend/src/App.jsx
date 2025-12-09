import React, { useState, useEffect, useContext } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { SettingsProvider, SettingsContext } from './context/SettingsContext';
import { ThemeProvider } from './context/ThemeContext';
import MarketContext, { MarketProvider } from './context/MarketContext';
import { ToolProvider } from './context/ToolContext';
import { DrawingProvider } from './context/DrawingContext';
import MainLayout from './components/layout/MainLayout';
import PublicLayout from './components/layout/PublicLayout';
import Home from './pages/Home';
import TradingPage from './pages/TradingPage';
import JournalPage from './pages/JournalPage';
import BacktestPage from './pages/BacktestPage';
import AccountPage from './pages/AccountPage';
import SettingsPage from './pages/SettingsPage';
import TrainerPage from './pages/TrainerPage';
import GymPage from './pages/GymPage';

function AppContent() {
    const { pair: currentPair } = useContext(MarketContext); // Renamed to avoid conflict with settings.pair
    const { currentLayout } = useContext(SettingsContext);
    // State and effects moved to TradingPage


    if (!currentLayout) { // Conditional rendering to prevent accessing properties of undefined
        return <div>Loading settings...</div>;
    }

    return (
        <Router>
            <Routes>
                {/* Public Routes */}
                <Route element={<PublicLayout />}>
                    <Route path="/" element={<Home />} />
                </Route>

                {/* App Routes */}
                <Route element={<MainLayout />}>
                    <Route path="/trade" element={<TradingPage />} />
                    <Route path="/journal" element={<JournalPage />} />
                    <Route path="/backtest" element={<BacktestPage />} />
                    <Route path="/account" element={<AccountPage />} />
                    <Route path="/settings" element={<SettingsPage />} />
                    <Route path="/trainer" element={<TrainerPage />} />
                    <Route path="/gym" element={<GymPage />} />
                </Route>

                {/* Fallback */}
                <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
        </Router>
    );
}

function App() {
    return (
        <ThemeProvider>
            <SettingsProvider>
                <MarketProvider>
                    <ToolProvider>
                        <DrawingProvider>
                            <AppContent />
                        </DrawingProvider>
                    </ToolProvider>
                </MarketProvider>
            </SettingsProvider>
        </ThemeProvider>
    );
}

export default App;
