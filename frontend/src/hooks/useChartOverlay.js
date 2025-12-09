/**
 * Enhanced canvas overlay for all SMC visualizations:
 * - Order Blocks (grey boxes)
 * - FVG (Fair Value Gaps - colored boxes)
 * - Liquidity Zones (horizontal lines)
 * - Market Structure (lines from pivot to break point)
 */
import { useEffect, useRef } from 'react';

export function useChartOverlay(
    chartContainerRef,
    chartRef,
    candleSeriesRef,
    orderBlockData,
    fvgData,
    liquidityData,
    marketStructureData,
    premiumDiscountZones, // Add new prop
    // New visibility props
    showSwings,
    showMarketStructure,
    showOrderBlocks,
    showFvgs,
    showLiquidity,
    showPremiumDiscount
) {
    const canvasRef = useRef(null);

    useEffect(() => {
        if (!chartContainerRef.current || !chartRef.current || !candleSeriesRef.current) return;

        // Create overlay canvas
        const canvas = document.createElement('canvas');
        canvas.style.position = 'absolute';
        canvas.style.top = '0';
        canvas.style.left = '0';
        canvas.style.pointerEvents = 'none';
        canvas.style.zIndex = '1';

        chartContainerRef.current.appendChild(canvas);
        canvasRef.current = canvas;

        const resizeCanvas = () => {
            if (!chartContainerRef.current || !canvasRef.current) return;
            const rect = chartContainerRef.current.getBoundingClientRect();
            canvasRef.current.width = rect.width;
            canvasRef.current.height = rect.height;
            drawAll();
        };

        const drawAll = () => {
            if (!canvasRef.current || !chartRef.current || !candleSeriesRef.current) return;

            const ctx = canvasRef.current.getContext('2d');
            const width = canvasRef.current.width;
            const height = canvasRef.current.height;
            const pixelRatio = window.devicePixelRatio || 1;

            // Handle high-DPI displays
            canvasRef.current.width = width * pixelRatio;
            canvasRef.current.height = height * pixelRatio;
            ctx.scale(pixelRatio, pixelRatio);
            canvasRef.current.style.width = `${width}px`;
            canvasRef.current.style.height = `${height}px`;

            // Clear canvas
            ctx.clearRect(0, 0, width, height);

            const timeScale = chartRef.current.timeScale();
            const visibleRange = timeScale.getVisibleLogicalRange();
            if (!visibleRange) return;

            // Helper to get X coordinate safely (handles off-screen)
            const getX = (time) => {
                const coord = timeScale.timeToCoordinate(time);
                if (coord !== null) return coord;

                // If null, check if it's before or after visible range
                // We can estimate based on logical index if we had it, but for now:
                // If time is older than visible start, return negative
                const visibleStartTime = timeScale.coordinateToTime(0);
                if (visibleStartTime && time < visibleStartTime) return -1000;
                return width + 1000; // Off-screen right
            };

            // 1. Draw Order Blocks with mitigation levels and Breaker Blocks
            if (orderBlockData && showOrderBlocks) {
                orderBlockData.order_blocks.forEach((ob) => {
                    const obTime = new Date(ob.timestamp).getTime() / 1000;
                    const x1 = getX(obTime);

                    // Limit to 20 bars forward
                    const barWidth = timeScale.options().barSpacing || 6;
                    const x2 = x1 + (20 * barWidth);

                    // Skip if completely off-screen
                    if (x2 < 0 || x1 > width) return;

                    const yHigh = candleSeriesRef.current.priceToCoordinate(ob.high);
                    const yLow = candleSeriesRef.current.priceToCoordinate(ob.low);
                    const yMid = candleSeriesRef.current.priceToCoordinate(ob.mid);
                    if (yHigh === null || yLow === null || yMid === null) return;

                    const boxWidth = Math.max(1, x2 - x1);
                    const rectY = Math.min(yHigh, yLow);
                    const rectHeight = Math.abs(yLow - yHigh);

                    // Determine colors based on type and state
                    const isBullish = ob.type === 'bullish';
                    const isBreaker = ob.is_breaker || false;
                    const mitigationLevel = ob.mitigation_level || 0;

                    // Base colors
                    let baseColor = isBullish ? '38, 166, 154' : '239, 83, 80'; // Teal for bullish, Red for bearish

                    // Adjust opacity based on mitigation level
                    // Level 0: 0.15, Level 1: 0.12, Level 2: 0.10, Level 3: 0.08, Level 4: 0.05
                    const fillOpacity = Math.max(0.05, 0.15 - (mitigationLevel * 0.025));
                    const borderOpacity = Math.max(0.2, 0.4 - (mitigationLevel * 0.05));

                    // Draw rectangle
                    ctx.fillStyle = `rgba(${baseColor}, ${fillOpacity})`;
                    ctx.fillRect(x1, rectY, boxWidth, rectHeight);

                    // Border style
                    ctx.strokeStyle = `rgba(${baseColor}, ${borderOpacity})`;
                    ctx.lineWidth = isBreaker ? 2 : 1;

                    // Dashed border for Breaker Blocks
                    if (isBreaker) {
                        ctx.setLineDash([5, 5]);
                    }

                    ctx.strokeRect(x1, rectY, boxWidth, rectHeight);
                    ctx.setLineDash([]);

                    // 50% mid-line
                    ctx.strokeStyle = `rgba(${baseColor}, ${borderOpacity + 0.2})`;
                    ctx.setLineDash([4, 4]);
                    ctx.beginPath();
                    ctx.moveTo(x1, yMid);
                    ctx.lineTo(x1 + boxWidth, yMid);
                    ctx.stroke();
                    ctx.setLineDash([]);

                    // Label for Breaker Blocks
                    if (isBreaker) {
                        ctx.fillStyle = `rgba(${baseColor}, 0.8)`;
                        ctx.font = '10px sans-serif';
                        ctx.fillText('BREAKER', x1 + 5, rectY + 12);
                    }

                    // Mitigation level indicator
                    if (mitigationLevel > 0) {
                        ctx.fillStyle = `rgba(${baseColor}, 0.6)`;
                        ctx.font = '9px sans-serif';
                        const levelText = `${mitigationLevel * 25}%`;
                        ctx.fillText(levelText, x1 + 5, rectY + (isBreaker ? 24 : 12));
                    }
                });
            }

            // 2. Draw FVG - end when filled (price touches it)
            if (fvgData && showFvgs) {
                fvgData.fvgs.forEach((fvg) => {
                    // Skip if filled - don't show filled FVGs
                    if (fvg.filled) return;

                    const fvgTime = new Date(fvg.timestamp).getTime() / 1000;
                    const x1 = getX(fvgTime);

                    const yTop = candleSeriesRef.current.priceToCoordinate(fvg.top);
                    const yBottom = candleSeriesRef.current.priceToCoordinate(fvg.bottom);
                    if (yTop === null || yBottom === null) return;

                    // Extend to visible range end
                    const x2 = timeScale.logicalToCoordinate(visibleRange.to);

                    // Skip if completely off-screen
                    if (x2 < 0 || x1 > width) return;

                    const boxWidth = Math.max(1, x2 - x1);
                    const rectY = Math.min(yTop, yBottom);
                    const rectHeight = Math.abs(yBottom - yTop);

                    // Color based on type
                    const isBullish = fvg.type === 'bullish';
                    const fillColor = isBullish ? 'rgba(38, 166, 154, 0.1)' : 'rgba(239, 83, 80, 0.1)';
                    const borderColor = isBullish ? 'rgba(38, 166, 154, 0.4)' : 'rgba(239, 83, 80, 0.4)';

                    // Draw FVG box
                    ctx.fillStyle = fillColor;
                    ctx.fillRect(x1, rectY, boxWidth, rectHeight);
                    ctx.strokeStyle = borderColor;
                    ctx.lineWidth = 1;
                    ctx.setLineDash([2, 2]);
                    ctx.strokeRect(x1, rectY, boxWidth, rectHeight);
                    ctx.setLineDash([]);
                });
            }

            // 3. Draw Liquidity - different styles for Session, EQH/EQL, and Swing
            if (liquidityData && showLiquidity) {
                liquidityData.liquidity_zones.forEach((liq) => {
                    // Skip swept liquidity
                    if (liq.swept) return;

                    const liqTime = new Date(liq.timestamp).getTime() / 1000;
                    const x1 = getX(liqTime);

                    const y = candleSeriesRef.current.priceToCoordinate(liq.price);
                    if (y === null) return;

                    // Extend to visible range
                    const x2 = timeScale.logicalToCoordinate(visibleRange.to);

                    // Skip if completely off-screen
                    if (x2 < 0 || x1 > width) return;

                    const isBSL = liq.type === 'buy_side';
                    const subtype = liq.subtype || 'swing_high';

                    // Determine color and style based on subtype
                    let color, lineWidth, dashPattern;

                    if (subtype === 'session_high' || subtype === 'session_low') {
                        // Session liquidity - thicker, solid lines
                        color = isBSL ? 'rgba(239, 83, 80, 0.9)' : 'rgba(38, 166, 154, 0.9)';
                        lineWidth = 2.5;
                        dashPattern = [];
                    } else if (subtype === 'eqh' || subtype === 'eql') {
                        // Equal Highs/Lows - dotted lines
                        color = isBSL ? 'rgba(251, 191, 36, 0.9)' : 'rgba(168, 85, 247, 0.9)'; // Yellow/Purple
                        lineWidth = 2;
                        dashPattern = [2, 3];
                    } else {
                        // Swing liquidity - standard
                        color = isBSL ? 'rgba(239, 83, 80, 0.7)' : 'rgba(38, 166, 154, 0.7)';
                        lineWidth = 1.5;
                        dashPattern = [];
                    }

                    // Draw line from swing point forward
                    ctx.strokeStyle = color;
                    ctx.lineWidth = lineWidth;
                    ctx.setLineDash(dashPattern);
                    ctx.beginPath();
                    ctx.moveTo(x1, y);
                    ctx.lineTo(x2, y);
                    ctx.stroke();
                    ctx.setLineDash([]);

                    // Add label for Session and EQH/EQL
                    if (subtype !== 'swing_high' && subtype !== 'swing_low') {
                        ctx.fillStyle = color;
                        ctx.font = '9px sans-serif';
                        let label = '';
                        if (subtype === 'session_high' || subtype === 'session_low') {
                            label = liq.session ? `${liq.session.toUpperCase()} ${subtype.split('_')[1].toUpperCase()}` : 'SESSION';
                        } else if (subtype === 'eqh') {
                            label = 'EQH';
                        } else if (subtype === 'eql') {
                            label = 'EQL';
                        }
                        ctx.fillText(label, x1 + 5, y - 3);
                    }
                });
            }

            // 4. Draw Market Structure Lines (already handled by markers in TradingViewChart.jsx, but keeping for completeness if needed for lines)
            // This section is effectively redundant if markers are used for BOS/CHOCH.
            // However, if we want to draw lines *between* pivots for structure, this would be the place.
            // For now, we'll keep it as is, but it won't be controlled by a new prop as it's already handled by markers.
            if (marketStructureData && showMarketStructure) { // Added showMarketStructure check
                marketStructureData.structure_events.forEach((event) => {
                    const pivotTime = new Date(event.pivot_timestamp).getTime() / 1000;
                    const breakTime = new Date(event.timestamp).getTime() / 1000;

                    const x1 = getX(pivotTime);
                    const x2 = getX(breakTime);

                    // Skip if completely off-screen
                    if (Math.max(x1, x2) < 0 || Math.min(x1, x2) > width) return;

                    const y = candleSeriesRef.current.priceToCoordinate(event.price);
                    if (y === null) return;

                    const isBOS = event.type === 'BOS';
                    const color = isBOS ? '#3b82f6' : '#f59e0b';

                    // Draw line from pivot to break point
                    ctx.strokeStyle = color;
                    ctx.lineWidth = 2;
                    ctx.setLineDash(isBOS ? [] : [4, 4]);
                    ctx.beginPath();
                    ctx.moveTo(x1, y);
                    ctx.lineTo(x2, y);
                    ctx.stroke();
                    ctx.setLineDash([]);

                    // Add label
                    const midX = (x1 + x2) / 2;
                    // Only draw label if visible
                    if (midX > 0 && midX < width) {
                        ctx.fillStyle = color;
                        ctx.font = '11px sans-serif';
                        ctx.textAlign = 'center';
                        const isBullish = event.direction === 'bullish';
                        const labelY = isBullish ? y + 12 : y - 4;
                        ctx.fillText(event.type, midX, labelY);
                    }
                });
            }

            // 5. Draw Premium/Discount/OTE Zones
            if (premiumDiscountZones && showPremiumDiscount) {
                premiumDiscountZones.forEach((zone) => {
                    const zoneStartTime = new Date(zone.start_time).getTime() / 1000;
                    const zoneEndTime = new Date(zone.end_time).getTime() / 1000;

                    const x1 = getX(zoneStartTime);
                    const x2 = getX(zoneEndTime);

                    // Skip if completely off-screen
                    if (x2 < 0 || x1 > width) return;

                    const yTop = candleSeriesRef.current.priceToCoordinate(zone.top);
                    const yBottom = candleSeriesRef.current.priceToCoordinate(zone.bottom);
                    if (yTop === null || yBottom === null) return;

                    const boxWidth = Math.max(1, x2 - x1);
                    const rectY = Math.min(yTop, yBottom);
                    const rectHeight = Math.abs(yBottom - yTop);

                    // Parse color string (e.g., '#8b5a5a' or 'rgba(R,G,B,A)')
                    let fillColor = zone.color;
                    if (fillColor.startsWith('#')) {
                        // Convert hex to rgba with some opacity
                        const hex = fillColor.slice(1);
                        const r = parseInt(hex.substring(0, 2), 16);
                        const g = parseInt(hex.substring(2, 4), 16);
                        const b = parseInt(hex.substring(4, 6), 16);
                        fillColor = `rgba(${r}, ${g}, ${b}, 0.1)`; // Default opacity for zones
                    } else if (!fillColor.startsWith('rgba')) {
                        fillColor = `rgba(128, 128, 128, 0.1)`; // Fallback to grey with opacity
                    }

                    ctx.fillStyle = fillColor;
                    ctx.fillRect(x1, rectY, boxWidth, rectHeight);

                    // Add a border for OTE zones for emphasis
                    if (zone.type === 'ote') {
                        ctx.strokeStyle = zone.color;
                        ctx.lineWidth = 1;
                        ctx.setLineDash([4, 2]);
                        ctx.strokeRect(x1, rectY, boxWidth, rectHeight);
                        ctx.setLineDash([]);
                    }

                    // Add label for the zone
                    ctx.fillStyle = zone.color;
                    ctx.font = '10px sans-serif';
                    ctx.textAlign = 'left';
                    const labelText = zone.type.toUpperCase();
                    ctx.fillText(labelText, x1 + 5, rectY + 12);
                });
            }
        };

        resizeCanvas();
        window.addEventListener('resize', resizeCanvas);

        const handleChartUpdate = () => {
            requestAnimationFrame(drawAll);
        };

        chartRef.current.timeScale().subscribeVisibleLogicalRangeChange(handleChartUpdate);

        return () => {
            window.removeEventListener('resize', resizeCanvas);
            if (canvasRef.current && chartContainerRef.current) {
                try {
                    chartContainerRef.current.removeChild(canvasRef.current);
                } catch (e) {
                    // Canvas already removed
                }
            }
        };
    }, [
        chartContainerRef, chartRef, candleSeriesRef,
        orderBlockData, fvgData, liquidityData, marketStructureData, premiumDiscountZones,
        // Add new visibility props to dependency array
        showOrderBlocks, showFvgs, showLiquidity, showPremiumDiscount, showMarketStructure
    ]);

    return null;
}
