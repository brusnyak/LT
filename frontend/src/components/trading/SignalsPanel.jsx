import React, { useState, useEffect } from 'react';
import { Radio, Activity, Eye, ArrowRight, Image as ImageIcon, ChevronLeft, ChevronRight, Play, Pause, RefreshCw } from 'lucide-react';
import { fetchHumanTrainedSignals, predictionAPI, acceptSignal, clearTrades, dataAPI } from '../../services/api';
import { useMarket } from '../../context/MarketContext';
import { formatPrice, formatRR } from '../../utils/pairFormatting';
import './SignalsPanel.css';

export default function SignalsPanel({ onPredictionUpdate }) {
    const [activeTab, setActiveTab] = useState('strategy'); // strategy, prediction, vision
    const [signals, setSignals] = useState([]);
    const [signalsByPair, setSignalsByPair] = useState({}); // Store signals per pair
    const [visionUrl, setVisionUrl] = useState('');
    const { pair, setPair, timeframe } = useMarket();
    const [loading, setLoading] = useState(false);
    const [lastRefresh, setLastRefresh] = useState(null);

    // Prediction State
    const [prediction, setPrediction] = useState(null);
    const [currentSplit, setCurrentSplit] = useState(2500);
    const [isPlaying, setIsPlaying] = useState(false);
    const [ghostPredictions, setGhostPredictions] = useState([]); // Previous 2 predictions

    const [pairs, setPairs] = useState(['EURUSD', 'GBPUSD', 'USDJPY', 'XAUUSD', 'BTCUSD']); // Default fallback

    // Load available pairs
    useEffect(() => {
        const loadPairs = async () => {
            try {
                const available = await dataAPI.getPairs();
                setPairs(available);
            } catch (e) {
                console.error("Failed to load pairs", e);
            }
        };
        loadPairs();
    }, []);

    // Load signals for current pair
    useEffect(() => {
        if (activeTab === 'strategy') {
            loadSignals();
        }
    }, [activeTab, pair, timeframe]);

    const loadSignals = async () => {
        setLoading(true);
        try {
            const data = await fetchHumanTrainedSignals(pair, timeframe);
            const newSignals = data.signals || [];

            // Store signals for this pair
            setSignalsByPair(prev => ({
                ...prev,
                [pair]: newSignals
            }));

            setSignals(newSignals);
            setLastRefresh(new Date());
        } catch (error) {
            console.error("Failed to load signals:", error);
        } finally {
            setLoading(false);
        }
    };

    const handleAcceptSignal = async (signal) => {
        try {
            await acceptSignal({
                pair: signal.pair || pair,
                type: signal.type,
                entry: signal.entry || signal.price,
                sl: signal.sl,
                tp: signal.tp,
                rr: signal.rr,
                signal_time: signal.time || new Date().toISOString(),
                strategy: 'human_trained',
                challenge_id: 1
            });
            alert('✅ Signal accepted! Check Journal tab to view your trade.');
        } catch (error) {
            console.error('Failed to accept signal:', error);
            alert('❌ Failed to accept signal. Please try again.');
        }
    };

    const handleClearSignals = async () => {
        if (!window.confirm(`Clear all signals for ${pair}? This cannot be undone.`)) {
            return;
        }

        try {
            await clearTrades(1, pair);
            alert(`✅ Cleared signals for ${pair}`);
            loadSignals(); // Refresh
        } catch (err) {
            console.error('Failed to clear signals:', err);
            alert('❌ Failed to clear signals');
        }
    };

    const handleStartPrediction = async () => {
        setLoading(true);
        try {
            // For now, use challenge_id = 1 (hardcoded, will be from context later)
            const challengeId = 1;
            const result = await predictionAPI.start(challengeId, pair, timeframe, currentSplit, 20);

            setPrediction(result);

            // Notify parent component to update chart
            if (onPredictionUpdate) {
                onPredictionUpdate(result);
            }
        } catch (error) {
            console.error("Failed to start prediction:", error);
            alert("Failed to generate prediction. Make sure backend is running.");
        } finally {
            setLoading(false);
        }
    };

    const handleStep = async (direction) => {
        if (!prediction) return;

        setLoading(true);
        try {
            const challengeId = 1;
            const result = await predictionAPI.step(
                pair,
                timeframe,
                challengeId,
                currentSplit,
                direction
            );

            // Save current prediction as ghost
            setGhostPredictions(prev => {
                const updated = [prediction, ...prev].slice(0, 2); // Keep last 2
                return updated;
            });

            // Update with new prediction
            const newPrediction = result.prediction;
            setPrediction(newPrediction);
            setCurrentSplit(result.new_split_index);

            // Notify parent
            if (onPredictionUpdate) {
                onPredictionUpdate(newPrediction, ghostPredictions);
            }
        } catch (error) {
            console.error("Failed to step prediction:", error);
        } finally {
            setLoading(false);
        }
    };

    const handleReset = () => {
        setPrediction(null);
        setGhostPredictions([]);
        setCurrentSplit(2500);
        if (onPredictionUpdate) {
            onPredictionUpdate(null);
        }
    };

    // Auto-play feature
    useEffect(() => {
        if (isPlaying && prediction) {
            const interval = setInterval(() => {
                handleStep('forward');
            }, 2000); // Step every 2 seconds

            return () => clearInterval(interval);
        }
    }, [isPlaying, prediction]);

    return (
        <div className="signals-panel">
            <div className="panel-header">
                <h3>Analysis</h3>
                <div className="panel-tabs">
                    <button
                        className={`tab-btn ${activeTab === 'strategy' ? 'active' : ''}`}
                        onClick={() => setActiveTab('strategy')}
                        title="Strategy Signals"
                    >
                        <Activity size={16} />
                    </button>
                    <button
                        className={`tab-btn ${activeTab === 'prediction' ? 'active' : ''}`}
                        onClick={() => setActiveTab('prediction')}
                        title="Market Prediction"
                    >
                        <Radio size={16} />
                    </button>
                    <button
                        className={`tab-btn ${activeTab === 'vision' ? 'active' : ''}`}
                        onClick={() => setActiveTab('vision')}
                        title="Vision Mode"
                    >
                        <Eye size={16} />
                    </button>
                </div>
            </div>

            <div className="panel-content">
                {activeTab === 'strategy' && (
                    <div className="strategy-container">
                        <div className="strategy-header">
                            <div className="strategy-info">
                                <h4>Human-Trained Strategy</h4>
                                <p className="strategy-desc">SMC-based · 92% Win Rate · 4.5 R:R</p>
                            </div>
                            <button
                                className="refresh-btn"
                                onClick={loadSignals}
                                disabled={loading}
                                title="Refresh signals"
                            >
                                <RefreshCw size={16} className={loading ? 'spinning' : ''} />
                            </button>
                        </div>

                        <div className="selectors-group">
                            <div className="selector-item">
                                <label>Asset</label>
                                <select
                                    value={pair}
                                    onChange={(e) => setPair(e.target.value)}
                                    className="panel-select"
                                >
                                    {pairs.map(p => (
                                        <option key={p} value={p}>{p}</option>
                                    ))}
                                </select>
                            </div>
                        </div>

                        {/* Multi-pair toggle view */}
                        {Object.keys(signalsByPair).length > 1 && (
                            <div className="pair-toggles">
                                {Object.keys(signalsByPair).map(p => (
                                    <button
                                        key={p}
                                        className={`pair-toggle ${pair === p ? 'active' : ''}`}
                                        onClick={() => {
                                            setPair(p);
                                            setSignals(signalsByPair[p] || []);
                                        }}
                                    >
                                        {p}
                                        <span className="signal-count">{signalsByPair[p]?.length || 0}</span>
                                    </button>
                                ))}
                            </div>
                        )}

                        {lastRefresh && (
                            <div className="last-refresh">
                                Last updated: {lastRefresh.toLocaleTimeString()}
                            </div>
                        )}

                        <div className="signals-actions">
                            <button
                                className="clear-signals-btn"
                                onClick={handleClearSignals}
                                disabled={signals.length === 0}
                            >
                                Clear Signals
                            </button>
                        </div>

                        <div className="signals-list">
                            {loading ? (
                                <div className="loading-signals">Loading...</div>
                            ) : signals.length === 0 ? (
                                <div className="no-signals">No active signals</div>
                            ) : (
                                signals.map((signal, index) => (
                                    <div key={index} className={`signal-item ${signal.type.toLowerCase()}`}>
                                        <div className="signal-header">
                                            <span className="signal-type-badge">{signal.type}</span>
                                            <span className="signal-rr">{signal.rr?.toFixed(1)}R</span>
                                        </div>
                                        <div className="signal-prices">
                                            <div className="price-row">
                                                <span className="label">Entry:</span>
                                                <span className="value">{formatPrice(signal.entry || signal.price, signal.pair || pair)}</span>
                                            </div>
                                            <div className="price-row sl">
                                                <span className="label">SL:</span>
                                                <span className="value">{formatPrice(signal.sl, signal.pair || pair)}</span>
                                            </div>
                                            <div className="price-row tp">
                                                <span className="label">TP:</span>
                                                <span className="value">{formatPrice(signal.tp, signal.pair || pair)}</span>
                                            </div>
                                        </div>
                                        {signal.poi_type && (
                                            <div className="signal-meta">
                                                <span className="poi-badge">{signal.poi_type}</span>
                                                {signal.structure && <span className="structure-badge">{signal.structure}</span>}
                                            </div>
                                        )}
                                        <button
                                            className="accept-signal-btn"
                                            onClick={() => handleAcceptSignal(signal)}
                                        >
                                            Accept Trade
                                        </button>
                                    </div>
                                ))
                            )}
                        </div>
                    </div>
                )}

                {activeTab === 'prediction' && (
                    <div className="prediction-container">
                        {!prediction ? (
                            <>
                                <div className="mode-info">
                                    <h4>📈 Market Prediction</h4>
                                    <p>Statistical pattern analysis with multi-strategy ensemble</p>
                                </div>

                                <div className="prediction-config">
                                    <label>Split Index:</label>
                                    <input
                                        type="number"
                                        value={currentSplit}
                                        onChange={(e) => setCurrentSplit(parseInt(e.target.value))}
                                        min={100}
                                        max={4500}
                                        className="split-input"
                                    />
                                    <small>Position in data to start prediction</small>
                                </div>

                                <button
                                    className="btn-action"
                                    onClick={handleStartPrediction}
                                    disabled={loading}
                                >
                                    {loading ? 'Generating...' : 'Generate Prediction'} <ArrowRight size={16} />
                                </button>
                            </>
                        ) : (
                            <div className="prediction-active">
                                {/* Prediction Info */}
                                <div className="prediction-badge">
                                    <div className={`direction-badge ${prediction.direction.toLowerCase()}`}>
                                        {prediction.direction}
                                    </div>
                                    <div className="confidence-score">
                                        {prediction.confidence.toFixed(1)}% confidence
                                    </div>
                                </div>

                                {/* Targets */}
                                <div className="prediction-targets">
                                    <div className="target-item">
                                        <span className="target-label">Target High:</span>
                                        <span className="target-value">{formatPrice(prediction.target_high, pair)}</span>
                                    </div>
                                    <div className="target-item">
                                        <span className="target-label">Target Low:</span>
                                        <span className="target-value">{formatPrice(prediction.target_low, pair)}</span>
                                    </div>
                                    <div className="target-item">
                                        <span className="target-label">Reversal:</span>
                                        <span className="target-value">{formatPrice(prediction.reversal_point, pair)}</span>
                                    </div>
                                </div>

                                {/* Time Controls */}
                                <div className="time-controls">
                                    <button
                                        onClick={() => handleStep('backward')}
                                        disabled={loading || currentSplit <= 100}
                                        className="control-btn"
                                    >
                                        <ChevronLeft size={16} />
                                    </button>

                                    <div className="split-display">
                                        <span>Split: {currentSplit}</span>
                                    </div>

                                    <button
                                        onClick={() => setIsPlaying(!isPlaying)}
                                        className="control-btn play-btn"
                                    >
                                        {isPlaying ? <Pause size={16} /> : <Play size={16} />}
                                    </button>

                                    <button
                                        onClick={() => handleStep('forward')}
                                        disabled={loading || currentSplit >= 3000}
                                        className="control-btn"
                                    >
                                        <ChevronRight size={16} />
                                    </button>
                                </div>

                                {/* Pattern Analysis */}
                                {prediction.pattern_analysis && (
                                    <div className="pattern-info">
                                        <h5>Pattern Analysis</h5>
                                        <div className="pattern-detail">
                                            <span>Trend Strength:</span>
                                            <span>{prediction.pattern_analysis.trend?.strength?.toFixed(0)}%</span>
                                        </div>
                                        <div className="pattern-detail">
                                            <span>Momentum:</span>
                                            <span>{prediction.pattern_analysis.trend?.momentum?.toFixed(2)}%</span>
                                        </div>
                                    </div>
                                )}

                                {/* Ghost Lines Info */}
                                {ghostPredictions.length > 0 && (
                                    <div className="ghost-info">
                                        <small>Showing {ghostPredictions.length} previous prediction(s)</small>
                                    </div>
                                )}

                                {/* Reset Button */}
                                <button
                                    className="btn-secondary"
                                    onClick={handleReset}
                                >
                                    Reset Prediction
                                </button>
                            </div>
                        )}
                    </div>
                )}

                {activeTab === 'vision' && (
                    <div className="mode-container">
                        <div className="mode-info">
                            <h4>👁️ Vision Mode</h4>
                            <p>Analyze chart screenshots for SMC setups.</p>
                        </div>
                        <div className="input-group">
                            <label>Image URL / Link</label>
                            <div className="url-input-wrapper">
                                <ImageIcon size={16} />
                                <input
                                    type="text"
                                    placeholder="Paste TradingView image link..."
                                    value={visionUrl}
                                    onChange={(e) => setVisionUrl(e.target.value)}
                                />
                            </div>
                        </div>
                        <button className="btn-action">
                            Analyze Chart <Eye size={16} />
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
}