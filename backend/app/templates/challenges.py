"""Predefined challenge templates for prop firms"""

CHALLENGE_TEMPLATES = {
    "FTMO_10K": {
        "name": "FTMO $10,000",
        "type": "FTMO",
        "starting_balance": 10000.0,
        "profit_target": 1000.0,  # 10%
        "daily_loss_limit": 500.0,  # 5%
        "max_drawdown": 1000.0,  # 10%
        "risk_per_trade": 0.5,
        "max_positions": 2,
    },
    "FTMO_25K": {
        "name": "FTMO $25,000",
        "type": "FTMO",
        "starting_balance": 25000.0,
        "profit_target": 2500.0,
        "daily_loss_limit": 1250.0,
        "max_drawdown": 2500.0,
        "risk_per_trade": 0.5,
        "max_positions": 2,
    },
    "FTMO_50K": {
        "name": "FTMO $50,000",
        "type": "FTMO",
        "starting_balance": 50000.0,
        "profit_target": 5000.0,
        "daily_loss_limit": 2500.0,
        "max_drawdown": 5000.0,
        "risk_per_trade": 0.5,
        "max_positions": 2,
    },
    "FTMO_100K": {
        "name": "FTMO $100,000",
        "type": "FTMO",
        "starting_balance": 100000.0,
        "profit_target": 10000.0,
        "daily_loss_limit": 5000.0,
        "max_drawdown": 10000.0,
        "risk_per_trade": 0.5,
        "max_positions": 2,
    },
    "MFF_10K": {
        "name": "MyForexFunds $10,000",
        "type": "MFF",
        "starting_balance": 10000.0,
        "profit_target": 800.0,  # 8%
        "daily_loss_limit": 500.0,  # 5%
        "max_drawdown": 1000.0,  # 10%
        "risk_per_trade": 0.5,
        "max_positions": 2,
    },
    "MFF_25K": {
        "name": "MyForexFunds $25,000",
        "type": "MFF",
        "starting_balance": 25000.0,
        "profit_target": 2000.0,
        "daily_loss_limit": 1250.0,
        "max_drawdown": 2500.0,
        "risk_per_trade": 0.5,
        "max_positions": 2,
    },
    "FUNDED_TRADER_5K": {
        "name": "The Funded Trader $5,000",
        "type": "FundedTrader",
        "starting_balance": 5000.0,
        "profit_target": 500.0,  # 10%
        "daily_loss_limit": 250.0,  # 5%
        "max_drawdown": 500.0,  # 10%
        "risk_per_trade": 0.5,
        "max_positions": 2,
    },
    "FUNDED_TRADER_15K": {
        "name": "The Funded Trader $15,000",
        "type": "FundedTrader",
        "starting_balance": 15000.0,
        "profit_target": 1500.0,
        "daily_loss_limit": 750.0,
        "max_drawdown": 1500.0,
        "risk_per_trade": 0.5,
        "max_positions": 2,
    },
    "CUSTOM": {
        "name": "Custom Challenge",
        "type": "Custom",
        "starting_balance": 10000.0,
        "profit_target": 1000.0,
        "daily_loss_limit": 500.0,
        "max_drawdown": 1000.0,
        "risk_per_trade": 0.5,
        "max_positions": 2,
    },
}


def get_template(template_id: str):
    """Get challenge template by ID"""
    return CHALLENGE_TEMPLATES.get(template_id)


def list_templates():
    """List all available challenge templates"""
    return CHALLENGE_TEMPLATES
