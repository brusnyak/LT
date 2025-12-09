/**
 * Position Visualizer
 * Draws TradingView-style position boxes with Entry, SL, TP lines
 * Uses finite lines (LineSeries) instead of infinite PriceLines to reduce clutter.
 */

export function drawPositions(chart, candleSeries, signals, chartData) {
    if (!chart || !candleSeries || !signals || signals.length === 0) return { lines: [], series: [] };

    const series = [];
    
    // Get the last visible candle time from chart data
    // This prevents positions from extending beyond the chart
    let lastVisibleTime = Date.now() / 1000;
    if (chartData && chartData.candles && chartData.candles.length > 0) {
        const lastCandle = chartData.candles[chartData.candles.length - 1];
        lastVisibleTime = new Date(lastCandle.timestamp).getTime() / 1000;
    }

    signals.forEach(signal => {
        // Handle both 'entry' and 'price' fields
        const entryPrice = signal.entry || signal.price;
        if (!entryPrice || !signal.sl || !signal.tp) return; // Skip invalid signals

        const entryTime = signal.time 
            ? new Date(signal.time).getTime() / 1000 
            : lastVisibleTime;
        
        // Calculate closeTime based on when SL/TP would be hit
        // For now, extend to last visible candle or a reasonable duration
        // In future, we can calculate actual hit time from historical data
        const closeTime = signal.close_time 
            ? new Date(signal.close_time).getTime() / 1000 
            : Math.min(lastVisibleTime, entryTime + (60 * 60 * 24)); // Max 24 hours or last candle

        // Colors - Updated per requirements
        const profitFillColor = 'rgba(255, 152, 0, 0.15)'; // Orange TP with low opacity
        const lossFillColor = 'rgba(171, 71, 188, 0.15)';   // Purple SL with low opacity
        const entryColor = '#787b86';
        const tpLineColor = '#ff9800'; // Orange for TP
        const slLineColor = '#ab47bc'; // Purple for SL
        
        // 1. Profit Zone (Baseline Series)
        // For LONG: Value = TP, Base = Entry. Top = Orange.
        // For SHORT: Value = TP, Base = Entry. Bottom = Orange.
        
        const profitSeries = chart.addBaselineSeries({
            baseValue: { type: 'price', price: entryPrice },
            topFillColor1: signal.type === 'LONG' ? profitFillColor : 'transparent',
            topFillColor2: signal.type === 'LONG' ? profitFillColor : 'transparent',
            bottomFillColor1: signal.type === 'SHORT' ? profitFillColor : 'transparent',
            bottomFillColor2: signal.type === 'SHORT' ? profitFillColor : 'transparent',
            topLineColor: 'transparent',
            bottomLineColor: 'transparent',
            lineWidth: 0,
            crosshairMarkerVisible: false,
            lastValueVisible: false,
            priceLineVisible: false,
            autoscaleInfoProvider: () => null, // Prevent affecting scale
        });
        
        const profitData = [
            { time: entryTime, value: signal.tp },
            { time: closeTime, value: signal.tp },
        ];
        profitSeries.setData(profitData);
        series.push(profitSeries);

        // 2. Loss Zone (Baseline Series)
        // For LONG: Value = SL, Base = Entry. Bottom = Purple.
        // For SHORT: Value = SL, Base = Entry. Top = Purple.
        
        const lossSeries = chart.addBaselineSeries({
            baseValue: { type: 'price', price: entryPrice },
            topFillColor1: signal.type === 'SHORT' ? lossFillColor : 'transparent',
            topFillColor2: signal.type === 'SHORT' ? lossFillColor : 'transparent',
            bottomFillColor1: signal.type === 'LONG' ? lossFillColor : 'transparent',
            bottomFillColor2: signal.type === 'LONG' ? lossFillColor : 'transparent',
            topLineColor: 'transparent',
            bottomLineColor: 'transparent',
            lineWidth: 0,
            crosshairMarkerVisible: false,
            lastValueVisible: false,
            priceLineVisible: false,
            autoscaleInfoProvider: () => null,
        });
        
        const lossData = [
            { time: entryTime, value: signal.sl },
            { time: closeTime, value: signal.sl },
        ];
        lossSeries.setData(lossData);
        series.push(lossSeries);

        // 3. Finite Lines (Entry, SL, TP) using LineSeries
        // This avoids infinite horizontal lines across the chart
        
        // Helper to create a finite line segment
        const createLineSegment = (price, color, width = 2, style = 0, title = '') => {
            const lineSeries = chart.addLineSeries({
                color: color,
                lineWidth: width,
                lineStyle: style,
                crosshairMarkerVisible: false,
                lastValueVisible: true,
                priceLineVisible: false,
                autoscaleInfoProvider: () => null,
                title: title // Add title for legend
            });
            
            lineSeries.setData([
                { time: entryTime, value: price },
                { time: closeTime, value: price }
            ]);
            
            series.push(lineSeries);
            return lineSeries;
        };

        // Entry Line (Solid Grey, thinner)
        createLineSegment(entryPrice, entryColor, 1, 0, 'Entry');

        // SL Line (Solid Purple, thicker)
        createLineSegment(signal.sl, slLineColor, 2, 0, 'SL');

        // TP Line (Solid Orange, thicker)
        createLineSegment(signal.tp, tpLineColor, 2, 0, 'TP');
        
        // TP2 Line (Dashed Orange, if exists)
        if (signal.tp2) {
            createLineSegment(signal.tp2, tpLineColor, 2, 2, 'TP2');
        }
    });

    return { lines: [], series }; // No price lines returned, only series
}

export function clearPositions(candleSeries, chart, { lines, series }) {
    // Remove series
    if (series && series.length > 0) {
        series.forEach(s => {
            try {
                if (s && chart) {
                    chart.removeSeries(s);
                }
            } catch (e) {
                // Ignore errors if series already removed
            }
        });
    }
    
    // Legacy support for lines if any passed
    if (lines && lines.length > 0) {
        lines.forEach(line => {
            try {
                if (line && candleSeries) {
                    candleSeries.removePriceLine(line);
                }
            } catch (e) {
                // Ignore
            }
        });
    }
}
