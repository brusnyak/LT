/**
 * Formatting utilities
 */

/**
 * Format price with appropriate decimal places
 */
export function formatPrice(price, pair = 'EURUSD') {
    // JPY pairs use 3 decimals, others use 5
    const decimals = pair.includes('JPY') ? 3 : 5;
    return price.toFixed(decimals);
}

/**
 * Format percentage
 */
export function formatPercent(value, decimals = 2) {
    return `${(value * 100).toFixed(decimals)}%`;
}

/**
 * Format date/time
 */
export function formatDateTime(date) {
    return new Date(date).toLocaleString('en-US', {
        year: 'numeric',
        month: 'short',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
    });
}

/**
 * Format date only
 */
export function formatDate(date) {
    return new Date(date).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: '2-digit',
    });
}
