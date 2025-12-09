/**
 * Pair-specific price formatting utilities
 * Handles decimal precision for different trading pairs
 */

// Pair-specific decimal precision mapping
const PAIR_DECIMALS = {
  // Forex - Major pairs (5 decimals)
  'EURUSD': 5,
  'GBPUSD': 5,
  'USDCHF': 5,
  'AUDUSD': 5,
  'NZDUSD': 5,
  'USDCAD': 5,
  'EURGBP': 5,
  'EURJPY': 3,
  'EURCHF': 5,
  'AUDJPY': 3,
  'CADJPY': 3,
  'NZDJPY': 3,
  
  // Forex - JPY pairs (3 decimals)
  'USDJPY': 3,
  'GBPJPY': 3,
  
  // Metals (2-3 decimals)
  'XAUUSD': 2,  // Gold
  'XAGUSD': 3,  // Silver
  
  // Crypto (2 decimals for major, 4 for smaller)
  'BTCUSD': 2,
  'ETHUSD': 2,
  'ADAUSD': 4,
  'XRPUSD': 4,
  
  // Indices (2 decimals)
  'US30': 2,
  'US500': 2,
  'NAS100': 2,
  'USTEC': 2,
};

/**
 * Get decimal precision for a given pair
 * @param {string} pair - Trading pair symbol (e.g., 'EURUSD', 'XAUUSD')
 * @returns {number} Number of decimal places
 */
export function getPairDecimals(pair) {
  if (!pair) return 5; // Default fallback
  const upperPair = pair.toUpperCase();
  return PAIR_DECIMALS[upperPair] || 5; // Default to 5 decimals
}

/**
 * Format price with correct decimal precision for the pair
 * @param {number} price - Price value to format
 * @param {string} pair - Trading pair symbol
 * @returns {string} Formatted price string
 */
export function formatPrice(price, pair) {
  if (price === null || price === undefined || isNaN(price)) {
    return '—';
  }
  const decimals = getPairDecimals(pair);
  return Number(price).toFixed(decimals);
}

/**
 * Get price scale options for lightweight-charts
 * @param {string} pair - Trading pair symbol
 * @returns {object} Price scale configuration
 */
export function getPriceScaleOptions(pair) {
  const decimals = getPairDecimals(pair);
  return {
    minMove: Math.pow(10, -decimals),
    // Custom formatter for Y-axis labels
    priceFormatter: (price) => {
      if (price === null || price === undefined || isNaN(price)) {
        return '—';
      }
      return Number(price).toFixed(decimals);
    },
  };
}

/**
 * Format R:R ratio
 * @param {number} rr - Risk-reward ratio
 * @returns {string} Formatted R:R string
 */
export function formatRR(rr) {
  if (rr === null || rr === undefined || isNaN(rr)) {
    return '—';
  }
  return Number(rr).toFixed(2);
}

/**
 * Calculate pip value based on pair
 * @param {string} pair - Trading pair symbol
 * @returns {number} Pip value
 */
export function getPipValue(pair) {
  const decimals = getPairDecimals(pair);
  return Math.pow(10, -decimals);
}
