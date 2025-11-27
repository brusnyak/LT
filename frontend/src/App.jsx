import React, { useState, useEffect } from 'react';
import './App.css';
import SplitView from './components/layout/SplitView';
import TradingViewChart from './components/chart/TradingViewChart';
import JournalTab from './components/tabs/JournalTab';
import AccountTab from './components/tabs/AccountTab';
import SettingsTab from './components/tabs/SettingsTab';
import BacktestTab from './components/tabs/BacktestTab';
import { fetchCandles, fetchAnalysis } from './services/api';

function App() {
    const [activeTab, setActiveTab] = useState('journal');
    const [candleData, setCandleData] = useState([]);
    const [ranges, setRanges] = useState([]);
    const [signals, setSignals] = useState([]);
    const [loading, setLoading] = useState(true);
    const [journalLoading, setJournalLoading] = useState(false);

    // Settings
    const [settings, setSettings] = useState(() => {
        const saved = localStorage.getItem('smc_settings');
        return saved ? JSON.parse(saved) : {
            startingBalance: 50000,
            riskPercent: 0.5,
            targetRR: 2.0,
            timezone: 'UTC+1',
            showPositions: true
        };
    });

    const [smcToggles, setSmcToggles] = useState({
        swings: true,
        structure: true,
        orderBlocks: true,
        fvg: true,
        liquidity: true
    });

    // Load initial data
    useEffect(() => {
        const loadData = async () => {
            try {
                // 1. Load Candles (5M)
                const candles = await fetchCandles('EURUSD', '5M', 1000);
                setCandleData(candles);

                // 2. Load Analysis (Ranges & Signals)
                const analysis = await fetchAnalysis('5M', 'EURUSD');
                setRanges(analysis.ranges || []);
                setSignals(analysis.signals || []);

            } catch (error) {
                console.error("Failed to load data:", error);
            } finally {
                setLoading(false);
            }
        };

        loadData();
    }, []);

    const handleSettingsChange = (newSettings) => {
        setSettings(newSettings);
        // Here we could trigger a re-calculation or API call if settings affect strategy
    };

    const renderContent = () => {
        if (loading) return <div className="loading">Loading Market Data...</div>;

        // If Backtest tab is active, show full screen backtest view
        if (activeTab === 'backtest') {
            return <BacktestTab candleData={candleData} />;
        }

        // Otherwise show standard Split View (Chart + Bottom Panel)
        return (
            <SplitView
                topPanel={
                    <TradingViewChart
                        data={candleData}
                        ranges={ranges}
                        signals={signals}
                        smcToggles={smcToggles}
                        showPositions={settings.showPositions}
                    />
                }
                bottomPanel={
                    <div className="bottom-panel-content">
                        {activeTab === 'journal' && (
                            <JournalTab
                                signals={signals}
                                loading={journalLoading}
                            />
                        )}
                        {activeTab === 'account' && (
                            <AccountTab
                                signals={signals}
                                settings={settings}
                            />
                        )}
                        {activeTab === 'settings' && (
                            <SettingsTab
                                settings={settings}
                                onSettingsChange={handleSettingsChange}
                            />
                        )}
                    </div>
                }
            />
        );
    };

    return (
        <div className="app-container">
            <header className="app-header">
                <div className="logo">SMC Trading Environment</div>
                <nav className="main-nav">
                    <button
                        className={activeTab === 'journal' ? 'active' : ''}
                        onClick={() => setActiveTab('journal')}
                    >
                        📓 Journal
                    </button>
                    <button
                        className={activeTab === 'account' ? 'active' : ''}
                        onClick={() => setActiveTab('account')}
                    >
                        📊 Account
                    </button>
                    <button
                        className={activeTab === 'backtest' ? 'active' : ''}
                        onClick={() => setActiveTab('backtest')}
                    >
                        🧪 Backtest
                    </button>
                    <button
                        className={activeTab === 'settings' ? 'active' : ''}
                        onClick={() => setActiveTab('settings')}
                    >
                        ⚙️ Settings
                    </button>
                </nav>
            </header>

            <main className="app-main">
                {renderContent()}
            </main>
        </div>
    );
}

export default App;
