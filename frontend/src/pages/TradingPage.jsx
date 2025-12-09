import React, { useState, useEffect } from 'react';
import { Panel, PanelGroup, PanelResizeHandle } from 'react-resizable-panels';
import { DndContext } from '@dnd-kit/core';
import TradingViewChart from '../components/chart/TradingViewChart';
import SignalsPanel from '../components/trading/SignalsPanel';
import UniversalFloatingToolbar from '../components/trading/UniversalFloatingToolbar';
import ChartOverlayControls from '../components/trading/ChartOverlayControls';
import DrawingOverlay from '../components/overlay/DrawingOverlay'; // Added import
import {
    fetchCandles,
    fetchHumanTrainedSignals,
    fetchSwings,
    fetchOrderBlocks,
    fetchFVGs,
    fetchLiquidity
} from '../services/api';
import { useSettings } from '../context/SettingsContext';
import { useMarket } from '../context/MarketContext';
import './TradingPage.css';

import { useTools } from '../context/ToolContext'; // Add import
import InteractivePositionOverlay from '../components/chart/InteractivePositionOverlay';
import { useScreenshot } from '../hooks/useScreenshot';
import { useRef } from 'react'; // Ensure useRef is imported

export default function TradingPage() {
    const { activeTool, setActiveTool } = useTools(); // Use hook

    const [swings, setSwings] = useState(null);
    const [obs, setObs] = useState(null);
    const [fvgs, setFvgs] = useState(null);
    const [liquidity, setLiquidity] = useState(null);
    const [candleData, setCandleData] = useState([]);
    const [ranges, setRanges] = useState([]);
    const [signals, setSignals] = useState([]);
    const [loading, setLoading] = useState(true);

    // Prediction state
    const [predictionData, setPredictionData] = useState(null);
    const [ghostPredictions, setGhostPredictions] = useState([]);

    const { isOverlayEnabled } = useSettings();
    const { pair, timeframe, dataSource } = useMarket();

    const [toolbarPos, setToolbarPos] = useState(() => {
        const saved = localStorage.getItem('smc-toolbar-pos');
        return saved ? JSON.parse(saved) : { x: 100, y: 100 };
    });

    const chartRef = useRef(null);
    const { captureChart, saveScreenshot } = useScreenshot();

    // Position Drawing State
    const [activePosition, setActivePosition] = useState(null);
    const [positionStep, setPositionStep] = useState('idle');

    const handleDragEnd = (event) => {
        const { delta } = event;
        setToolbarPos(prev => {
            const newPos = {
                x: prev.x + delta.x,
                y: prev.y + delta.y
            };
            localStorage.setItem('smc-toolbar-pos', JSON.stringify(newPos));
            return newPos;
        });
    };

    // Prediction update handler
    const handlePredictionUpdate = (prediction, ghosts = []) => {
        setPredictionData(prediction);
        setGhostPredictions(ghosts);
    };

    // Load data and sync with prediction
    useEffect(() => {
        const loadData = async () => {
            setLoading(true);
            try {
                let candles;
                if (predictionData && predictionData.split_time) {
                    // Fetch historical data ending at split time
                    candles = await fetchCandles(pair, timeframe, 5000, null, predictionData.split_time, dataSource);
                } else {
                    // Fetch latest data
                    candles = await fetchCandles(pair, timeframe, 5000, null, null, dataSource);
                }
                setCandleData(candles);

                // Fetch signals from HumanTrainedStrategy
                const strategyData = await fetchHumanTrainedSignals(pair, timeframe);
                setSignals(strategyData.signals || []);
                setRanges([]); // No ranges for HumanTrained strategy

            } catch (error) {
                console.error("Failed to load data:", error);
            } finally {
                setLoading(false);
            }
        };

        loadData();
    }, [pair, timeframe, predictionData, dataSource]);

    // Fetch Overlays based on toggles
    useEffect(() => {
        const loadOverlays = async () => {
            try {
                // Clear or load swings/structure
                if (isOverlayEnabled('structure')) {
                    if (!swings) {
                        const data = await fetchSwings(pair, timeframe);
                        setSwings(data);
                    }
                } else {
                    setSwings(null);
                }

                // Clear or load order blocks
                if (isOverlayEnabled('order_blocks')) {
                    if (!obs) {
                        const data = await fetchOrderBlocks(pair, timeframe);
                        setObs(data);
                    }
                } else {
                    setObs(null);
                }

                // Clear or load FVGs
                if (isOverlayEnabled('fvgs')) {
                    if (!fvgs) {
                        const data = await fetchFVGs(pair, timeframe);
                        setFvgs(data);
                    }
                } else {
                    setFvgs(null);
                }

                // Clear or load liquidity
                if (isOverlayEnabled('liquidity')) {
                    if (!liquidity) {
                        const data = await fetchLiquidity(pair, timeframe);
                        setLiquidity(data);
                    }
                } else {
                    setLiquidity(null);
                }
            } catch (error) {
                console.error("Failed to load overlays:", error);
            }
        };
        loadOverlays();
    }, [isOverlayEnabled, pair, timeframe]); // Removed overlay states from dependencies

    // Loading check moved to JSX to avoid hook order violation

    const smcToggles = {
        swings: isOverlayEnabled('structure'), // 'structure' toggle maps to swings/market structure
        structure: isOverlayEnabled('structure'),
        orderBlocks: isOverlayEnabled('order_blocks'),
        fvg: isOverlayEnabled('fvgs'),
        liquidity: isOverlayEnabled('liquidity')
    };

    const handleChartClick = (e) => {
        if (positionStep !== 'placing' || !['long', 'short'].includes(activeTool)) return;
        if (!chartRef.current || !chartRef.current.chart) return;

        const { chart, series, container } = chartRef.current;
        const rect = container.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;

        const price = series.coordinateToPrice(y);
        const time = chart.timeScale().coordinateToTime(x);

        if (!price || !time) return;

        // Initial Position
        const entry = price;
        const dist = price * 0.001;
        const sl = activeTool === 'long' ? entry - dist : entry + dist;
        const tp = activeTool === 'long' ? entry + (dist * 2) : entry - (dist * 2);

        setActivePosition({
            type: activeTool === 'long' ? 'LONG' : 'SHORT',
            entry,
            sl,
            tp,
            entryTime: time * 1000,
            exitTime: (time + 3000) * 1000 // Placeholder duration
        });
        setPositionStep('modifying');
    };

    const handleConfirmPosition = async () => {
        if (!activePosition) return;

        try {
            // 1. Log Trade to Backend (Accept Signal logic or generic trade log?)
            // Since this is "Trading Tab", it's likely a Live or Challenge account.
            // We should use /api/trades/accept logic BUT that expects a "Signal" object.
            // Or we can create a new endpoint /api/trades/manual
            // For now, let's use acceptSignal but construct it like a signal?
            // User requested: "set the trades, then confirm them so that there would be automatic screenshot and record"

            // Construct payload compatible with `accept_signal`?
            // SignalAcceptRequest: pair, type, entry, sl, tp, rr, signal_time, strategy='manual'

            const rr = Math.abs((activePosition.tp - activePosition.entry) / (activePosition.entry - activePosition.sl));

            const signalPayload = {
                pair: pair,
                type: activePosition.type,
                entry: activePosition.entry,
                sl: activePosition.sl,
                tp: activePosition.tp,
                rr: rr,
                signal_time: new Date(activePosition.entryTime).toISOString(),
                strategy: 'manual',
                challenge_id: 1 // Default challenge for now
            };

            // We need to import acceptSignal from api.js. 
            // Oops, I need to make sure acceptSignal is imported (it wasn't in list above, but fetchHumanTrainedSignals was).
            // Let's check imports.

            // Assuming acceptSignal is imported.
            // const savedTrade = await acceptSignal(signalPayload);
            // Wait, acceptSignal is imported below in existing imports?
            // Let's assume I need to update imports if missing.

            // For now, let's mock specific manual trade endpoint via fetch to avoid circular dep or missing import
            const resp = await fetch('http://localhost:9000/api/trades/accept', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(signalPayload)
            });

            if (!resp.ok) throw new Error("Failed to log trade");
            const savedTrade = await resp.json();

            // 2. Screenshot
            const screenshot = await captureChart(chartRef);
            if (screenshot) {
                // Use Journal Screenshot Endpoint (default in hook)
                await saveScreenshot(screenshot, savedTrade.id);
            }

            console.log("Trade recorded:", savedTrade.id);
            setActivePosition(null);
            setPositionStep('idle');
            setActiveTool(null); // Reset tool

        } catch (e) {
            console.error("Failed to record trade", e);
            alert("Failed to record trade");
        }
    };

    const handleCancelPosition = () => {
        setActivePosition(null);
        setPositionStep('idle');
    };

    // Listen for tool changes
    useEffect(() => {
        if (['long', 'short'].includes(activeTool)) {
            setPositionStep('placing');
        } else {
            setPositionStep('idle');
            setActivePosition(null);
        }
    }, [activeTool]);

    return (
        <div className="trading-page">
            {loading ? (
                <div className="loading-container">
                    <div className="loading-spinner"></div>
                    <p>Loading Market Data...</p>
                </div>
            ) : (
                <PanelGroup direction="horizontal">
                    {/* Chart Area */}
                    <Panel defaultSize={75} minSize={40}>
                        <div className="chart-section" style={{ position: 'relative' }}>
                            <ChartOverlayControls />

                            {/* Wrapper to handle clicks */}
                            <div
                                className="chart-wrapper"
                                style={{ flex: 1, height: '100%', cursor: positionStep === 'placing' ? 'crosshair' : 'default' }}
                                onClick={handleChartClick}
                            >
                                <div style={{ position: 'relative', height: '100%', flex: 1 }}>
                                    <TradingViewChart
                                        ref={chartRef}
                                        data={candleData}
                                        pair={pair}
                                        // ... other props
                                        ranges={isOverlayEnabled('ranges') ? ranges : []}
                                        signals={signals}
                                        showSignals={isOverlayEnabled('signals')}
                                        smcToggles={smcToggles}
                                        showPositions={isOverlayEnabled('signals')}
                                        swingData={isOverlayEnabled('structure') ? swings : null}
                                        orderBlockData={isOverlayEnabled('order_blocks') ? obs : null}
                                        fvgData={isOverlayEnabled('fvgs') ? fvgs : null}
                                        liquidityData={isOverlayEnabled('liquidity') ? liquidity : null}
                                        predictionData={predictionData}
                                        ghostPredictions={ghostPredictions}
                                    />
                                    {chartRef.current && (
                                        <DrawingOverlay
                                            chart={chartRef.current.chart}
                                            series={chartRef.current.series}
                                            containerRef={{ current: chartRef.current.container }}
                                        />
                                    )}
                                </div>
                                {activePosition && chartRef.current && (
                                    <InteractivePositionOverlay
                                        chartContainerRef={{ current: chartRef.current.container }}
                                        chart={chartRef.current.chart}
                                        series={chartRef.current.series}
                                        activePosition={activePosition}
                                        onUpdatePosition={setActivePosition}
                                        onConfirm={handleConfirmPosition}
                                        onCancel={handleCancelPosition}
                                    />
                                )}
                            </div>
                        </div>
                    </Panel>


                    {/* Resize Handle */}
                    <PanelResizeHandle className="panel-resize-handle" />

                    {/* Signals Panel */}
                    <Panel defaultSize={20} minSize={15} maxSize={40}>
                        <SignalsPanel
                            signals={signals}
                            onPredictionUpdate={handlePredictionUpdate}
                        />
                    </Panel>
                </PanelGroup>
            )}
        </div>
    );
}


