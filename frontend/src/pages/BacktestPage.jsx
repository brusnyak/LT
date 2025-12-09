import React, { useState, useEffect } from 'react';
import { Panel, PanelGroup, PanelResizeHandle } from 'react-resizable-panels';
import { DndContext } from '@dnd-kit/core';
import TradingViewChart from '../components/chart/TradingViewChart';

import SignalsPanel from '../components/trading/SignalsPanel';
import FloatingToolbar from '../components/trading/FloatingToolbar';
import ChartOverlayControls from '../components/trading/ChartOverlayControls';
import BacktestConfig from '../components/backtest/BacktestConfig';
import { fetchCandles, fetchHumanTrainedSignals, fetchBacktestResults } from '../services/api';
import { useSettings } from '../context/SettingsContext';
import { useMarket } from '../context/MarketContext';
import './BacktestPage.css';

export default function BacktestPage() {
    const [candleData, setCandleData] = useState([]);
    const [ranges, setRanges] = useState([]);
    const [signals, setSignals] = useState([]);
    const [loading, setLoading] = useState(true);
    const [backtestResults, setBacktestResults] = useState(null);

    const { isOverlayEnabled } = useSettings();
    const { pair, timeframe } = useMarket();

    useEffect(() => {
        // Load initial data
        const loadData = async () => {
            setLoading(true);
            try {
                const candles = await fetchCandles(pair, timeframe, 1000);
                setCandleData(candles);

                const strategyData = await fetchHumanTrainedSignals(pair, timeframe);
                setRanges([]); // No ranges for HumanTrained strategy
                setSignals(strategyData.signals || []);
            } catch (error) {
                console.error("Failed to load data:", error);
            } finally {
                setLoading(false);
            }
        };

        loadData();
    }, [pair, timeframe]);

    const handleRunBacktest = async (config) => {
        console.log('Running backtest with config:', config);
        try {
            const results = await fetchBacktestResults();
            setBacktestResults(results);
        } catch (error) {
            console.error("Backtest failed:", error);
        }
    };

    if (loading) {
        return (
            <div className="loading-container">
                <div className="loading-spinner"></div>
                <p>Loading Backtest Environment...</p>
            </div>
        );
    }

    const smcToggles = {
        swings: isOverlayEnabled('structure'),
        structure: isOverlayEnabled('structure'),
        orderBlocks: isOverlayEnabled('order_blocks'),
        fvg: isOverlayEnabled('fvgs'),
        liquidity: isOverlayEnabled('liquidity')
    };

    return (
        <DndContext>
            <div className="backtest-page">
                <PanelGroup direction="vertical">
                    {/* Trading View (Top) */}
                    <Panel defaultSize={70} minSize={50}>
                        <div className="backtest-trading-view">
                            <PanelGroup direction="horizontal">


                                <Panel defaultSize={75} minSize={40}>
                                    <div className="chart-section">
                                        <FloatingToolbar />
                                        <ChartOverlayControls />
                                        <TradingViewChart
                                            data={candleData}
                                            ranges={isOverlayEnabled('ranges') ? ranges : []}
                                            signals={signals}
                                            smcToggles={smcToggles}
                                            showPositions={isOverlayEnabled('positions')}
                                        />
                                    </div>
                                </Panel>

                                <PanelResizeHandle className="panel-resize-handle" />

                                <Panel defaultSize={20} minSize={15} maxSize={40}>
                                    <SignalsPanel signals={signals} />
                                </Panel>
                            </PanelGroup>
                        </div>
                    </Panel>

                    {/* Resize Handle */}
                    <PanelResizeHandle className="panel-resize-handle-horizontal" />

                    {/* Config Panel (Bottom) */}
                    <Panel defaultSize={30} minSize={20} maxSize={50}>
                        <BacktestConfig onRunBacktest={handleRunBacktest} />
                    </Panel>
                </PanelGroup>
            </div>
        </DndContext>
    );
}
