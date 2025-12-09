"""
cTrader API Client for fetching historical and live market data

Uses ctrader-open-api library with WebSocket connection

Credentials from .env:
- CTRADER_CLIENT_ID
- CTRADER_CLIENT_SECRET  
- CTRADER_ACCOUNT_ID
- CTRADER_ACCESS_TOKEN

API Documentation: https://connect.spotware.com/docs/api
"""
from ctrader_open_api import Client, Protobuf, TcpProtocol, Auth
from ctrader_open_api.messages.OpenApiCommonMessages_pb2 import * # Keep this for other common messages
from ctrader_open_api.messages.OpenApiMessages_pb2 import (
    ProtoOAApplicationAuthReq,
    ProtoOAAccountAuthReq,
    ProtoOAGetTrendbarsReq,
    ProtoOASubscribeSpotsReq,
    ProtoOASpotEvent,
)
from ctrader_open_api.messages.OpenApiModelMessages_pb2 import (
    ProtoOATrendbarPeriod,
    ProtoOAPayloadType, # Corrected import location for ProtoOAPayloadType
)
import threading
import pytz
from twisted.internet import reactor, defer

import pandas as pd
from typing import Optional, Dict, List, Callable
from datetime import datetime, timedelta
import os
import time
from app.core.realtime_candle_builder import RealtimeCandleBuilder # Import the new builder

