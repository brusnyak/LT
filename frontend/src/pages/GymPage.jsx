import React, { useState, useEffect, useRef } from 'react';
import { Panel, PanelGroup, PanelResizeHandle } from 'react-resizable-panels';
import { DndContext } from '@dnd-kit/core';

import GymChart from '../components/chart/GymChart';
import GymTopBar from '../components/gym/GymTopBar';
// import LeftToolbar from '../components/trading/LeftToolbar'; // Removed in favor of TabBar tools
// import GymFloatingToolbar from '../components/gym/GymFloatingToolbar'; // Removed
import UniversalFloatingToolbar from '../components/trading/UniversalFloatingToolbar'; // Added
import InteractivePositionOverlay from '../components/chart/InteractivePositionOverlay';
import DrawingOverlay from '../components/overlay/DrawingOverlay'; // Added import
import ConfirmTradeModal from '../components/gym/ConfirmTradeModal'; // Keeping for detailed edit if needed? Or relying on overlay confirm?
// Actually overlay confirm is quick. Enhanced modal is good for notes.
// Let's open enhanced modal on overlay confirm.

import { useScreenshot } from '../hooks/useScreenshot';
import { formatPrice } from '../utils/pairFormatting';
import { useTools } from '../context/ToolContext';
import './GymPage.css';

import { dataAPI } from '../services/api'; // Add import
// Removed hardcoded AVAILABLE_PAIRS

