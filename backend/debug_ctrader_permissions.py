import os
import time
import logging
import threading
from twisted.internet import reactor, defer
from ctrader_open_api import Client, Protobuf, TcpProtocol, EndPoints
from ctrader_open_api.messages.OpenApiMessages_pb2 import (
    ProtoOAApplicationAuthReq,
    ProtoOAAccountAuthReq,
    ProtoOASymbolsListReq,
    ProtoOAGetTrendbarsReq
)

from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load credentials
load_dotenv()
CLIENT_ID = os.getenv("CTRADER_CLIENT_ID")
CLIENT_SECRET = os.getenv("CTRADER_CLIENT_SECRET")
ACCOUNT_ID = 2067137 # Testing on Live host
ACCESS_TOKEN = os.getenv("CTRADER_ACCESS_TOKEN")

# Constants
PROTO_OA_ERROR_RES = 2142
M5_PERIOD = 5

class CTraderDebug:
    def __init__(self):
        # Try LIVE host (in case accounts are on Live server)
        logger.info("Testing LIVE host...")
        self.client = Client(EndPoints.PROTOBUF_LIVE_HOST, EndPoints.PROTOBUF_PORT, TcpProtocol)
        self.connected = False
        self.authorized = False
        self.account_authorized = False
        
    def connect(self):
        self.client.setConnectedCallback(self._on_connected)
        self.client.setDisconnectedCallback(self._on_disconnected)
        self.client.setMessageReceivedCallback(self._on_message_received)
        self.client.startService()
        
        # Start reactor in thread
        if not reactor.running:
            threading.Thread(target=lambda: reactor.run(installSignalHandlers=False), daemon=True).start()
            
    def _on_connected(self, client):
        logger.info("Connected to cTrader API")
        self.connected = True
        self.authorize_app()
        
    def _on_disconnected(self, client, reason):
        logger.info(f"Disconnected: {reason}")
        self.connected = False
        
    def _on_message_received(self, client, message):
        # We handle specific responses in callbacks, but log errors here
        if message.payloadType == PROTO_OA_ERROR_RES:
            try:
                error = Protobuf.extract(message)
                logger.error(f"API ERROR: {error.errorCode} - {error.description}")
            except:
                logger.error("API ERROR (could not extract details)")

    def authorize_app(self):
        logger.info("Authorizing Application...")
        req = ProtoOAApplicationAuthReq()
        req.clientId = CLIENT_ID
        req.clientSecret = CLIENT_SECRET
        
        d = self.client.send(req)
        d.addCallback(self._on_app_auth_success)
        d.addErrback(self._on_error)
        
    def _on_app_auth_success(self, result):
        logger.info("✅ Application Authorized")
        self.authorized = True
        self.authorize_account()
        
    def _on_error(self, failure):
        logger.error(f"❌ Request Failed: {failure}")
        
    def authorize_account(self):
        logger.info(f"Authorizing Account {ACCOUNT_ID}...")
        req = ProtoOAAccountAuthReq()
        req.ctidTraderAccountId = ACCOUNT_ID
        req.accessToken = ACCESS_TOKEN
        
        d = self.client.send(req)
        d.addCallback(self._on_account_auth_success)
        d.addErrback(self._on_error)
        
    def _on_account_auth_success(self, result):
        logger.info("✅ Account Authorized")
        self.account_authorized = True
        self.request_symbols()
        
    def request_symbols(self):
        logger.info("Requesting Symbol List (Permission Check)...")
        req = ProtoOASymbolsListReq()
        req.ctidTraderAccountId = ACCOUNT_ID
        
        d = self.client.send(req)
        d.addCallback(self._on_symbols_success)
        d.addErrback(self._on_error)
        
    def _on_symbols_success(self, result):
        msg = Protobuf.extract(result)
        count = len(msg.symbol)
        logger.info(f"✅ Symbol List Received: {count} symbols found")
        
        # Find EURUSD ID
        eurusd_id = None
        for sym in msg.symbol:
            if sym.symbolName == "EURUSD":
                eurusd_id = sym.symbolId
                break
        
        if eurusd_id:
            logger.info(f"Found EURUSD ID: {eurusd_id}")
            self.request_trendbar(eurusd_id)
        else:
            logger.error("EURUSD not found in symbol list")
            
    def request_trendbar(self, symbol_id):
        logger.info("Requesting 1 Trendbar for EURUSD (Historical Data Check)...")
        req = ProtoOAGetTrendbarsReq()
        req.ctidTraderAccountId = ACCOUNT_ID
        req.period = M5_PERIOD
        req.symbolId = symbol_id
        req.count = 1
        # req.fromTimestamp = ... (optional, defaults to latest if count used)
        
        d = self.client.send(req)
        d.addCallback(self._on_trendbar_success)
        d.addErrback(self._on_error)
        
    def _on_trendbar_success(self, result):
        msg = Protobuf.extract(result)
        if hasattr(msg, 'trendbar') and len(msg.trendbar) > 0:
            logger.info(f"✅ Trendbar Received: {msg.trendbar[0]}")
            logger.info("🎉 SUCCESS: Account has historical data permissions!")
        else:
            logger.warning("⚠️ Trendbar response received but empty")
            
if __name__ == "__main__":
    debug = CTraderDebug()
    debug.connect()
    
    # Keep running for a bit
    time.sleep(10)
    print("Done")
