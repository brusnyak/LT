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
            ...options, // start, end, limit
        };

        const response = await api.get('/data/candles', { params });
        return response.data;
    },

    /**
     * Get available pairs
     */
    async getPairs() {
        const response = await api.get('/data/pairs');
        return response.data.pairs;
    },

    /**
     * Get available timeframes
     */
    async getTimeframes() {
        const response = await api.get('/data/timeframes');
        return response.data.timeframes;
    },

    /**
     * Get date range for pair/timeframe
     */
    async getDateRange(pair, timeframe) {
        const response = await api.get('/data/date-range', {
            params: { pair, timeframe },
        });
        return response.data;
    },
};

export default api;
