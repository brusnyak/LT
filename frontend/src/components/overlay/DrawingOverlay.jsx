import React, { useState, useRef, useEffect } from 'react';
import { useTools } from '../../context/ToolContext';
import { useDrawings } from '../../context/DrawingContext';
import { Trash2 } from 'lucide-react';
import './DrawingOverlay.css';

export default function DrawingOverlay({ chart, series, containerRef }) {
    const { activeTool, setActiveTool } = useTools();
    const { drawings, addDrawing, updateDrawing, removeDrawing, selectedDrawingId, setSelectedDrawingId } = useDrawings();

    // Interaction State
    const [dragStart, setDragStart] = useState(null); // { x, y, time, price }
    const [currentPoint, setCurrentPoint] = useState(null); // { x, y, time, price }
    const [isDrawing, setIsDrawing] = useState(false);

    // Tools managed by this overlay
    const draggingTools = ['trendline', 'rect', 'triangle', 'circle', 'text', 'fib', 'hline'];
    // Logic to determine if overlay should capture events
    const isDrawingTool = draggingTools.includes(activeTool);

    // Helper to get coords
    const getCoords = (e) => {
        if (!containerRef.current || !chart || !series) return null;
        const rect = containerRef.current.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        const price = series.coordinateToPrice(y);
        const time = chart.timeScale().coordinateToTime(x);
        return { x, y, price, time };
    };

    // Coordinate conversion for rendering
    const toXY = (time, price) => {
        if (!chart || !series) return { x: -100, y: -100 };
        const x = chart.timeScale().timeToCoordinate(time);
        const y = series.priceToCoordinate(price);
        return { x: x ?? -100, y: y ?? -100 };
    };

    const handleMouseDown = (e) => {
        if (!isDrawingTool && activeTool !== 'cursor' && activeTool !== 'eraser') return; // Pass through for other tools like 'long'

        if (activeTool === 'cursor') {
            setSelectedDrawingId(null);
            return;
        }

        if (activeTool === 'eraser') {
            // Eraser click handled by shape click
            return;
        }

        // Start Drawing
        const coords = getCoords(e);
        if (!coords || !coords.time) return;

        setDragStart(coords);
        setCurrentPoint(coords);
        setIsDrawing(true);
    };

    const handleMouseMove = (e) => {
        if (!isDrawing) return;
        const coords = getCoords(e);
        if (coords) setCurrentPoint(coords);
    };

    const handleMouseUp = () => {
        if (!isDrawing) return;

        if (dragStart && currentPoint) {
            // Create Drawing
            const drawing = {
                type: activeTool,
                points: [
                    { time: dragStart.time, price: dragStart.price },
                    { time: currentPoint.time, price: currentPoint.price }
                ],
                style: {
                    color: '#2962ff',
                    lineWidth: 2,
                    text: activeTool === 'text' ? 'Text' : ''
                }
            };

            // Handle specific tool logic
            if (activeTool === 'text') {
                const text = prompt("Enter text:", "Text");
                if (text) {
                    drawing.style.text = text;
                    addDrawing(drawing);
                }
            } else {
                addDrawing(drawing);
            }
        }

        setIsDrawing(false);
        setDragStart(null);
        setCurrentPoint(null);

        // Reset to cursor? User preference usually "continuous drawing" is shift-click, default auto-reset.
        // For now, let's keep tool active for multiple drawings.
        // setActiveTool('cursor'); 
    };

    // Interaction with existing drawings
    const handleDrawingClick = (e, id) => {
        e.stopPropagation(); // Stop bubbling to chart (which might deselect)

        if (activeTool === 'eraser') {
            removeDrawing(id);
            return;
        }
        // If cursor or drawing tool, select it
        if (!isDrawing) {
            setSelectedDrawingId(id);
        }
    };

    // Re-render on chart scroll/zoom
    const [, setTick] = useState(0);
    useEffect(() => {
        if (!chart) return;
        const update = () => setTick(t => t + 1);
        chart.timeScale().subscribeVisibleLogicalRangeChange(update);
        return () => chart.timeScale().unsubscribeVisibleLogicalRangeChange(update);
    }, [chart]);


    return (
        <div
            className="drawing-overlay"
            style={{
                position: 'absolute',
                top: 0,
                left: 0,
                right: 0,
                bottom: 0,
                pointerEvents: isDrawingTool ? 'auto' : 'none', // Capture only if drawing tool
                zIndex: 10
            }}
            onMouseDown={handleMouseDown}
            onMouseMove={handleMouseMove}
            onMouseUp={handleMouseUp}
        >
            <svg style={{ width: '100%', height: '100%', pointerEvents: 'none' }}>
                <defs>
                    <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="10" refY="3.5" orient="auto">
                        <polygon points="0 0, 10 3.5, 0 7" fill="#2962ff" />
                    </marker>
                </defs>

                {/* Existing Drawings */}
                {drawings.map(d => {
                    const p1 = toXY(d.points[0].time, d.points[0].price);
                    const p2 = d.points.length > 1 ? toXY(d.points[1].time, d.points[1].price) : p1;

                    const isSelected = selectedDrawingId === d.id;
                    const stroke = isSelected ? '#ff9800' : (d.style?.color || '#2962ff');
                    const strokeWidth = d.style?.lineWidth || 2;

                    let element = null;

                    switch (d.type) {
                        case 'trendline':
                            element = <line x1={p1.x} y1={p1.y} x2={p2.x} y2={p2.y} stroke={stroke} strokeWidth={strokeWidth} />;
                            break;
                        case 'hline':
                            element = <line x1={0} y1={p1.y} x2={'100%'} y2={p1.y} stroke={stroke} strokeWidth={strokeWidth} />;
                            break;
                        case 'rect':
                            {
                                const x = Math.min(p1.x, p2.x);
                                const y = Math.min(p1.y, p2.y);
                                const w = Math.abs(p2.x - p1.x);
                                const h = Math.abs(p2.y - p1.y);
                                element = <rect x={x} y={y} width={w} height={h} fill={stroke} fillOpacity={0.2} stroke={stroke} strokeWidth={strokeWidth} />;
                            }
                            break;
                        case 'circle':
                            {
                                const r = Math.sqrt(Math.pow(p2.x - p1.x, 2) + Math.pow(p2.y - p1.y, 2));
                                element = <circle cx={p1.x} cy={p1.y} r={r} fill="transparent" stroke={stroke} strokeWidth={strokeWidth} />;
                            }
                            break;
                        case 'triangle':
                            {
                                const midX = (p1.x + p2.x) / 2;
                                element = <polygon points={`${midX},${p1.y} ${p2.x},${p2.y} ${p1.x},${p2.y}`} fill={stroke} fillOpacity={0.2} stroke={stroke} strokeWidth={strokeWidth} />;
                            }
                            break;
                        case 'fib':
                            {
                                const dy = p2.y - p1.y;
                                const levels = [0, 0.236, 0.382, 0.5, 0.618, 0.786, 1];
                                element = (
                                    <g>
                                        <line x1={p1.x} y1={p1.y} x2={p2.x} y2={p2.y} stroke={stroke} strokeWidth={1} strokeDasharray="4 4" opacity={0.5} />
                                        {levels.map(level => {
                                            const y = p1.y + (dy * level);
                                            return (
                                                <g key={level}>
                                                    <line x1={Math.min(p1.x, p2.x)} y1={y} x2={Math.max(p1.x, p2.x)} y2={y} stroke={stroke} strokeWidth={1} />
                                                    <text x={Math.max(p1.x, p2.x) + 5} y={y} fill={stroke} fontSize="10">{level}</text>
                                                </g>
                                            );
                                        })}
                                    </g>
                                );
                            }
                            break;
                        case 'text':
                            element = (
                                <text x={p1.x} y={p1.y} fill={stroke} fontSize="14" fontFamily="sans-serif">
                                    {d.style?.text || 'Text'}
                                </text>
                            );
                            break;
                        default:
                            return null;
                    }

                    return (
                        <g
                            key={d.id}
                            onClick={(e) => handleDrawingClick(e, d.id)}
                            style={{
                                cursor: activeTool === 'eraser' ? 'not-allowed' : 'pointer',
                                pointerEvents: 'auto' // Important: Allow clicking drawings even if overlay pass-through is active (via parent? No parent is none)
                                // Wait, if parent div is pointerEvents: none, children with pointerEvents: auto will capture? Yes.
                            }}
                        >
                            {element}
                            {isSelected && (
                                <g>
                                    <circle cx={p1.x} cy={p1.y} r={4} fill="#fff" stroke="#ff9800" />
                                    {d.points.length > 1 && <circle cx={p2.x} cy={p2.y} r={4} fill="#fff" stroke="#ff9800" />}
                                </g>
                            )}
                        </g>
                    );
                })}

                {/* Preview Current Drawing */}
                {isDrawing && dragStart && currentPoint && (
                    <g opacity={0.6}>
                        {(() => {
                            const p1 = toXY(dragStart.time, dragStart.price);
                            const p2 = toXY(currentPoint.time, currentPoint.price);
                            // ... same switches for preview ...
                            switch (activeTool) {
                                case 'trendline': return <line x1={p1.x} y1={p1.y} x2={p2.x} y2={p2.y} stroke="#2962ff" strokeWidth={2} />;
                                case 'rect': { const x = Math.min(p1.x, p2.x); const y = Math.min(p1.y, p2.y); const w = Math.abs(p2.x - p1.x); const h = Math.abs(p2.y - p1.y); return <rect x={x} y={y} width={w} height={h} fill="#2962ff" fillOpacity={0.2} stroke="#2962ff" strokeWidth={2} />; }
                                case 'circle': { const r = Math.sqrt(Math.pow(p2.x - p1.x, 2) + Math.pow(p2.y - p1.y, 2)); return <circle cx={p1.x} cy={p1.y} r={r} fill="transparent" stroke="#2962ff" strokeWidth={2} />; }
                                case 'triangle': { const midX = (p1.x + p2.x) / 2; return <polygon points={`${midX},${p1.y} ${p2.x},${p2.y} ${p1.x},${p2.y}`} fill="#2962ff" fillOpacity={0.2} stroke="#2962ff" strokeWidth={2} />; }
                                case 'fib': { const dy = p2.y - p1.y; const levels = [0, 0.5, 1]; return <g><line x1={p1.x} y1={p1.y} x2={p2.x} y2={p2.y} stroke="#2962ff" strokeWidth={1} strokeDasharray="4 4" />{levels.map(l => <line key={l} x1={Math.min(p1.x, p2.x)} y1={p1.y + dy * l} x2={Math.max(p1.x, p2.x)} y2={p1.y + dy * l} stroke="#2962ff" />)}</g>; }
                                default: return null;
                            }
                        })()}
                    </g>
                )}
            </svg>

            {/* Delete button for selected */}
            {selectedDrawingId && (
                <div style={{ position: 'absolute', top: 10, right: 10, background: 'rgba(0,0,0,0.7)', padding: 5, borderRadius: 4, cursor: 'pointer', pointerEvents: 'auto' }} onClick={() => removeDrawing(selectedDrawingId)}>
                    <Trash2 size={16} color="#fff" />
                </div>
            )}
        </div>
    );
}
