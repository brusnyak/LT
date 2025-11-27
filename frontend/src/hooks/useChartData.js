/**
 * Custom hook for fetching chart data
 */
import { useState, useEffect, useCallback } from 'react';
import { dataAPI } from '../services/api';

export function useChartData(pair, timeframe, limit = 1000) {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const fetchData = useCallback(async () => {
        if (!pair || !timeframe) return;

        setLoading(true);
        setError(null);

        try {
            const response = await dataAPI.getCandles(pair, timeframe, { limit });
            setData(response);
        } catch (err) {
            setError(err.message || 'Failed to fetch chart data');
            console.error('Error fetching chart data:', err);
        } finally {
            setLoading(false);
        }
    }, [pair, timeframe, limit]);

    useEffect(() => {
        fetchData();
    }, [fetchData]);

    return { data, loading, error, refetch: fetchData };
}
