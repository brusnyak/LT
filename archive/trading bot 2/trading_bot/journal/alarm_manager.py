"""
Alarm Manager for price alerts
"""

import logging
import sqlite3
import time
from datetime import datetime
from typing import List, Dict, Optional, Tuple, Union
import pandas as pd
import os
from trading_bot.data.data_processor import DataProcessor

logger = logging.getLogger(__name__)

class AlarmManager:
    """
    Manages price alarms for trading pairs
    """