export default function GymPage() {
    const [selectedPair, setSelectedPair] = useState('EURUSD');
    const [timeframe, setTimeframe] = useState('M5');
    const [session, setSession] = useState(null);
    const [positions, setPositions] = useState([]); // Confirmed positions
    const [availablePairs, setAvailablePairs] = useState([{ value: 'EURUSD', label: 'EUR/USD' }]); // Default fallback

    // Load available pairs
    useEffect(() => {
        const loadPairs = async () => {
            try {
                const pairs = await dataAPI.getPairs();
                // Format for dropdown (value=EURUSD, label=EURUSD or EUR/USD)
                const formatted = pairs.map(p => ({
                    value: p,
                    label: p.length === 6 ? `${p.slice(0, 3)}/${p.slice(3)}` : p
                }));
                setAvailablePairs(formatted);
            } catch (e) {
                console.error("Failed to load pairs", e);
            }
        };
        loadPairs();
    }, []);

    // Tools State - use global context + local override for floating tools
    const { activeTool: globalActiveTool, setActiveTool: setGlobalActiveTool } = useTools();
    const [localActiveTool, setLocalActiveTool] = useState(null); // For floating toolbar specifics like long/short

    // Derived active tool (local takes precedence or logic to mix?)
    // Long/Short are in GymFloatingToolbar. Trendline etc are in TabBar (Global).
    // Let's treat them as shared space.
    const activeTool = localActiveTool || globalActiveTool;

    // Active Drawing Position State
    // Steps: null -> 'placing' -> 'modifying' -> (confirm) -> null
    const [activePosition, setActivePosition] = useState(null);
    const [positionStep, setPositionStep] = useState('idle'); // idle, placing, modifying

    const [toolbarPos, setToolbarPos] = useState({ x: 100, y: 100 });

    const chartRef = useRef(null); // { chart, series, container }
    const chartWrapperRef = useRef(null); // Wrapper containing chart + overlays
    const { captureChart, saveScreenshot } = useScreenshot();

    // Reset tools when switching
    useEffect(() => {
        if (globalActiveTool && localActiveTool) {
            setLocalActiveTool(null); // Global tool selected (Sidebar), clear local
        }
    }, [globalActiveTool]);

    // Start Session
    const startSession = async () => {
        try {
            // Fetch account settings to link balance
            let initialBalance = 50000;
            try {
                // Determine balance from account settings
                // Can import fetchChallenge or just basic fetch if lazy
                const accResp = await fetch('http://localhost:9000/api/challenges/1');
                if (accResp.ok) {
                    const accData = await accResp.json();
                    initialBalance = accData.starting_balance || 50000;
                }
            } catch (e) {
                console.warn("Could not fetch account balance, using default", e);
            }

            // Mock session creation valid for UI testing, use real API in prod
            const resp = await fetch('http://localhost:9000/api/trainer/sessions', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    id: crypto.randomUUID(),
                    name: `Gym ${selectedPair} ${new Date().toLocaleDateString()}`,
                    symbol: selectedPair,
                    start_date: new Date().toISOString(),
                    end_date: new Date().toISOString(),
                    initial_balance: initialBalance
                }),
            });
            if (!resp.ok) throw new Error("Failed to start session");
            const data = await resp.json();
            setSession(data);
        } catch (err) {
            console.error(err);
            alert("Failed to start session. Check console.");
        }
    };

    const endSession = () => {
        setSession(null);
        setPositions([]);
        setActivePosition(null);
        // Optionally save session summary to backend?
    };

    // Tool Selection (Local Tools like Long/Short)
    const handleToolSelect = (toolId) => {
        if (!session) return;

        if (toolId === 'cursor') {
            setLocalActiveTool(null);
            setGlobalActiveTool(null);
            setActivePosition(null);
            setPositionStep('idle');
            return;
        }

        if (toolId === 'long' || toolId === 'short') {
            setLocalActiveTool(toolId);
            setGlobalActiveTool(null); // Clear global tool
            setPositionStep('placing');
            setActivePosition(null); // Clear any current working position
        } else {
            // For tools in FloatingBar that might duplicate Sidebar
            setLocalActiveTool(toolId);
        }
    };

    // Sync positionStep with activeTool (Global Tool Selection)
    useEffect(() => {
        if (activeTool === 'long' || activeTool === 'short') {
            setPositionStep('placing');
            setActivePosition(null); // Reset active position for new placement
        } else {
            // If switching away from long/short (e.g. to cursor or drawing tool), stop placing
            if (positionStep === 'placing') {
                setPositionStep('idle');
            }
        }
    }, [activeTool]);

    // Click on Chart (to place position)
    useEffect(() => {
        const checkClick = (e) => {
            // Only handle if in placing mode and clicking on chart wrapper
            if (positionStep !== 'placing') return;
            if (!chartRef.current || !chartRef.current.chart) return;
        };
    }, [positionStep]);

    // Handler for chart click (passed to wrapper div)
    const handleChartContainerClick = (e) => {
        if (positionStep !== 'placing' || !activeTool) return;
        if (!chartRef.current) return;

        // Support for Global Drawing Tools (Placeholder logic) - HANDLED BY DrawingOverlay
        // If activeTool is 'trendline', handle drawing...
        // if (['trendline', 'hline', 'fib', 'triangle', 'circle', 'text'].includes(activeTool)) {
        //     console.log("Drawing tool click:", activeTool);
        //     // Implement drawing logic here or forward to separate hook
        //     return;
        // }

        const { chart, series, container } = chartRef.current;
        const rect = container.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;

        const price = series.coordinateToPrice(y);
        const time = chart.timeScale().coordinateToTime(x);

        if (!price || !time) return;

        if (activeTool === 'long' || activeTool === 'short') {
            // Set initial position
            const entry = price;
            const dist = price * 0.001; // 0.1% default dist
            const sl = activeTool === 'long' ? entry - dist : entry + dist;
            const tp = activeTool === 'long' ? entry + (dist * 2) : entry - (dist * 2);

            setActivePosition({
                type: activeTool === 'long' ? 'LONG' : 'SHORT',
                entry,
                sl,
                tp,
                entryTime: time * 1000,
                exitTime: (time + 3000) * 1000 // default 5 candles forward? (assuming M1=60s, M5=300s)
                // We need to know timeframe interval to set reasonable default width
                // For now just add some arbitrary seconds, logic in overlay uses coords
            });

            setPositionStep('modifying');
            // setLocalActiveTool('cursor'); // Optional: reset or stay in tool
        }
    };

    // Update active position from overlay drag
    const handleUpdatePosition = (newPos) => {
        setActivePosition(newPos);
    };

    const handleConfirmPosition = async () => {
        if (!activePosition || !session) return;

        // 1. Log Trade to Backend
        try {
            // Prepare payload for trainer API
            const tradePayload = {
                id: crypto.randomUUID(), // Generate ID here or let backend do it
                session_id: session.id,
                symbol: selectedPair,
                entry_time: new Date(activePosition.entryTime).toISOString(),
                type: activePosition.type,
                entry_price: activePosition.entry,
                sl_price: activePosition.sl,
                tp_price: activePosition.tp,
                exit_time: new Date(activePosition.exitTime).toISOString() // Planned exit
            };

            const resp = await fetch(`http://localhost:9000/api/trainer/sessions/${session.id}/trades`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(tradePayload)
            });

            if (!resp.ok) throw new Error("Failed to log trade");
            const savedTrade = await resp.json();

            // 2. Capture & Upload Screenshot
            let screenshot = null;
            try {
                // Use wrapper ref to capture everything (chart + overlays)
                screenshot = await captureChart(chartWrapperRef);
                if (screenshot) {
                    const screenshotUrl = `http://localhost:9000/api/trainer/sessions/${session.id}/trades/${savedTrade.id}/screenshot`;
                    await saveScreenshot(screenshot, savedTrade.id, screenshotUrl);
                }
            } catch (e) { console.warn("Screenshot failed", e); }

            // 3. Update Local State
            const confirmed = {
                ...activePosition,
                id: savedTrade.id, // Use backend ID
                screenshot_path: screenshot ? 'uploaded' : null,
                notes: '',
                outcome: 'PENDING' // Trainer API sets it too
            };

            setPositions([...positions, confirmed]);
            setActivePosition(null);
            setPositionStep('idle');

            // Optional: Toast success
            console.log("Trade confirmed and recorded:", savedTrade.id);

        } catch (err) {
            console.error("Failed to confirm trade", err);
            alert("Failed to save trade. Check console.");
        }
    };

    const handleCancelPosition = () => {
        setActivePosition(null);
        setPositionStep('idle');
    };

    return (
        <DndContext>
            <div className="gym-page">
                {/* Top Bar */}
                <GymTopBar
                    timeframe={timeframe}
                    setTimeframe={setTimeframe}
                    pair={selectedPair}
                    setPair={setSelectedPair}
                    availablePairs={availablePairs}
                    activeTool={activeTool}
                    onToolSelect={handleToolSelect}
                    onStartSession={startSession}
                    onEndSession={endSession}
                    sessionName={session?.name}
                    disabled={!session}
                />

                <PanelGroup direction="horizontal">
                    <Panel defaultSize={80} minSize={50}>
                        <div className="gym-chart-section">
                            {/* Left Toolbar Removed - Using Global TabBar */}

                            {/* Chart Wrapper */}
                            <div
                                ref={chartWrapperRef}
                                className="chart-container-wrapper"
                                style={{ position: 'relative', flex: 1, cursor: activeTool ? 'crosshair' : 'default' }}
                                onClick={handleChartContainerClick}
                            >
                                <GymChart
                                    ref={chartRef}
                                    pair={selectedPair}
                                    timeframe={timeframe}
                                    positions={positions}
                                />

                                {chartRef.current && (
                                    <DrawingOverlay
                                        chart={chartRef.current.chart}
                                        series={chartRef.current.series}
                                        containerRef={{ current: chartRef.current.container }}
                                    />
                                )}

                                {/* Confirmed Positions Overlays */}
                                {chartRef.current && positions.map((p) => (
                                    <InteractivePositionOverlay
                                        key={p.id}
                                        chartContainerRef={{ current: chartRef.current.container }}
                                        chart={chartRef.current.chart}
                                        series={chartRef.current.series}
                                        activePosition={p}
                                        readOnly={true} // Assuming component supports this or ignores interaction if callbacks missing
                                        onUpdatePosition={() => { }}
                                        onConfirm={() => { }}
                                        onCancel={() => { }}
                                    />
                                ))}

                                {/* Interactive Overlay (Active Placement) */}
                                {positionStep === 'modifying' && activePosition && chartRef.current && (
                                    <InteractivePositionOverlay
                                        chartContainerRef={{ current: chartRef.current.container }}
                                        chart={chartRef.current.chart}
                                        series={chartRef.current.series}
                                        activePosition={activePosition}
                                        onUpdatePosition={handleUpdatePosition}
                                        onConfirm={handleConfirmPosition}
                                        onCancel={handleCancelPosition}
                                    />
                                )}
                            </div>

                            {/* Floating Toolbar Removed */}
                        </div>
                    </Panel>

                    <PanelResizeHandle className="panel-resize-handle" />

                    <Panel defaultSize={20} minSize={10}>
                        {/* Right Panel (Positions List) */}
                        <div className="gym-panel">
                            <div className="panel-header">Positions</div>
                            <div className="panel-content">
                                {positions.map(p => (
                                    <div key={p.id} className="position-card">
                                        {p.type} @ {formatPrice(p.entry, selectedPair)}
                                        {/* Add more details */}
                                    </div>
                                ))}
                            </div>
                        </div>
                    </Panel>
                </PanelGroup>
            </div>
        </DndContext>
    );
}
