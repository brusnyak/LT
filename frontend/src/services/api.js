/**
 * API client for backend communication
 */
import axios from 'axios';

const API_BASE_URL = 'http://localhost:9000/api';

const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

export const dataAPI = {
    /**
     * Fetch candle data
     */
    async getCandles(pair, timeframe, options = {}) {
        const params = {
            pair,
            timeframe,
            ...options, // start, end, limit, source
        };

        const response = await api.get('/data/candles', { params });
        return response.data;
    },

    /**
     * Fetch available pairs
     */
    async getPairs() {
        const response = await api.get('/data/pairs');
        return response.data.pairs;
    },

    // ... (rest of object)
};

export const fetchCandles = async (pair, timeframe, limit, start = null, end = null, source = 'csv') => {
    return dataAPI.getCandles(pair, timeframe, { limit, start, end, source });
};

export const fetchHumanTrainedSignals = async (pair, timeframe, limit = 5000) => {
    const response = await axios.get(`${API_BASE_URL}/analysis/human-trained`, {
        params: { pair, timeframe, limit }
    });
    return response.data;
};

export const fetchSignalsList = async (pair, strategy = 'human_trained') => {
    // Redirect all strategies to human-trained for now
    return fetchHumanTrainedSignals(pair);
};

export const fetchJournal = async (pair, timeframe = 'M15') => {
    const response = await api.get('/analysis/journal', { params: { pair, timeframe } });
    return response.data;
};

export const fetchStatsSummary = async (pair = 'EURUSD', timeframe = 'M15') => {
    const response = await api.get('/stats/summary', { params: { pair, timeframe } });
    return response.data;
};

// Trades API
export const acceptSignal = async (signal) => {
    const response = await api.post('/trades/accept', signal);
    return response.data;
};

export const fetchTrades = async (challengeId = 1, pair = null) => {
    const response = await api.get('/trades/', { params: { challenge_id: challengeId, pair } });
    return response.data;
};

export const deleteTrade = async (tradeId) => {
    const response = await api.delete(`/trades/${tradeId}`);
    return response.data;
};

export const clearTrades = async (challengeId = 1, pair = null) => {
    const response = await api.delete('/trades/clear', { params: { challenge_id: challengeId, pair } });
    return response.data;
};

export const closeTrade = async (tradeId, closePrice, outcome) => {
    const response = await api.patch(`/trades/${tradeId}/close`, null, { 
        params: { close_price: closePrice, outcome } 
    });
    return response.data;
};

export const fetchBacktestResults = async () => {
    const response = await api.get('/backtest/run');
    return response.data;
};

export const fetchSwings = async (pair, timeframe) => {
    const response = await api.get('/analysis/swings', { params: { pair, timeframe } });
    return response.data;
};

export const fetchOrderBlocks = async (pair, timeframe) => {
    const response = await api.get('/analysis/order-blocks', { params: { pair, timeframe } });
    return response.data;
};

export const fetchFVGs = async (pair, timeframe) => {
    const response = await api.get('/analysis/fvg', { params: { pair, timeframe } });
    return response.data;
};

export const fetchLiquidity = async (pair, timeframe) => {
    const response = await api.get('/analysis/liquidity', { params: { pair, timeframe } });
    return response.data;
};

// Challenge API
export const fetchChallenge = async (challengeId = 1) => {
    const response = await api.get(`/challenges/${challengeId}`);
    return response.data;
};

export const updateChallenge = async (challengeId, data) => {
    const response = await api.put(`/challenges/${challengeId}`, data);
    return response.data;
};

export const predictionAPI = {
    /**
     * Start a new prediction
     */
    start: async (challengeId, pair, timeframe, splitIndex, numCandles = 20) => {
        const response = await api.post('/prediction/start', {
            challenge_id: challengeId,
            pair,
            timeframe,
            split_index: splitIndex,
            num_candles: numCandles
        });
        return response.data;
    },

    /**
     * Step forward/backward in prediction
     */
    step: async (pair, timeframe, challengeId, currentSplit, direction = 'forward') => {
        const response = await api.post('/prediction/step', 
            { direction },
            { params: { pair, timeframe, challenge_id: challengeId, current_split: currentSplit } }
        );
        return response.data;
    },

    /**
     * Get prediction history
     */
    getHistory: async (challengeId, pair = null, limit = 50) => {
        const params = { challenge_id: challengeId, limit };
        if (pair) params.pair = pair;
        const response = await api.get('/prediction/history', { params });
        return response.data;
    },

    /**
     * Get specific prediction
     */
    getById: async (predictionId) => {
        const response = await api.get(`/prediction/${predictionId}`);
        return response.data;
    },

    /**
     * Verify prediction accuracy
     */
    verify: async (predictionId) => {
        const response = await api.post(`/prediction/${predictionId}/verify`);
        return response.data;
    },

    /**
     * Get prediction stats for challenge
     */
    stats: async (challengeId) => {
        const response = await api.get(`/prediction/stats/${challengeId}`);
        return response.data;
    }
};

export default api;

