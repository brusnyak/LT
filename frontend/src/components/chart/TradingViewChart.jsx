import React, { useEffect, useRef, forwardRef, useImperativeHandle } from 'react';
import { createChart } from 'lightweight-charts';
import { useChartOverlay } from '../../hooks/useChartOverlay';
import { drawPositions, clearPositions } from '../../utils/positionVisualizer';
import { getPriceScaleOptions } from '../../utils/pairFormatting';
import '../../styles/TradingViewChart.css';

const TradingViewChart = forwardRef(({
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
    showPositions = true,
    showSignals = true,
    predictionData,
    ghostPredictions = [],
    premiumDiscountZones,
    showSwings,
    showMarketStructure,
    showOrderBlocks,
    showFvgs,
    showLiquidity,
    showPremiumDiscount
}, ref) => {
    const chartContainerRef = useRef(null);
    const chartRef = useRef(null);
    const candleSeriesRef = useRef(null);
    const predictedSeriesRef = useRef(null);
    const ghostSeriesRefs = useRef([]);
    const positionVisualsRef = useRef({ lines: [], series: [] });

    useImperativeHandle(ref, () => ({
        chart: chartRef.current,
        series: candleSeriesRef.current,
        container: chartContainerRef.current
    }));

    // Use canvas overlay for all SMC visualizations
    useChartOverlay(
        chartContainerRef,
        chartRef,
        candleSeriesRef,
        orderBlockData,
        fvgData,
        liquidityData,
        marketStructureData,
        premiumDiscountZones, // Pass to useChartOverlay
        // Pass visibility props to useChartOverlay
        showSwings,
        showMarketStructure,
        showOrderBlocks,
        showFvgs,
        showLiquidity,
        showPremiumDiscount
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
                mode: 0, // CrosshairMode.Normal
            },
            rightPriceScale: {
                borderColor: '#485c7b',
                ...getPriceScaleOptions(pair),
            },
            timeScale: {
                borderColor: '#485c7b',
                timeVisible: true,
                secondsVisible: false,
            },
        });

        chartRef.current = chart;

        // Main candle series
        const candleSeries = chart.addCandlestickSeries({
            upColor: '#26a69a',
            downColor: '#ef5350',
            borderUpColor: '#26a69a',
            borderDownColor: '#ef5350',
            wickUpColor: '#26a69a',
            wickDownColor: '#ef5350',
        });
        candleSeriesRef.current = candleSeries;

        // Predicted candle series (semi-transparent)
        const predictedSeries = chart.addCandlestickSeries({
            upColor: 'rgba(38, 166, 154, 0.5)',
            downColor: 'rgba(239, 83, 80, 0.5)',
            borderUpColor: 'rgba(38, 166, 154, 0.5)',
            borderDownColor: 'rgba(239, 83, 80, 0.5)',
            wickUpColor: 'rgba(38, 166, 154, 0.5)',
            wickDownColor: 'rgba(239, 83, 80, 0.5)',
        });
        predictedSeriesRef.current = predictedSeries;

        // Handle resize
        const handleResize = () => {
            if (chartContainerRef.current && chartRef.current) {
                chartRef.current.applyOptions({
                    width: chartContainerRef.current.clientWidth,
                    height: chartContainerRef.current.clientHeight,
                });
            }
        };

        const resizeObserver = new ResizeObserver(() => {
            handleResize();
        });

        if (chartContainerRef.current) {
            resizeObserver.observe(chartContainerRef.current);
        }

        return () => {
            resizeObserver.disconnect();
            if (chartRef.current) {
                chartRef.current.remove();
            }
        };
    }, []);

    // Update chart data
    useEffect(() => {
        if (!data || !data.candles || !candleSeriesRef.current) return;

        const candleData = data.candles.map((candle) => ({
            time: new Date(candle.timestamp).getTime() / 1000,
            open: candle.open,
            high: candle.high,
            low: candle.low,
            close: candle.close,
        }));

        candleSeriesRef.current.setData(candleData);

        if (chartRef.current && !predictionData) {
            chartRef.current.timeScale().fitContent();
        }
    }, [data]);

    // Handle Prediction Visualization
    useEffect(() => {
        if (!chartRef.current || !predictedSeriesRef.current) return;

        // 1. Clear previous ghost series
        ghostSeriesRefs.current.forEach(series => {
            chartRef.current.removeSeries(series);
        });
        ghostSeriesRefs.current = [];

        // 2. Draw Ghost Predictions (Lines)
        if (ghostPredictions && ghostPredictions.length > 0) {
            ghostPredictions.forEach((ghost, index) => {
                const lineSeries = chartRef.current.addLineSeries({
                    color: `rgba(255, 255, 255, ${0.2 + (index * 0.1)})`, // Fade out older ghosts
                    lineWidth: 1,
                    lineStyle: 2, // Dashed
                    crosshairMarkerVisible: false,
                    lastValueVisible: false,
                    priceLineVisible: false,
                });

                const lineData = ghost.predicted_candles
                    .map(c => ({
                        time: new Date(c.timestamp).getTime() / 1000,
                        value: c.close
                    }))
                    .filter(c => !isNaN(c.time))
                    .sort((a, b) => a.time - b.time);

                lineSeries.setData(lineData);
                ghostSeriesRefs.current.push(lineSeries);
            });
        }

        // 3. Draw Active Prediction
        if (predictionData && predictionData.predicted_candles) {
            const predData = predictionData.predicted_candles
                .map(c => ({
                    time: new Date(c.timestamp).getTime() / 1000,
                    open: c.open,
                    high: c.high,
                    low: c.low,
                    close: c.close
                }))
                .filter(c => !isNaN(c.time))
                .sort((a, b) => a.time - b.time);

            predictedSeriesRef.current.setData(predData);

            // Add markers for targets
            const markers = [];

            // Split point marker
            if (predictionData.split_time) {
                markers.push({
                    time: new Date(predictionData.split_time).getTime() / 1000,
                    position: 'aboveBar',
                    color: '#fb8c00',
                    shape: 'arrowDown',
                    text: 'SPLIT',
                });
            }

            // Target markers
            const lastCandle = predData[predData.length - 1];
            if (lastCandle) {
                if (predictionData.target_high) {
                    // We can't easily draw horizontal lines without plugins, 
                    // so we'll use price lines on the series
                    predictedSeriesRef.current.createPriceLine({
                        price: predictionData.target_high,
                        color: '#4caf50',
                        lineWidth: 2,
                        lineStyle: 2, // Dashed
                        axisLabelVisible: true,
                        title: 'TARGET HIGH',
                    });
                }
                if (predictionData.target_low) {
                    predictedSeriesRef.current.createPriceLine({
                        price: predictionData.target_low,
                        color: '#f44336',
                        lineWidth: 2,
                        lineStyle: 2,
                        axisLabelVisible: true,
                        title: 'TARGET LOW',
                    });
                }
            }

            predictedSeriesRef.current.setMarkers(markers);

        } else {
            predictedSeriesRef.current.setData([]);
        }

    }, [predictionData, ghostPredictions]);

    // Add markers (Swings + Signals)
    useEffect(() => {
        if (!candleSeriesRef.current) return;

        const markers = [];

        if (swingData && showSwings) {
            swingData.swing_highs.forEach((swing) => {
                markers.push({
                    time: new Date(swing.timestamp).getTime() / 1000,
                    position: 'aboveBar',
                    color: '#ef5350',
                    shape: 'arrowDown',
                    text: 'SH',
                });
            });

            swingData.swing_lows.forEach((swing) => {
                markers.push({
                    time: new Date(swing.timestamp).getTime() / 1000,
                    position: 'belowBar',
                    color: '#26a69a',
                    shape: 'arrowUp',
                    text: 'SL',
                });
            });
        }

        if (marketStructureData && marketStructureData.structure_events && showMarketStructure) {
            marketStructureData.structure_events.forEach((event) => {
                const isBullish = event.direction === 'bullish';
                markers.push({
                    time: new Date(event.timestamp).getTime() / 1000,
                    position: isBullish ? 'belowBar' : 'aboveBar',
                    color: isBullish ? '#26a69a' : '#ef5350',
                    shape: isBullish ? 'arrowUp' : 'arrowDown',
                    text: event.type, // 'BOS' or 'CHOCH'
                });
            });
        }

        if (signals && showSignals) {
            signals.forEach(signal => {
                markers.push({
                    time: new Date(signal.time).getTime() / 1000,
                    position: signal.type === 'LONG' ? 'belowBar' : 'aboveBar',
                    color: signal.type === 'LONG' ? '#26a69a' : '#ef5350',
                    shape: signal.type === 'LONG' ? 'arrowUp' : 'arrowDown',
                    text: signal.type === 'LONG' ? 'L' : 'S',
                });
            });
        }

        markers.sort((a, b) => a.time - b.time);
        candleSeriesRef.current.setMarkers(markers);
    }, [swingData, signals, showSignals]);

    // Draw positions
    useEffect(() => {
        if (!candleSeriesRef.current || !signals || !chartRef.current || !showPositions) return;
        clearPositions(candleSeriesRef.current, chartRef.current, positionVisualsRef.current);
        positionVisualsRef.current = drawPositions(
            chartRef.current,
            candleSeriesRef.current,
            signals,
            data  // Pass chart data to calculate proper closeTime
        );
    }, [signals, showPositions, data]);

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
});

export default TradingViewChart;
