/**
 * Strategy API Service
 */

const API_BASE_URL = 'http://localhost:9000/api';

export const strategyApi = {
    /**
     * Fetch 4H Range Strategy Analysis
     */
    async getRange4HStrategy(pair) {
        const response = await fetch(`${API_BASE_URL}/analysis/range-4h?pair=${pair}`);
        if (!response.ok) {
            throw new Error(`Failed to fetch strategy: ${response.statusText}`);
        }
        return response.json();
    },

    /**
     * Fetch Unified SMC Strategy Analysis
     */
    async getUnifiedSMCStrategy(pair, timeframeH4 = 'H4', timeframeM15 = 'M15', timeframeM5 = 'M5', 
                                limitH4 = 1000, limitM15 = 2000, limitM5 = 5000, limitM1 = 5000,
                                sweepThreshold = 0.5, eqhEqlThreshold = 0.1) {
        const params = new URLSearchParams({
            pair,
            timeframe_h4: timeframeH4,
            timeframe_m15: timeframeM15,
            timeframe_m5: timeframeM5,
            limit_h4: limitH4,
            limit_m15: limitM15,
            limit_m5: limitM5,
            limit_m1: limitM1,
            sweep_threshold: sweepThreshold,
            eqh_eql_threshold: eqhEqlThreshold
        }).toString();
        
        const response = await fetch(`${API_BASE_URL}/analysis/unified-smc?${params}`);
        if (!response.ok) {
            throw new Error(`Failed to fetch Unified SMC strategy: ${response.statusText}`);
        }
        return response.json();
    }
};
