"""
Base Strategy Class

All trading strategies should inherit from BaseStrategy and implement
the required abstract methods.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
import pandas as pd
from app.models.strategy import Signal


class BaseStrategy(ABC):
    """
    Abstract base class for all trading strategies
    
    All strategies must implement:
    - analyze(): Main analysis method
    - get_config_schema(): Return configuration options
    
    Provides utility methods for:
    - Position sizing
    - Risk-reward calculation
    - Signal management
    """
    
    def __init__(self, name: str, description: str, version: str = "1.0"):
        """
        Initialize base strategy
        
        Args:
            name: Strategy name (e.g., "4H Range", "MTF 30/1")
            description: Brief description of strategy logic
            version: Strategy version number
        """
        self.name = name
        self.description = description
        self.version = version
        self.signals: List[Signal] = []
        self.config: Dict[str, Any] = {}
    
    @abstractmethod
    def analyze(self, df_multi_tf: Dict[str, pd.DataFrame], config: Optional[Dict] = None) -> Dict:
        """
        Main analysis method - must be implemented by subclasses
        
        Args:
            df_multi_tf: Dictionary of timeframe dataframes
                        e.g., {'4H': df_4h, '5M': df_5m}
            config: Optional configuration dictionary
            
        Returns:
            Dictionary containing:
                - 'signals': List of Signal objects
                - 'metadata': Additional strategy-specific data
                - 'visualizations': Data for chart overlays
        """
        pass
    
    @abstractmethod
    def get_config_schema(self) -> Dict:
        """
        Return configuration schema for this strategy
        
        Returns:
            Dictionary defining configurable parameters:
            {
                'parameter_name': {
                    'type': 'number|boolean|string|select',
                    'default': default_value,
                    'min': min_value,  # for numbers
                    'max': max_value,  # for numbers
                    'options': [],  # for select
                    'description': 'Human readable description'
                }
            }
        """
        pass
    
    def calculate_position_size(
        self, 
        balance: float, 
        risk_pct: float, 
        entry_price: float,
        sl_price: float,
        pip_value: float = 10.0  # $10 per pip for 1 lot
    ) -> float:
        """
        Calculate position size based on risk parameters
        
        Args:
            balance: Account balance
            risk_pct: Risk percentage (e.g., 0.005 for 0.5%)
            entry_price: Entry price
            sl_price: Stop loss price
            pip_value: Value of 1 pip in account currency per lot
            
        Returns:
            Position size in lots
        """
        risk_amount = balance * risk_pct
        sl_distance_pips = abs(entry_price - sl_price) * 10000  # Convert to pips
        
        if sl_distance_pips == 0:
            return 0.0
        
        position_size = risk_amount / (sl_distance_pips * pip_value)
        
        # Round to 2 decimal places (standard lot sizing)
        return round(position_size, 2)
    
    def calculate_rr(self, entry: float, sl: float, tp: float) -> float:
        """
        Calculate risk-reward ratio
        
        Args:
            entry: Entry price
            sl: Stop loss price
            tp: Take profit price
            
        Returns:
            RR ratio (e.g., 2.0 for 2R)
        """
        risk = abs(entry - sl)
        reward = abs(tp - entry)
        
        if risk == 0:
            return 0.0
        
        return round(reward / risk, 2)
    
    def validate_signal(self, signal: Signal) -> bool:
        """
        Validate signal parameters
        
        Args:
            signal: Signal object to validate
            
        Returns:
            True if signal is valid
        """
        # Entry must be between SL and TP
        if signal.type == "LONG":
            if not (signal.stop_loss < signal.entry_price < signal.take_profit):
                return False
        elif signal.type == "SHORT":
            if not (signal.take_profit < signal.entry_price < signal.stop_loss):
                return False
        
        # RR must be positive
        if signal.risk_reward <= 0:
            return False
        
        # Position size must be positive
        if signal.position_size <= 0:
            return False
        
        return True
    
    def filter_signals_by_rr(self, signals: List[Signal], min_rr: float = 1.5) -> List[Signal]:
        """
        Filter signals by minimum risk-reward ratio
        
        Args:
            signals: List of signals to filter
            min_rr: Minimum RR ratio
            
        Returns:
            Filtered list of signals
        """
        return [s for s in signals if s.risk_reward >= min_rr]
    
    def get_strategy_info(self) -> Dict:
        """
        Get strategy information
        
        Returns:
            Dictionary with strategy metadata
        """
        return {
            'name': self.name,
            'description': self.description,
            'version': self.version,
            'config_schema': self.get_config_schema(),
            'total_signals': len(self.signals)
        }
    
    def set_config(self, config: Dict):
        """
        Set strategy configuration
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
    
    def get_visualization_data(self, df_multi_tf: Dict[str, pd.DataFrame]) -> Dict:
        """
        Get data for chart visualizations (override in subclasses)
        
        Args:
            df_multi_tf: Dictionary of timeframe dataframes
            
        Returns:
            Dictionary with visualization data for overlays
        """
        return {
            'overlays': [],
            'markers': [],
            'lines': []
        }


class StrategyRegistry:
    """
    Registry for managing multiple strategies
    
    Allows dynamic loading and selection of strategies
    """
    
    def __init__(self):
        self.strategies: Dict[str, BaseStrategy] = {}
    
    def register(self, strategy_id: str, strategy: BaseStrategy):
        """
        Register a strategy
        
        Args:
            strategy_id: Unique identifier (e.g., 'range_4h')
            strategy: Strategy instance
        """
        self.strategies[strategy_id] = strategy
    
    def get(self, strategy_id: str) -> Optional[BaseStrategy]:
        """
        Get a strategy by ID
        
        Args:
            strategy_id: Strategy identifier
            
        Returns:
            Strategy instance or None
        """
        return self.strategies.get(strategy_id)
    
    def list_all(self) -> List[Dict]:
        """
        List all registered strategies
        
        Returns:
            List of strategy information dictionaries
        """
        return [
            {
                'id': sid,
                'name': strategy.name,
                'description': strategy.description,
                'version': strategy.version
            }
            for sid, strategy in self.strategies.items()
        ]


# Global strategy registry
registry = StrategyRegistry()
