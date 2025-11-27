/**
 * Custom hook for fetching SMC analysis
 */
import { useState, useEffect, useCallback } from 'react';
import axios from 'axios';

const API_BASE_URL = 'http://localhost:9000/api';

export function useSMCAnalysis(pair, timeframe, limit = 1000) {
    const [swingData, setSwingData] = useState(null);
    const [orderBlockData, setOrderBlockData] = useState(null);
    const [marketStructureData, setMarketStructureData] = useState(null);
    const [fvgData, setFvgData] = useState(null);
    const [liquidityData, setLiquidityData] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const fetchAnalysis = useCallback(async () => {
        if (!pair || !timeframe) return;

        setLoading(true);
        setError(null);

        try {
            // Fetch all SMC data in parallel
            const [swingsResponse, obResponse, msResponse, fvgResponse, liqResponse] = await Promise.all([
                axios.get(`${API_BASE_URL}/analysis/swings`, {
                    params: { pair, timeframe, limit },
                }),
                axios.get(`${API_BASE_URL}/analysis/order-blocks`, {
                    params: { pair, timeframe, limit },
                }),
                axios.get(`${API_BASE_URL}/analysis/market-structure`, {
                    params: { pair, timeframe, limit },
                }),
                axios.get(`${API_BASE_URL}/analysis/fvg`, {
                    params: { pair, timeframe, limit },
                }),
                axios.get(`${API_BASE_URL}/analysis/liquidity`, {
                    params: { pair, timeframe, limit },
                }),
            ]);

            setSwingData(swingsResponse.data);
            setOrderBlockData(obResponse.data);
            setMarketStructureData(msResponse.data);
            setFvgData(fvgResponse.data);
            setLiquidityData(liqResponse.data);
        } catch (err) {
            setError(err.message || 'Failed to fetch SMC analysis');
            console.error('Error fetching SMC analysis:', err);
        } finally {
            setLoading(false);
        }
    }, [pair, timeframe, limit]);

    useEffect(() => {
        fetchAnalysis();
    }, [fetchAnalysis]);

    return { swingData, orderBlockData, marketStructureData, fvgData, liquidityData, loading, error, refetch: fetchAnalysis };
}
