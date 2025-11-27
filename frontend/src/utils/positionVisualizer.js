/**
 * Position Visualizer
 * Draws TradingView-style position boxes with Entry, SL, TP lines
 */

export function drawPositions(chart, candleSeries, signals) {
    if (!chart || !candleSeries || !signals) return [];

    const lines = [];
    const series = [];

    signals.forEach(signal => {
        const color = signal.type === 'LONG' ? 'rgba(38, 166, 154, 0.2)' : 'rgba(239, 83, 80, 0.2)';
        const borderColor = signal.type === 'LONG' ? '#26a69a' : '#ef5350';
        
        const entryTime = new Date(signal.time).getTime() / 1000;
        const closeTime = signal.close_time ? new Date(signal.close_time).getTime() / 1000 : null;

        // Create position box (filled area between entry and SL or TP)
        if (closeTime) {
            // Position is closed - draw box from entry to close
            const positionSeries = chart.addAreaSeries({
                topColor: color,
                bottomColor: color,
                lineColor: 'transparent',
                lineWidth: 0,
                priceLineVisible: false,
                crosshairMarkerVisible: false,
            });

            const positionData = [
                { time: entryTime, value: signal.type === 'LONG' ? signal.sl : signal.price },
                { time: closeTime, value: signal.type === 'LONG' ? signal.sl : signal.price },
            ];

            const topData = [
                { time: entryTime, value: signal.type === 'LONG' ? signal.price : signal.sl },
                { time: closeTime, value: signal.type === 'LONG' ? signal.price : signal.sl },
            ];

            // Use a rectangle-like area
            positionSeries.setData(positionData);
            series.push(positionSeries);
        }

        // Entry line (horizontal from entry time to close or current)
        const entryLine = candleSeries.createPriceLine({
            price: signal.price,
            color: borderColor,
            lineWidth: 2,
            lineStyle: 0, // Solid
            axisLabelVisible: true,
            title: `${signal.type} Entry`,
        });
        lines.push(entryLine);

        // SL line (purple/violet)
        const slLine = candleSeries.createPriceLine({
            price: signal.sl,
            color: '#9c27b0', // Purple like in the image
            lineWidth: 2,
            lineStyle: 2, // Dashed
            axisLabelVisible: true,
            title: 'SL',
        });
        lines.push(slLine);

        // TP line (green for long, red for short)
        const tpLine = candleSeries.createPriceLine({
            price: signal.tp,
            color: signal.type === 'LONG' ? '#26a69a' : '#ef5350',
            lineWidth: 2,
            lineStyle: 2, // Dashed
            axisLabelVisible: true,
            title: 'TP',
        });
        lines.push(tpLine);
    });

    return { lines, series };
}

export function clearPositions(candleSeries, chart, { lines, series }) {
    if (!lines || !series) return;
    
    // Remove price lines
    if (lines && lines.length > 0) {
        lines.forEach(line => {
            try {
                if (line && candleSeries) {
                    candleSeries.removePriceLine(line);
                }
            } catch (e) {
                // Ignore errors if line already removed
            }
        });
    }

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
}
