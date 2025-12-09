import React, { useState, useEffect, useRef } from 'react';
import TradingViewChart from '../chart/TradingViewChart';
import api from '../../services/api';
import './PredictionTab.css';

const PredictionTab = () => {
    const [session, setSession] = useState(null);
    const [loading, setLoading] = useState(false);
    const [playing, setPlaying] = useState(false);
    const [stats, setStats] = useState({ balance: 10000, positions: 0, predictions_made: 0 });

    const playInterval = useRef(null);

    // Start a new session
    const startSession = async () => {
        setLoading(true);
        try {
            const response = await api.post('/prediction/start', {
                pair: 'EURUSD',
                timeframe: '5M',
                limit: 1000,
                start_offset: 200
            });
            setSession(response.data);
            await fetchStats();
        } catch (error) {
            console.error("Failed to start session:", error);
        } finally {
            setLoading(false);
        }
    };

    // Step forward
    const nextStep = async () => {
        try {
            const response = await api.post('/prediction/next');
            setSession(response.data);
            await fetchStats();
        } catch (error) {
            console.error("Failed to step forward:", error);
            stopPlay();
        }
    };

    // Fetch stats
    const fetchStats = async () => {
        try {
            const response = await api.get('/prediction/stats');
            setStats(response.data);
        } catch (error) {
            console.error("Failed to fetch stats:", error);
        }
    };

    // Play/Pause logic
    const togglePlay = () => {
        if (playing) {
            stopPlay();
        } else {
            setPlaying(true);
            playInterval.current = setInterval(nextStep, 1000); // 1 step per second
        }
    };

    const stopPlay = () => {
        setPlaying(false);
        if (playInterval.current) {
            clearInterval(playInterval.current);
            playInterval.current = null;
        }
    };

    // Cleanup on unmount
    useEffect(() => {
        return () => stopPlay();
    }, []);

    if (!session && !loading) {
        return (
            <div className="prediction-intro">
                <h2>🔮 Prediction Mode</h2>
                <p>Test your skills or validate the strategy by replaying historical data.</p>
                <button className="btn-primary" onClick={startSession}>
                    Start New Session (EURUSD)
                </button>
            </div>
        );
    }

    return (
        <div className="prediction-tab">
            <div className="prediction-controls">
                <div className="control-group">
                    <button className="btn-control" onClick={startSession}>
                        🔄 Reset
                    </button>
                    <button className={`btn-control ${playing ? 'active' : ''}`} onClick={togglePlay}>
                        {playing ? '⏸ Pause' : '▶ Play'}
                    </button>
                    <button className="btn-control" onClick={nextStep} disabled={playing}>
                        ⏭ Step
                    </button>
                </div>

                <div className="stats-group">
                    <div className="stat-item">
                        <span className="label">Progress</span>
                        <span className="value">{session?.progress.toFixed(1)}%</span>
                    </div>
                    <div className="stat-item">
                        <span className="label">Prediction</span>
                        <span className={`value ${session?.last_prediction?.direction}`}>
                            {session?.last_prediction?.direction || 'WAITING'}
                        </span>
                    </div>
                    <div className="stat-item">
                        <span className="label">Confidence</span>
                        <span className="value">
                            {session?.last_prediction ? (session.last_prediction.confidence * 100).toFixed(0) + '%' : '-'}
                        </span>
                    </div>
                </div>
            </div>

            <div className="prediction-chart">
                {session && (
                    <TradingViewChart
                        data={session.candles}
                        ranges={[]} // TODO: Add ranges if needed
                        signals={[]} // TODO: Add signals if needed
                        smcToggles={{}}
                        showPositions={false}
                        height="100%"
                    />
                )}
            </div>
        </div>
    );
};

export default PredictionTab;
