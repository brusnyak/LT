import React, { useState, useEffect, useRef } from 'react';
import { createChart } from 'lightweight-charts';
import '../styles/TrainerPage.css';

const API_BASE = 'http://localhost:9000/api';

// Available pairs from CSV data
const AVAILABLE_PAIRS = [
    { value: 'EURUSD', label: 'EUR/USD', category: 'Forex' },
    { value: 'GBPUSD', label: 'GBP/USD', category: 'Forex' },
    { value: 'GBPJPY', label: 'GBP/JPY', category: 'Forex' },
    { value: 'USDCAD', label: 'USD/CAD', category: 'Forex' },
    { value: 'XAUUSD', label: 'XAU/USD (Gold)', category: 'Metals' },
    { value: 'XAGUSD', label: 'XAG/USD (Silver)', category: 'Metals' },
    { value: 'BTCUSD', label: 'BTC/USD', category: 'Crypto' },
    { value: 'ETHUSD', label: 'ETH/USD', category: 'Crypto' },
];

export default function TrainerPage() {
    const [selectedPair, setSelectedPair] = useState('EURUSD');
    const [session, setSession] = useState(null);
    const [data, setData] = useState([]);
    const [cursor, setCursor] = useState(0);
    const [isPlaying, setIsPlaying] = useState(false);
    const [speed, setSpeed] = useState(1);
    const [activeTrade, setActiveTrade] = useState(null);
    const [tradeForm, setTradeForm] = useState({ sl: '', tp: '' });
    const [isLoading, setIsLoading] = useState(false);

    const chartContainerRef = useRef(null);
    const chartRef = useRef(null);
    const candleSeriesRef = useRef(null);
    const intervalRef = useRef(null);

    // Initialize chart
    useEffect(() => {
        if (!chartContainerRef.current) return;

        const chart = createChart(chartContainerRef.current, {
            width: chartContainerRef.current.clientWidth,
            height: 600,
            layout: { background: { color: '#1e222d' }, textColor: '#d1d4dc' },
            grid: { vertLines: { color: '#2b2b43' }, horzLines: { color: '#2b2b43' } },
            timeScale: { borderColor: '#485c7b', timeVisible: true },
            rightPriceScale: { borderColor: '#485c7b' },
        });

        chartRef.current = chart;
        const candleSeries = chart.addCandlestickSeries({
            upColor: '#26a69a', downColor: '#ef5350',
            borderUpColor: '#26a69a', borderDownColor: '#ef5350',
            wickUpColor: '#26a69a', wickDownColor: '#ef5350',
        });
        candleSeriesRef.current = candleSeries;

        return () => chart.remove();
    }, []);

    // Load session data
    const startSession = async () => {
        setIsLoading(true);
        try {
            // Create session
            const sessionResp = await fetch(`${API_BASE}/trainer/sessions`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    id: crypto.randomUUID(),
                    name: `Training ${selectedPair} ${new Date().toLocaleDateString()}`,
                    symbol: selectedPair,
                    start_date: new Date().toISOString(),
                    end_date: new Date().toISOString(),
                }),
            });
            const sessionData = await sessionResp.json();
            setSession(sessionData);

            // Load candle data for selected pair
            const dataResp = await fetch(`${API_BASE}/data/candles?pair=${selectedPair}&timeframe=M5&limit=500`);
            const { candles } = await dataResp.json();
            setData(candles);
            setCursor(50); // Start 50 candles in
        } catch (err) {
            console.error('Failed to start session:', err);
            alert(`Failed to load data for ${selectedPair}. Please try another pair.`);
        } finally {
            setIsLoading(false);
        }
    };

    // Handle pair change
    const handlePairChange = (newPair) => {
        if (session) {
            if (!confirm(`Changing pair will end the current session. Continue?`)) {
                return;
            }
            setSession(null);
            setData([]);
            setCursor(0);
            if (intervalRef.current) clearInterval(intervalRef.current);
            setIsPlaying(false);
        }
        setSelectedPair(newPair);
    };

    // Update chart with visible data
    useEffect(() => {
        if (!candleSeriesRef.current || !data.length) return;

        const visibleData = data.slice(0, cursor).map(c => ({
            time: new Date(c.timestamp).getTime() / 1000,
            open: c.open,
            high: c.high,
            low: c.low,
            close: c.close,
        }));

        candleSeriesRef.current.setData(visibleData);
        chartRef.current.timeScale().fitContent();
    }, [cursor, data]);

    // Replay controls
    const play = () => {
        setIsPlaying(true);
        intervalRef.current = setInterval(() => {
            setCursor(prev => Math.min(prev + 1, data.length - 1));
        }, 1000 / speed);
    };

    const pause = () => {
        setIsPlaying(false);
        if (intervalRef.current) clearInterval(intervalRef.current);
    };

    const nextCandle = () => setCursor(prev => Math.min(prev + 1, data.length - 1));

    // Trade actions
    const enterTrade = (type) => {
        const currentCandle = data[cursor];
        setActiveTrade({
            type,
            entry_price: currentCandle.close,
            entry_time: currentCandle.timestamp,
        });
    };

    const confirmTrade = async () => {
        if (!activeTrade || !session) return;

        const trade = {
            id: crypto.randomUUID(),
            session_id: session.id,
            symbol: selectedPair,
            entry_time: activeTrade.entry_time,
            type: activeTrade.type,
            entry_price: activeTrade.entry_price,
            sl_price: parseFloat(tradeForm.sl),
            tp_price: parseFloat(tradeForm.tp),
        };

        try {
            await fetch(`${API_BASE}/trainer/sessions/${session.id}/trades`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(trade),
            });
            alert('Trade logged!');
            setActiveTrade(null);
            setTradeForm({ sl: '', tp: '' });
        } catch (err) {
            console.error('Failed to log trade:', err);
        }
    };

    // Group pairs by category
    const pairsByCategory = AVAILABLE_PAIRS.reduce((acc, pair) => {
        if (!acc[pair.category]) acc[pair.category] = [];
        acc[pair.category].push(pair);
        return acc;
    }, {});

    return (
        <div className="trainer-page">
            <div className="trainer-header">
                <h1>Strategy Trainer (Gym)</h1>

                {/* Pair Selector */}
                <div className="pair-selector">
                    <label htmlFor="pair-select">Trading Pair:</label>
                    <select
                        id="pair-select"
                        value={selectedPair}
                        onChange={(e) => handlePairChange(e.target.value)}
                        disabled={isLoading}
                        className="pair-dropdown"
                    >
                        {Object.entries(pairsByCategory).map(([category, pairs]) => (
                            <optgroup key={category} label={category}>
                                {pairs.map(pair => (
                                    <option key={pair.value} value={pair.value}>
                                        {pair.label}
                                    </option>
                                ))}
                            </optgroup>
                        ))}
                    </select>
                </div>

                {!session ? (
                    <button
                        onClick={startSession}
                        className="btn-primary"
                        disabled={isLoading}
                    >
                        {isLoading ? 'Loading...' : `Start Session (${selectedPair})`}
                    </button>
                ) : (
                    <span className="session-info">
                        Session: {session.name} | {selectedPair}
                    </span>
                )}
            </div>

            <div className="trainer-content">
                <div className="chart-section">
                    <div ref={chartContainerRef} className="chart-container" />

                    <div className="replay-controls">
                        {!isPlaying ? (
                            <button onClick={play} className="btn-control">▶ Play</button>
                        ) : (
                            <button onClick={pause} className="btn-control">⏸ Pause</button>
                        )}
                        <button onClick={nextCandle} className="btn-control">⏭ Next</button>
                        <select value={speed} onChange={(e) => setSpeed(Number(e.target.value))}>
                            <option value={1}>1x</option>
                            <option value={2}>2x</option>
                            <option value={5}>5x</option>
                        </select>
                        <span className="cursor-info">Candle {cursor} / {data.length}</span>
                    </div>
                </div>

                <div className="trade-panel">
                    <h2>Trade Controls</h2>
                    {!activeTrade ? (
                        <div className="trade-buttons">
                            <button onClick={() => enterTrade('LONG')} className="btn-long">Enter Long</button>
                            <button onClick={() => enterTrade('SHORT')} className="btn-short">Enter Short</button>
                        </div>
                    ) : (
                        <div className="trade-form">
                            <h3>{activeTrade.type} @ {activeTrade.entry_price.toFixed(5)}</h3>
                            <input
                                type="number"
                                placeholder="SL Price"
                                step="0.00001"
                                value={tradeForm.sl}
                                onChange={(e) => setTradeForm({ ...tradeForm, sl: e.target.value })}
                            />
                            <input
                                type="number"
                                placeholder="TP Price"
                                step="0.00001"
                                value={tradeForm.tp}
                                onChange={(e) => setTradeForm({ ...tradeForm, tp: e.target.value })}
                            />
                            <button onClick={confirmTrade} className="btn-confirm">Confirm Trade</button>
                            <button onClick={() => setActiveTrade(null)} className="btn-cancel">Cancel</button>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
