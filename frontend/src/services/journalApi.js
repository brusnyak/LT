/**
 * Journal API Service
 */

const API_BASE_URL = 'http://localhost:9000/api';

export const journalApi = {
    /**
     * Fetch journal data (trades, account, stats)
     */
    async getJournal(pair) {
        const response = await fetch(`${API_BASE_URL}/analysis/journal?pair=${pair}`);
        if (!response.ok) {
            throw new Error(`Failed to fetch journal: ${response.statusText}`);
        }
        return response.json();
    }
};
