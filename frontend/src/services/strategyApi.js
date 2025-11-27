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
    }
};
