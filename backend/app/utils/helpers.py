"""
Helper functions for various utilities
"""

def standardize_timeframe(timeframe: str) -> str:
    """
    Standardize timeframe format
    
    Args:
        timeframe (str): Timeframe string
        
    Returns:
        str: Standardized timeframe
    """
    # Convert to uppercase
    tf = timeframe.upper()
    
    # Handle common formats
    if tf in ['M1', '1M', '1MIN', '1MINUTE']:
        return 'M1'
    elif tf in ['M3', '3M', '3MIN', '3MINUTE']:
        return 'M3'
    elif tf in ['M5', '5M', '5MIN', '5MINUTE']:
        return 'M5'
    elif tf in ['M15', '15M', '15MIN', '15MINUTE']:
        return 'M15'
    elif tf in ['M30', '30M', '30MIN', '30MINUTE']:
        return 'M30'
    elif tf in ['H1', '1H', '1HOUR']:
        return 'H1'
    elif tf in ['H4', '4H', '4HOUR']:
        return 'H4'
    elif tf in ['D1', '1D', 'DAILY', 'DAY']:
        return 'D1'
    elif tf in ['W1', '1W', 'WEEKLY', 'WEEK']:
        return 'W1'
    
    # Return as is if no match
    return tf

def timeframe_to_minutes(timeframe: str) -> int:
    """
    Convert timeframe to minutes
    
    Args:
        timeframe (str): Timeframe string
        
    Returns:
        int: Minutes
    """
    tf = standardize_timeframe(timeframe)
    
    if tf == 'M1':
        return 1
    elif tf == 'M3':
        return 3
    elif tf == 'M5':
        return 5
    elif tf == 'M15':
        return 15
    elif tf == 'M30':
        return 30
    elif tf == 'H1':
        return 60
    elif tf == 'H4':
        return 240
    elif tf == 'D1':
        return 1440
    elif tf == 'W1':
        return 10080
    
    # Default to 0 if unknown
    return 0
