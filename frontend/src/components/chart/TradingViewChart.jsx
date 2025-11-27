/**
 * TradingView Lightweight Charts wrapper
 */
import React, { useEffect, useRef } from 'react';
import { createChart } from 'lightweight-charts';
import { useChartOverlay } from '../../hooks/useChartOverlay';
import { drawPositions, clearPositions } from '../../utils/positionVisualizer';
import '../../styles/TradingViewChart.css';

export default function TradingViewChart({ 
    data, 
    pair, 
    swingData, 
    orderBlockData, 
    marketStructureData, 
    fvgData, 
    liquidityData,
    ranges,
    signals,
    timeframe,
    showPositions = true // Toggle for position visualization
}) {
    const chartContainerRef = useRef(null);
    const chartRef = useRef(null);
    const candleSeriesRef = useRef(null);
    const positionVisualsRef = useRef({ lines: [], series: [] });

    // Use canvas overlay for all SMC visualizations
    useChartOverlay(
        chartContainerRef,
        chartRef,
        candleSeriesRef,
        orderBlockData,
        fvgData,
        liquidityData,
        marketStructureData
    );

    // Initialize chart
    useEffect(() => {
        if (!chartContainerRef.current) return;

        const chart = createChart(chartContainerRef.current, {
            width: chartContainerRef.current.clientWidth,
            height: chartContainerRef.current.clientHeight,
            layout: {
                background: { color: '#1e222d' },
                textColor: '#d1d4dc',
            },
            grid: {
                vertLines: { color: '#2b2b43' },
                horzLines: { color: '#2b2b43' },
            },
            crosshair: {
                mode: 0, // Normal mode - no magnet
            },
            rightPriceScale: {
                borderColor: '#485c7b',
            },
            timeScale: {
                borderColor: '#485c7b',
                timeVisible: true,
                secondsVisible: false,
            },
        });

        chartRef.current = chart;

        // Add candlestick series
        const candleSeries = chart.addCandlestickSeries({
            upColor: '#26a69a',
            downColor: '#ef5350',
            borderUpColor: '#26a69a',
            borderDownColor: '#ef5350',
            wickUpColor: '#26a69a',
            wickDownColor: '#ef5350',
        });

        candleSeriesRef.current = candleSeries;

        // Volume removed for cleaner UI

        // Handle resize
        const handleResize = () => {
            if (chartContainerRef.current && chartRef.current) {
                chartRef.current.applyOptions({
                    width: chartContainerRef.current.clientWidth,
                    height: chartContainerRef.current.clientHeight,
                });
            }
        };

        window.addEventListener('resize', handleResize);

        return () => {
            window.removeEventListener('resize', handleResize);
            if (chartRef.current) {
                chartRef.current.remove();
            }
        };
    }, []);

    // Update chart data when data changes
    useEffect(() => {
        if (!data || !data.candles || !candleSeriesRef.current) return;

        // Format data for lightweight-charts
        const candleData = data.candles.map((candle) => ({
            time: new Date(candle.timestamp).getTime() / 1000, // Unix timestamp in seconds
            open: candle.open,
            high: candle.high,
            low: candle.low,
            close: candle.close,
        }));

        candleSeriesRef.current.setData(candleData);

        // Fit content
        if (chartRef.current) {
            chartRef.current.timeScale().fitContent();
        }
    }, [data]);

    // Add swing points markers (NO market structure markers - those are lines on canvas)
    useEffect(() => {
        if (!candleSeriesRef.current) return;

        // Clear markers if no data
        if (!swingData) {
            candleSeriesRef.current.setMarkers([]);
            return;
        }

        const markers = [];

        // Add swing highs and lows
        swingData.swing_highs.forEach((swing) => {
            markers.push({
                time: new Date(swing.timestamp).getTime() / 1000,
                position: 'aboveBar',
                color: '#ef5350',
                shape: 'arrowDown',
                text: 'H',
            });
        });

        swingData.swing_lows.forEach((swing) => {
            markers.push({
                time: new Date(swing.timestamp).getTime() / 1000,
                position: 'belowBar',
                color: '#26a69a',
                shape: 'arrowUp',
                text: 'L',
            });
        });

        // IMPORTANT: Sort markers by time (ascending) - required by lightweight-charts
        markers.sort((a, b) => a.time - b.time);

        candleSeriesRef.current.setMarkers(markers);
    }, [swingData]);

    // Draw positions (TradingView style with Entry, SL, TP)
    useEffect(() => {
        if (!candleSeriesRef.current || !signals || !chartRef.current || !showPositions) return;

        // Clear old visuals
        clearPositions(candleSeriesRef.current, chartRef.current, positionVisualsRef.current);

        // Draw new positions
        positionVisualsRef.current = drawPositions(
            chartRef.current,
            candleSeriesRef.current,
            signals
        );

        // Also add entry markers
        const markers = [];
        signals.forEach(signal => {
            markers.push({
                time: new Date(signal.time).getTime() / 1000,
                position: signal.type === 'LONG' ? 'belowBar' : 'aboveBar',
                color: signal.type === 'LONG' ? '#26a69a' : '#ef5350',
                shape: signal.type === 'LONG' ? 'arrowUp' : 'arrowDown',
                text: signal.type === 'LONG' ? 'L' : 'S',
            });
        });

        markers.sort((a, b) => a.time - b.time);
        candleSeriesRef.current.setMarkers(markers);
    }, [signals, showPositions]);

    return (
        <div className="chart-container">
            <div ref={chartContainerRef} className="chart-inner" />
            {!data && (
                <div className="chart-loading">
                    <div className="loading-spinner"></div>
                    <p>Loading chart data...</p>
                </div>
            )}
        </div>
    );
}
