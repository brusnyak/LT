/**
 * Telegram Mini App Theme Handler
 * This script handles the Telegram theme colors and applies them to the UI
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize Telegram WebApp
    const tg = window.Telegram?.WebApp;
    
    if (!tg) {
        console.warn('Telegram WebApp is not available. Using default theme.');
        return;
    }
    
    // Extract theme colors from Telegram
    const themeParams = tg.themeParams || {
        bg_color: '#ffffff',
        text_color: '#222222',
        hint_color: '#999999',
        link_color: '#2481cc',
        button_color: '#2481cc',
        button_text_color: '#ffffff',
        secondary_bg_color: '#f5f5f5'
    };
    
    // Convert hex colors to RGB for use with opacity
    const rgbColors = {
        bg_color_rgb: hexToRgb(themeParams.bg_color),
        text_color_rgb: hexToRgb(themeParams.text_color),
        hint_color_rgb: hexToRgb(themeParams.hint_color),
        link_color_rgb: hexToRgb(themeParams.link_color),
        button_color_rgb: hexToRgb(themeParams.button_color)
    };
    
    // Apply theme colors to CSS variables
    document.documentElement.style.setProperty('--tg-theme-bg-color', themeParams.bg_color);
    document.documentElement.style.setProperty('--tg-theme-text-color', themeParams.text_color);
    document.documentElement.style.setProperty('--tg-theme-hint-color', themeParams.hint_color);
    document.documentElement.style.setProperty('--tg-theme-link-color', themeParams.link_color);
    document.documentElement.style.setProperty('--tg-theme-button-color', themeParams.button_color);
    document.documentElement.style.setProperty('--tg-theme-button-text-color', themeParams.button_text_color);
    document.documentElement.style.setProperty('--tg-theme-secondary-bg-color', themeParams.secondary_bg_color);
    
    // Apply RGB values for use with opacity
    document.documentElement.style.setProperty('--tg-theme-bg-color-rgb', rgbColors.bg_color_rgb);
    document.documentElement.style.setProperty('--tg-theme-text-color-rgb', rgbColors.text_color_rgb);
    document.documentElement.style.setProperty('--tg-theme-hint-color-rgb', rgbColors.hint_color_rgb);
    document.documentElement.style.setProperty('--tg-theme-link-color-rgb', rgbColors.link_color_rgb);
    document.documentElement.style.setProperty('--tg-theme-button-color-rgb', rgbColors.button_color_rgb);
    
    // Determine if the theme is dark or light
    const isDarkTheme = isColorDark(themeParams.bg_color);
    
    // Set positive/negative colors based on theme
    // For dark themes, use slightly brighter colors
    if (isDarkTheme) {
        document.documentElement.style.setProperty('--tg-positive-color', '#4CAF50');
        document.documentElement.style.setProperty('--tg-negative-color', '#F44336');
        document.body.classList.add('dark-theme');
        document.body.classList.remove('light-theme');
    } else {
        document.documentElement.style.setProperty('--tg-positive-color', '#4CAF50');
        document.documentElement.style.setProperty('--tg-negative-color', '#F44336');
        document.body.classList.add('light-theme');
        document.body.classList.remove('dark-theme');
    }
    
    // Expose theme functions globally
    window.themeUtils = {
        formatDirection,
        formatPnL,
        isColorDark,
        isDarkTheme
    };
});

/**
 * Convert hex color to RGB
 * @param {string} hex - Hex color code
 * @returns {string} RGB values as comma-separated string
 */
function hexToRgb(hex) {
    // Remove the # if present
    hex = hex.replace('#', '');
    
    // Handle shorthand hex
    if (hex.length === 3) {
        hex = hex[0] + hex[0] + hex[1] + hex[1] + hex[2] + hex[2];
    }
    
    // Convert to RGB
    const r = parseInt(hex.substr(0, 2), 16);
    const g = parseInt(hex.substr(2, 2), 16);
    const b = parseInt(hex.substr(4, 2), 16);
    
    return `${r}, ${g}, ${b}`;
}

/**
 * Determine if a color is dark
 * @param {string} hexColor - Hex color code
 * @returns {boolean} True if the color is dark
 */
function isColorDark(hexColor) {
    // Remove the # if present
    hexColor = hexColor.replace('#', '');
    
    // Handle shorthand hex
    if (hexColor.length === 3) {
        hexColor = hexColor[0] + hexColor[0] + hexColor[1] + hexColor[1] + hexColor[2] + hexColor[2];
    }
    
    // Convert to RGB
    const r = parseInt(hexColor.substr(0, 2), 16);
    const g = parseInt(hexColor.substr(2, 2), 16);
    const b = parseInt(hexColor.substr(4, 2), 16);
    
    // Calculate brightness (YIQ formula)
    const brightness = (r * 299 + g * 587 + b * 114) / 1000;
    
    // Return true if the color is dark
    return brightness < 128;
}

/**
 * Format direction with appropriate color
 * @param {string} direction - Trade direction (buy/sell/long/short)
 * @returns {string} HTML with appropriate color class
 */
function formatDirection(direction) {
    if (!direction) return '';
    
    const directionLower = direction.toLowerCase();
    const isBuy = directionLower.includes('buy') || directionLower.includes('long');
    const isSell = directionLower.includes('sell') || directionLower.includes('short');
    
    if (isBuy) {
        return `<span class="direction-buy">${direction}</span>`;
    } else if (isSell) {
        return `<span class="direction-sell">${direction}</span>`;
    } else {
        return direction;
    }
}

/**
 * Format P/L with appropriate color
 * @param {string|number} pnl - Profit/loss value
 * @param {boolean} includeSign - Whether to include + sign for positive values
 * @returns {string} HTML with appropriate color class
 */
function formatPnL(pnl, includeSign = true) {
    if (pnl === null || pnl === undefined) return '';
    
    // Convert to number if it's a string
    let pnlValue = typeof pnl === 'string' ? parseFloat(pnl.replace(/[^-0-9.]/g, '')) : pnl;
    
    // Format the value
    let formattedValue;
    if (typeof pnl === 'string' && (pnl.includes('$') || pnl.includes('%'))) {
        // Preserve the original format but add sign
        formattedValue = pnl;
        if (pnlValue > 0 && includeSign && !pnl.includes('+')) {
            formattedValue = '+' + formattedValue;
        }
    } else {
        // Format as number
        formattedValue = pnlValue.toFixed(2);
        if (pnlValue > 0 && includeSign) {
            formattedValue = '+' + formattedValue;
        }
    }
    
    // Apply appropriate class
    if (pnlValue > 0) {
        return `<span class="pnl-positive">${formattedValue}</span>`;
    } else if (pnlValue < 0) {
        return `<span class="pnl-negative">${formattedValue}</span>`;
    } else {
        return `<span class="pnl-neutral">${formattedValue}</span>`;
    }
}