class CTraderClient:
    """
    Client for cTrader Open API
    
    Features:
    - Fetch historical OHLCV data
    - Support for multiple timeframes
    - Data normalization to standard format
    - Account information retrieval
    """
    
    # Demo environment
    HOST = "demo.ctraderapi.com"
    PORT = 5035
    
    # Timeframe mapping
    TIMEFRAME_MAP = {
        'M1': ProtoOATrendbarPeriod.M1,  # 1 minute
        '1M': ProtoOATrendbarPeriod.M1,  # Frontend format
        'M5': ProtoOATrendbarPeriod.M5,  # 5 minute
        '5M': ProtoOATrendbarPeriod.M5,  # Frontend format
        'M15': ProtoOATrendbarPeriod.M15,  # 15 minute
        '15M': ProtoOATrendbarPeriod.M15,  # Frontend format
        'M30': ProtoOATrendbarPeriod.M30,  # 30 minute
        '30M': ProtoOATrendbarPeriod.M30,  # Frontend format
        'H1': ProtoOATrendbarPeriod.H1,  # 1 hour
        '1H': ProtoOATrendbarPeriod.H1,  # Frontend format
        'H4': ProtoOATrendbarPeriod.H4,  # 4 hour
        '4H': ProtoOATrendbarPeriod.H4,  # Frontend format
        'D1': ProtoOATrendbarPeriod.D1,  # Daily
        'D': ProtoOATrendbarPeriod.D1,   # Frontend format
    }
    
    def __init__(self):
        """
        Initialize cTrader client with credentials from environment
        """
        self.client_id = os.getenv('CTRADER_CLIENT_ID')
        self.client_secret = os.getenv('CTRADER_CLIENT_SECRET')
        self.account_id = int(os.getenv('CTRADER_ACCOUNT_ID'))
        self.access_token = os.getenv('CTRADER_ACCESS_TOKEN')
        
        if not all([self.client_id, self.client_secret, self.account_id, self.access_token]):
            raise ValueError("Missing cTrader credentials in .env file")
        
        self.client = None
        self.connected = False
        self.authenticated = False
        self.accounts = []
        self._response_data = None
        self._response_received = False
        self._connection_deferred = defer.Deferred() # For tracking connection status
        self._auth_deferred = defer.Deferred() # For tracking authentication status
        self.live_data_streams: Dict[str, RealtimeCandleBuilder] = {} # Stores RealtimeCandleBuilder instances per symbol
        self._subscribed_symbols: Dict[str, int] = {} # Stores symbolId for subscribed symbols
    
    def connect(self) -> bool:
        """
        Connect to cTrader API
        
        Returns:
            True if connection successful
        """
        if self.connected:
            print("✅ Already connected to cTrader")
            return True
            
        try:
            self.client = Client(self.HOST, self.PORT, TcpProtocol)
            
            self.client.setConnectedCallback(self._on_connected)
            self.client.setDisconnectedCallback(self._on_disconnected)
            self.client.setMessageReceivedCallback(self._on_message_received)
            
            self.client.startService()
            
            if not reactor.running:
                threading.Thread(target=lambda: reactor.run(installSignalHandlers=False), daemon=True).start()
            
            # Wait for connection and authentication
            timeout = 10 # seconds
            start_time = time.time()
            
            while not self.authenticated and (time.time() - start_time) < timeout:
                time.sleep(0.1)
            
            if self.authenticated:
                print("✅ cTrader client connected and authenticated")
                return True
            else:
                print("❌ cTrader connection or authentication timed out")
                return False
            
        except Exception as e:
            print(f"❌ cTrader connection failed: {e}")
            return False

    def _on_connected(self, client):
        self.connected = True
        print("Connected to cTrader Open API")
        
        # Application authentication
        app_auth_req = ProtoOAApplicationAuthReq()
        app_auth_req.clientId = self.client_id
        app_auth_req.clientSecret = self.client_secret
        d = client.send(app_auth_req)
        d.addCallback(self._on_app_auth_response)
        d.addErrback(self._on_error)

    def _on_app_auth_response(self, response):
        if response.payloadType == ProtoOAPayloadType.PROTO_OA_APPLICATION_AUTH_RES:
            print("Application authenticated successfully")
            # Account authentication
            account_auth_req = ProtoOAAccountAuthReq()
            account_auth_req.ctidTraderAccountId = self.account_id
            account_auth_req.accessToken = self.access_token
            d = self.client.send(account_auth_req)
            d.addCallback(self._on_account_auth_response)
            d.addErrback(self._on_error)
        else:
            print(f"Application authentication failed: {response}")
            self.connected = False
            self.authenticated = False
            self._auth_deferred.err(Exception("Application authentication failed"))

    def _on_account_auth_response(self, response):
        if response.payloadType == ProtoOAPayloadType.PROTO_OA_ACCOUNT_AUTH_RES:
            print("Account authenticated successfully")
            self.authenticated = True
            self._auth_deferred.callback(True)
        else:
            print(f"Account authentication failed: {response}")
            self.authenticated = False
            self._auth_deferred.err(Exception("Account authentication failed"))

    def _on_disconnected(self, client, reason):
        print(f"Disconnected: {reason}")
        self.connected = False
        self.authenticated = False

    def _on_message_received(self, client, message):
        # Handle spot events for live data
        if message.payloadType == ProtoOAPayloadType.PROTO_OA_SPOT_EVENT:
            spot_event = Protobuf.extract(message)
            symbol_id = spot_event.symbolId
            
            # Find the symbol name from the symbol_id
            symbol_name = next((name for name, s_id in self._subscribed_symbols.items() if s_id == symbol_id), None)

            if symbol_name and symbol_name in self.live_data_streams:
                tick_time = datetime.fromtimestamp(spot_event.ctm / 1000, tz=pytz.utc)
                tick = {
                    'time': tick_time,
                    'bid': spot_event.bid / 100000, # Assuming 5 decimal places for forex
                    'ask': spot_event.ask / 100000
                }
                self.live_data_streams[symbol_name].add_tick(tick)
        # Generic message handler, specific responses are handled by callbacks
        pass

    def _on_error(self, failure):
        print(f"Error: {failure}")
    
    def disconnect(self):
        """Disconnect from cTrader API"""
        if self.client:
            self.client.disconnect()
            self.connected = False
    
    def test_connection(self) -> bool:
        """
        Test if the API connection works
        
        Returns:
            True if connection successful
        """
        if not self.connect(): # Ensure connected and authenticated
            return False

        print(f"✅ cTrader credentials loaded:")
        print(f"   Client ID: {self.client_id[:20]}...")
        print(f"   Account ID: {self.account_id}")
        print(f"   Access Token: {self.access_token[:20]}...")
        return True
    
    def get_accounts(self) -> List[Dict]:
        """
        Get list of trading accounts
        
        Note: For now, returns the configured account from .env
        Full implementation would query the API
        
        Returns:
            List of account dictionaries
        """
        return [{
            'accountId': self.account_id,
            'accountNumber': self.account_id,
            'live': False,
            'brokerName': 'blackbullmarkets',
            'depositCurrency': 'USD',
            'balance': 1000000,  # From your provided data
            'leverage': 100,
            'accountStatus': 'ACTIVE'
        }]
    
    def get_historical_data(
        self,
        symbol: str,
        timeframe: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        bars: int = 1000
    ) -> pd.DataFrame:
        """
        Fetch historical OHLCV data
        
        Args:
            symbol: Trading symbol (e.g., 'EURUSD')
            timeframe: Timeframe (M1, M5, M15, M30, H1, H4, D1)
            start_date: Start date (optional)
            end_date: End date (optional)
            bars: Number of bars to fetch (default: 1000)
            
        Returns:
            DataFrame with columns: time, open, high, low, close, volume
        """
        if not self.authenticated:
            print("❌ Not authenticated with cTrader, cannot fetch historical data.")
            return pd.DataFrame(columns=['time', 'open', 'high', 'low', 'close', 'volume'])
        
        print(f"Fetching historical data for {symbol} {timeframe}, {bars} bars...")
        
        self._response_data = None
        self._response_received = False

        def on_success(message):
            self._response_data = message
            self._response_received = True

        def on_error(failure):
            print(f"❌ Historical data request failed: {failure}")
            self._response_received = True

        # Request trendbars
        req = ProtoOAGetTrendbarsReq()
        req.ctidTraderAccountId = self.account_id
        req.symbolId = self._get_symbol_id(symbol)
        req.period = self.TIMEFRAME_MAP[timeframe]
        req.fromTimestamp = int(start_date.timestamp() * 1000) if start_date else int((datetime.utcnow() - timedelta(days=30)).timestamp() * 1000) # Default to last 30 days
        req.toTimestamp = int(end_date.timestamp() * 1000) if end_date else int(datetime.utcnow().timestamp() * 1000)
        req.count = bars # Request a specific number of bars

        d = self.client.send(req, responseTimeoutInSeconds=30)
        d.addCallback(on_success)
        d.addErrback(on_error)

        # Wait for response
        start_time = time.time()
        while not self._response_received and (time.time() - start_time) < 35: # 35 second timeout
            time.sleep(0.1)

        if not self._response_data:
            print(f"❌ No historical data received for {symbol} {timeframe}")
            return pd.DataFrame(columns=['time', 'open', 'high', 'low', 'close', 'volume'])

        # Process response
        trendbars = Protobuf.extract(self._response_data).trendbar
        data = []
        for bar in trendbars:
            data.append({
                'time': datetime.fromtimestamp(bar.utcTimestampInMinutes * 60, tz=pytz.utc),
                'open': (bar.low + bar.deltaOpen) / 100000,
                'high': (bar.low + bar.deltaHigh) / 100000,
                'low': bar.low / 100000,
                'close': (bar.low + bar.deltaClose) / 100000,
                'volume': getattr(bar, 'volume', 0)
            })
        
        df = pd.DataFrame(data)
        df.set_index('time', inplace=True)
        df.sort_index(inplace=True)
        return df
    
    def _get_symbol_id(self, symbol_name: str) -> int:
        """
        Helper to get symbol ID from name.
        In a full implementation, this would query the API for symbol list.
        For now, use a hardcoded map or the one from CTraderData.
        """
        # This should ideally come from a ProtoOASymbolsListReq response
        # For now, using the same mapping as in ctrader.py
        symbol_ids = {
            'EURUSD': 2596,
            'GBPUSD': 2,
            'USDJPY': 4,
            'AUDUSD': 5,
            'USDCAD': 8,
            'XAUUSD': 2469,
        }
        return symbol_ids.get(symbol_name, 0) # Return 0 or raise error if not found

    def subscribe_to_live_data(self, symbol: str, timeframes: List[str] = None):
        """
        Subscribes to live tick data for a given symbol and initializes a RealtimeCandleBuilder.
        """
        if not self.authenticated:
            print(f"❌ Not authenticated, cannot subscribe to live data for {symbol}.")
            return

        if symbol in self.live_data_streams:
            print(f"✅ Already subscribed to live data for {symbol}.")
            return

        symbol_id = self._get_symbol_id(symbol)
        if symbol_id == 0:
            print(f"❌ Unknown symbol: {symbol}. Cannot subscribe to live data.")
            return

        print(f"Subscribing to live data for {symbol} (ID: {symbol_id})...")
        req = ProtoOASubscribeSpotsReq()
        req.ctidTraderAccountId = self.account_id
        req.symbolId.append(symbol_id)
        
        d = self.client.send(req)
        d.addCallback(lambda _: print(f"✅ Subscribed to spots for {symbol}"))
        d.addErrback(self._on_error)

        self._subscribed_symbols[symbol] = symbol_id
        
        # Initialize RealtimeCandleBuilder for this symbol
        if timeframes is None:
            timeframes = ['M1', 'M5', 'M15', 'H1', 'H4'] # Default timeframes for live aggregation
        self.live_data_streams[symbol] = RealtimeCandleBuilder(timeframes=timeframes)
        print(f"Initialized RealtimeCandleBuilder for {symbol} with timeframes: {timeframes}")

    def get_live_candles(self, symbol: str, timeframe: str) -> Optional[Dict]:
        """
        Returns the currently forming candle for a given symbol and timeframe from the live stream.
        """
        if symbol not in self.live_data_streams:
            print(f"❌ Not subscribed to live data for {symbol}.")
            return None
        
        return self.live_data_streams[symbol].get_current_candle(timeframe)

    def get_symbols(self) -> List[str]:
        """
        Get list of available trading symbols
        
        Returns:
            List of symbol names
        """
        # Common forex pairs
        return [
            'EURUSD', 'GBPUSD', 'USDJPY', 'USDCAD',
            'AUDUSD', 'NZDUSD', 'EURJPY', 'GBPJPY',
            'XAUUSD', 'BTCUSD'
        ]


# Singleton instance
_ctrader_client: Optional[CTraderClient] = None

def get_ctrader_client() -> CTraderClient:
    """Get or create singleton cTrader client instance"""
    global _ctrader_client
    if _ctrader_client is None:
        _ctrader_client = CTraderClient()
    return _ctrader_client
