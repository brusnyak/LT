import React, { useEffect, useRef, useImperativeHandle, forwardRef } from 'react';
import { createChart } from 'lightweight-charts';
import { fetchCandles } from '../../services/api';
import { getPriceScaleOptions, formatPrice } from '../../utils/pairFormatting';
import './GymChart.css'; // Make sure this CSS exists or create it

const GymChart = forwardRef(({ pair, timeframe, positions = [] }, ref) => {
    const chartContainerRef = useRef(null);
    const chartRef = useRef(null);
    const seriesRef = useRef(null);
    const resizeObserverRef = useRef(null);

    // Expose chart and series to parent
    useImperativeHandle(ref, () => ({
        chart: chartRef.current,
        series: seriesRef.current,
        container: chartContainerRef.current
    }));

    // Initialize Chart
    useEffect(() => {
        if (!chartContainerRef.current) return;

        const chart = createChart(chartContainerRef.current, {
            layout: {
                background: { color: '#131722' },
                textColor: '#d1d4dc',
            },
            grid: {
                vertLines: { color: '#2b2b43' },
                horzLines: { color: '#2b2b43' },
            },
            timeScale: {
                timeVisible: true,
                secondsVisible: false,
                borderColor: '#2b2b43',
            },
            rightPriceScale: {
                borderColor: '#2b2b43',
                ...getPriceScaleOptions(pair)
            },
            crosshair: {
                mode: 0, // CrosshairMode.Normal
                vertLine: {
                    width: 1,
                    color: '#2962ff',
                    style: 3,
                },
                horzLine: {
                    width: 1,
                    color: '#2962ff',
                    style: 3,
                },
            },
        });

        const series = chart.addCandlestickSeries({
            upColor: '#26a69a',
            downColor: '#ef5350',
            borderVisible: false,
            wickUpColor: '#26a69a',
            wickDownColor: '#ef5350',
        });

        chartRef.current = chart;
        seriesRef.current = series;

        // Resize handler
        const handleResize = () => {
            if (chartContainerRef.current) {
                chart.applyOptions({ width: chartContainerRef.current.clientWidth, height: chartContainerRef.current.clientHeight });
            }
        };

        resizeObserverRef.current = new ResizeObserver(handleResize);
        resizeObserverRef.current.observe(chartContainerRef.current);

        return () => {
            if (resizeObserverRef.current) {
                resizeObserverRef.current.disconnect();
            }
            chart.remove();
        };
    }, [pair]);

    // Update Data
    useEffect(() => {
        let isMounted = true;
        if (!seriesRef.current || !pair || !timeframe) return;

        const loadData = async () => {
            try {
                // Fetch data
                // fetchCandles returns the whole response object now: { pair, timeframe, candles: [...], ... }
                // or just the array depending on api.js. 
                // api.js getCandles returns "response.data".
                // backend returns { pair, timeframe, candles: [], ... }
                const data = await fetchCandles(pair, timeframe, 100000);

                if (!isMounted) return;

                if (data && data.candles && Array.isArray(data.candles)) {
                    // Map backend candles to chart format
                    const chartData = data.candles.map(c => ({
                        time: new Date(c.timestamp).getTime() / 1000, // Unix timestamp in seconds
                        open: c.open,
                        high: c.high,
                        low: c.low,
                        close: c.close,
                        // volume: c.volume // optional
                    }));

                    if (seriesRef.current) {
                        seriesRef.current.setData(chartData);
                    }

                    // Adjust scale options for new pair
                    if (chartRef.current) {
                        chartRef.current.applyOptions({
                            rightPriceScale: getPriceScaleOptions(pair)
                        });
                    }
                } else {
                    console.warn(`No candle data found for ${pair} ${timeframe}`);
                }

            } catch (err) {
                console.error("Failed to load chart data:", err);
            }
        };

        loadData();

        return () => {
            isMounted = false;
        };
    }, [pair, timeframe]);

    // Render Confirmed Positions (Static Markers or leave to parent?)
    // If we want interactivity on confirmed positions, parent should render overlays.
    // If we want simple markers:
    useEffect(() => {
        if (!seriesRef.current) return;

        // Example: markers for entries
        const markers = positions.map(pos => ({
            time: pos.entryTime / 1000,
            position: pos.type === 'LONG' ? 'belowBar' : 'aboveBar',
            color: pos.type === 'LONG' ? '#26a69a' : '#ef5350',
            shape: pos.type === 'LONG' ? 'arrowUp' : 'arrowDown',
            text: pos.type
        }));

        // seriesRef.current.setMarkers(markers);
        // Commented out to let overlay handle it if active, but markers are good for history.
    }, [positions]);

    return (
        <div
            ref={chartContainerRef}
            className="gym-chart-container"
            style={{ width: '100%', height: '100%', position: 'relative' }}
        />
    );
});

export default GymChart;
