import { useState, useCallback } from 'react';

/**
 * Hook for TradingView-style position drawing
 * 4-click workflow: Entry → SL → TP → Exit
 */
export default function usePositionDrawing(chartRef, onPositionComplete) {
    const [drawingState, setDrawingState] = useState({
        active: false,
        mode: null, // 'LONG' or 'SHORT'
        step: 0, // 0: waiting, 1: entry set, 2: sl set, 3: tp set, 4: exit set
        entry: null,
        sl: null,
        tp: null,
        exit: null,
        entryTime: null,
        exitTime: null
    });

    const startDrawing = useCallback((mode) => {
        setDrawingState({
            active: true,
            mode,
            step: 0,
            entry: null,
            sl: null,
            tp: null,
            exit: null,
            entryTime: null,
            exitTime: null
        });
    }, []);

    const cancelDrawing = useCallback(() => {
        setDrawingState({
            active: false,
            mode: null,
            step: 0,
            entry: null,
            sl: null,
            tp: null,
            exit: null,
            entryTime: null,
            exitTime: null
        });
    }, []);

    const handleChartClick = useCallback((event) => {
        if (!drawingState.active || !chartRef.current) return;

        const chart = chartRef.current;
        const canvasPosition = chart.canvas.getBoundingClientRect();
        const x = event.clientX - canvasPosition.left;
        const y = event.clientY - canvasPosition.top;

        // Get price and time from click position
        const xScale = chart.scales.x;
        const yScale = chart.scales.y;
        const price = yScale.getValueForPixel(y);
        const time = xScale.getValueForPixel(x);

        if (!price || !time) return;

        const { mode, step } = drawingState;

        if (step === 0) {
            // Step 1: Set Entry
            setDrawingState(prev => ({
                ...prev,
                step: 1,
                entry: price,
                entryTime: new Date(time)
            }));
        } else if (step === 1) {
            // Step 2: Set SL
            const isValidSL = mode === 'LONG' ? price < drawingState.entry : price > drawingState.entry;
            if (!isValidSL) {
                alert(`SL must be ${mode === 'LONG' ? 'below' : 'above'} entry!`);
                return;
            }
            setDrawingState(prev => ({
                ...prev,
                step: 2,
                sl: price
            }));
        } else if (step === 2) {
            // Step 3: Set TP
            const isValidTP = mode === 'LONG' ? price > drawingState.entry : price < drawingState.entry;
            if (!isValidTP) {
                alert(`TP must be ${mode === 'LONG' ? 'above' : 'below'} entry!`);
                return;
            }

            // Calculate R:R
            const risk = Math.abs(drawingState.entry - drawingState.sl);
            const reward = Math.abs(price - drawingState.entry);
            const rr = (reward / risk).toFixed(2);

            setDrawingState(prev => ({
                ...prev,
                step: 3,
                tp: price,
                rr: parseFloat(rr)
            }));
        } else if (step === 3) {
            // Step 4: Set Exit (actual close)
            const exitTime = new Date(time);
            
            // Validate exit time is after entry
            if (exitTime <= drawingState.entryTime) {
                alert('Exit time must be after entry time!');
                return;
            }

            // Calculate actual PnL
            const pnl = mode === 'LONG' 
                ? price - drawingState.entry 
                : drawingState.entry - price;

            // Determine outcome based on exit price
            let outcome;
            if (mode === 'LONG') {
                if (price >= drawingState.tp) outcome = 'WIN';
                else if (price <= drawingState.sl) outcome = 'LOSS';
                else outcome = 'BE';
            } else {
                if (price <= drawingState.tp) outcome = 'WIN';
                else if (price >= drawingState.sl) outcome = 'LOSS';
                else outcome = 'BE';
            }

            // Complete position
            const position = {
                type: mode,
                entry: drawingState.entry,
                sl: drawingState.sl,
                tp: drawingState.tp,
                exit: price,
                rr: drawingState.rr,
                entryTime: drawingState.entryTime,
                exitTime: exitTime,
                pnl,
                outcome
            };

            onPositionComplete(position);
            cancelDrawing();
        }
    }, [drawingState, chartRef, onPositionComplete, cancelDrawing]);

    const getCurrentStep = useCallback(() => {
        if (!drawingState.active) return null;
        const steps = ['Entry', 'SL', 'TP', 'Exit'];
        return steps[drawingState.step] || null;
    }, [drawingState]);

    return {
        drawingState,
        startDrawing,
        cancelDrawing,
        handleChartClick,
        getCurrentStep
    };
}
