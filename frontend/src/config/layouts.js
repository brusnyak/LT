/**
 * Layout Presets Configuration
 * 
 * Defines all available layout presets with panel configurations and overlay settings
 */

export const LAYOUT_PRESETS = {
  range_4h: {
    id: 'range_4h',
    name: '4H Range',
    description: 'Optimized for 4H range trading strategy',
    panels: {
      chart_4h: { visible: true, order: 1 },
      chart_5m: { visible: true, order: 2 },
      signals: { visible: true, order: 3 },
      journal: { visible: true, order: 4 },
      account: { visible: true, order: 5 }
    },
    overlays: {
      ranges: true,
      positions: true,
      order_blocks: false,
      liquidity: false,
      structure: false,
      fvgs: false,
      sessions: false
    },
    strategy: 'range_4h'
  },

  mtf_30_1: {
    id: 'mtf_30_1',
    name: 'MTF 30/1',
    description: 'Multi-timeframe 30M/1M execution strategy',
    panels: {
      chart_4h: { visible: true, order: 1 },
      chart_30m: { visible: true, order: 2 },
      chart_1m: { visible: true, order: 3 },
      signals: { visible: true, order: 4 },
      journal: { visible: false, order: 5 },
      account: { visible: true, order: 6 }
    },
    overlays: {
      ranges: false,
      positions: true,
      order_blocks: true,
      liquidity: true,
      structure: true,
      fvgs: true,
      sessions: true
    },
    strategy: 'mtf_30_1'
  },

  multi_pair: {
    id: 'multi_pair',
    name: 'Multi-Pair',
    description: 'Monitor multiple currency pairs simultaneously',
    panels: {
      chart_4h: { visible: false, order: 1 },
      chart_5m: { visible: false, order: 2 },
      signals: { visible: true, order: 3 },
      journal: { visible: false, order: 4 },
      account: { visible: true, order: 5 }
    },
    overlays: {
      ranges: true,
      positions: true,
      order_blocks: false,
      liquidity: false,
      structure: false,
      fvgs: false,
      sessions: false
    },
    strategy: 'range_4h',
    multiPair: true,
    pairs: ['EURUSD', 'GBPUSD', 'USDCAD', 'GBPJPY']
  },

  minimal: {
    id: 'minimal',
    name: 'Minimal',
    description: 'Clean, distraction-free chart view',
    panels: {
      chart_4h: { visible: true, order: 1 },
      chart_5m: { visible: false, order: 2 },
      signals: { visible: false, order: 3 },
      journal: { visible: false, order: 4 },
      account: { visible: false, order: 5 }
    },
    overlays: {
      ranges: true,
      positions: true,
      order_blocks: false,
      liquidity: false,
      structure: false,
      fvgs: false,
      sessions: false
    },
    strategy: 'range_4h'
  }
};

export const DEFAULT_LAYOUT = 'range_4h';

/**
 * Overlay display configuration
 */
export const OVERLAY_CONFIG = {
  ranges: {
    name: 'Ranges',
    icon: '📊',
    color: '#3b82f6',
    description: '4H range boxes'
  },
  positions: {
    name: 'Positions',
    icon: '📍',
    color: '#10b981',
    description: 'Active trade positions'
  },
  order_blocks: {
    name: 'Order Blocks',
    icon: '🟦',
    color: '#8b5cf6',
    description: 'Institutional OB zones'
  },
  liquidity: {
    name: 'Liquidity',
    icon: '💧',
    color: '#06b6d4',
    description: 'Liquidity pools and sweeps'
  },
  structure: {
    name: 'Structure',
    icon: '⚡',
    color: '#f59e0b',
    description: 'BOS and ChoCH markers'
  },
  fvgs: {
    name: 'FVGs',
    icon: '🔷',
    color: '#ec4899',
    description: 'Fair Value Gaps'
  },
  sessions: {
    name: 'Sessions',
    icon: '🕐',
    color: '#6366f1',
    description: 'London/NY session boxes'
  }
};

/**
 * Panel display configuration
 */
export const PANEL_CONFIG = {
  chart_4h: {
    name: '4H Chart',
    icon: '📈',
    description: 'Higher timeframe analysis'
  },
  chart_5m: {
    name: '5M Chart',
    icon: '📊',
    description: 'Execution timeframe'
  },
  chart_30m: {
    name: '30M Chart',
    icon: '📊',
    description: 'Mid timeframe'
  },
  chart_1m: {
    name: '1M Chart',
    icon: '📉',
    description: 'Precision entries'
  },
  signals: {
    name: 'Signals',
    icon: '🎯',
    description: 'Trading signals panel'
  },
  journal: {
    name: 'Journal',
    icon: '📝',
    description: 'Trade journal and history'
  },
  account: {
    name: 'Account',
    icon: '💰',
    description: 'Account statistics'
  }
};

/**
 * Validate layout configuration
 */
export function validateLayout(layout) {
  if (!layout || typeof layout !== 'object') {
    return false;
  }
  
  // Check required fields
  if (!layout.id || !layout.name || !layout.panels || !layout.overlays) {
    return false;
  }
  
  return true;
}

/**
 * Get preset by ID
 */
export function getPreset(presetId) {
  return LAYOUT_PRESETS[presetId] || LAYOUT_PRESETS[DEFAULT_LAYOUT];
}

/**
 * Get all preset IDs
 */
export function getAllPresetIds() {
  return Object.keys(LAYOUT_PRESETS);
}
