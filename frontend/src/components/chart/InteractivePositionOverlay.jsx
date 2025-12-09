import React, { useEffect, useState, useRef, useCallback } from 'react';
import { Check, X, Move } from 'lucide-react';
import './InteractivePositionOverlay.css';

/**
 * Interactive Overlay for TradingView-style position tool.
 * Renders on top of the chart and handles dragging of Entry, SL, TP, and Exit.
 */
export default function InteractivePositionOverlay({
    chartContainerRef,
    chart,
    series,
    activePosition,
    onUpdatePosition,
    onConfirm,
    onCancel,
    readOnly = false
}) {
    const [coords, setCoords] = useState(null);
    const [dragging, setDragging] = useState(null); // 'entry', 'sl', 'tp', 'exit', 'whole'
    const overlayRef = useRef(null);

    // Update coordinates on chart interaction
    const updateCoords = useCallback(() => {
        if (!chart || !series || !activePosition) return;

        const timeScale = chart.timeScale();
        const entryY = series.priceToCoordinate(activePosition.entry);
        const slY = series.priceToCoordinate(activePosition.sl);
        const tpY = series.priceToCoordinate(activePosition.tp);

        // Convert time to X
        // Note: This assumes activePosition.entryTime and exitTime are timestamps or string dates
        const entryX = timeScale.timeToCoordinate(activePosition.entryTime / 1000);
        let exitX = timeScale.timeToCoordinate(activePosition.exitTime / 1000);

        // If exit time is not visible (e.g. future or off-screen), handle gracefully?
        // For now let's hope it returns null or coordinate off-screen logic is handled by CSS

        if (entryY === null || entryX === null) {
            setCoords(null);
            return;
        }

        // Determine outcome color
        const isLong = activePosition.type === 'LONG';
        const winColor = 'rgba(38, 166, 154, 0.2)';
        const lossColor = 'rgba(239, 83, 80, 0.2)';

        setCoords({
            entryY,
            slY,
            tpY,
            entryX,
            exitX: exitX ?? entryX + 100, // Default width if undefined
            isLong,
            colors: {
                profit: winColor,
                loss: lossColor
            }
        });
    }, [chart, series, activePosition]);

    // Subscribe to chart updates
    useEffect(() => {
        if (!chart) return;
        chart.timeScale().subscribeVisibleLogicalRangeChange(updateCoords);
        chart.subscribeCrosshairMove(updateCoords); // optional implementation detail for smoothness
        updateCoords();
        return () => {
            chart.timeScale().unsubscribeVisibleLogicalRangeChange(updateCoords);
            chart.unsubscribeCrosshairMove(updateCoords);
        };
    }, [chart, updateCoords]);

    // Handle Dragging
    const handleMouseDown = (e, handleType) => {
        if (readOnly) return; // Disable interaction in read-only mode
        e.stopPropagation();
        setDragging(handleType);
    };

    const handleMouseMove = useCallback((e) => {
        if (!dragging || !chart || !series || readOnly) return;

        const rect = chartContainerRef.current.getBoundingClientRect();
        const y = e.clientY - rect.top;
        const x = e.clientX - rect.left;

        const price = series.coordinateToPrice(y);
        const time = chart.timeScale().coordinateToTime(x);

        if (!price) return;

        const newPos = { ...activePosition };

        if (dragging === 'entry') {
            const diff = price - newPos.entry;
            newPos.entry = price;
            newPos.sl += diff;
            newPos.tp += diff;
        } else if (dragging === 'sl') {
            newPos.sl = price;
        } else if (dragging === 'tp') {
            newPos.tp = price;
        } else if (dragging === 'exit') {
            if (time) newPos.exitTime = time * 1000;
        } else if (dragging === 'whole') {
            // Move the whole box in time (optional)
        }

        onUpdatePosition(newPos);
    }, [dragging, chart, series, activePosition, onUpdatePosition, chartContainerRef, readOnly]);

    const handleMouseUp = () => {
        setDragging(null);
    };

    useEffect(() => {
        if (dragging) {
            window.addEventListener('mousemove', handleMouseMove);
            window.addEventListener('mouseup', handleMouseUp);
            return () => {
                window.removeEventListener('mousemove', handleMouseMove);
                window.removeEventListener('mouseup', handleMouseUp);
            };
        }
    }, [dragging, handleMouseMove]);

    if (!coords) return null;

    const { entryY, slY, tpY, entryX, exitX, isLong, colors } = coords;
    const width = Math.max(20, exitX - entryX);

    // Calculate heights
    const profitHeight = Math.abs(tpY - entryY);
    const lossHeight = Math.abs(slY - entryY);

    // Positions for Profit and Loss Boxes
    const profitTop = Math.min(entryY, tpY);
    const lossTop = Math.min(entryY, slY);

    return (
        <div
            className="position-overlay"
            ref={overlayRef}
            style={{ pointerEvents: 'none' }} // Underlying svg/divs have pointer-events: auto
        >
            {/* Profit Box */}
            <div
                className="zone profit-zone"
                style={{
                    left: entryX,
                    top: profitTop,
                    width: width,
                    height: profitHeight,
                    backgroundColor: colors.profit,
                    border: '1px solid #26a69a'
                }}
            />
            {/* Loss Box */}
            <div
                className="zone loss-zone"
                style={{
                    left: entryX,
                    top: lossTop,
                    width: width,
                    height: lossHeight,
                    backgroundColor: colors.loss,
                    border: '1px solid #ef5350'
                }}
            />

            {/* Handles - Render clickable areas ONLY if not readOnly */}
            {!readOnly && (
                <>
                    {/* TP Handle */}
                    <div
                        className="handle tp-handle"
                        onMouseDown={(e) => handleMouseDown(e, 'tp')}
                        style={{ left: entryX + width / 2, top: tpY, cursor: 'ns-resize' }}
                    >
                        Take Profit
                    </div>

                    {/* SL Handle */}
                    <div
                        className="handle sl-handle"
                        onMouseDown={(e) => handleMouseDown(e, 'sl')}
                        style={{ left: entryX + width / 2, top: slY, cursor: 'ns-resize' }}
                    >
                        Stop Loss
                    </div>

                    {/* Entry Handle */}
                    <div
                        className="handle entry-handle"
                        onMouseDown={(e) => handleMouseDown(e, 'entry')}
                        style={{ left: entryX, top: entryY, width: width, cursor: 'move' }}
                    >
                        Entry
                    </div>

                    {/* Exit/Duration Handle (Right Edge) */}
                    <div
                        className="handle exit-handle"
                        onMouseDown={(e) => handleMouseDown(e, 'exit')}
                        style={{ left: exitX, top: Math.min(tpY, slY), height: Math.abs(tpY - slY), cursor: 'ew-resize' }}
                    />

                    {/* Confirm Overlay */}
                    <div
                        className="confirm-actions"
                        style={{
                            left: exitX + 10,
                            top: entryY
                        }}
                    >
                        <button className="confirm-btn" onClick={onConfirm} style={{ pointerEvents: 'auto' }}>
                            <Check size={16} />
                        </button>
                        <button className="cancel-btn" onClick={onCancel} style={{ pointerEvents: 'auto' }}>
                            <X size={16} />
                        </button>
                    </div>
                </>
            )}
        </div>
    );
}
