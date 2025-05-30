from typing import Dict, List, Optional
import aiohttp
import hmac
import hashlib
import json
import base64
import time
from datetime import datetime
from app.core.config import settings
from app.models.portfolio import AssetType, Platform

class GeminiAPI:
    BASE_URL = "https://api.gemini.com/v1"
    
    def __init__(self):
        if not settings.GEMINI_API_KEY or not settings.GEMINI_API_SECRET:
            raise ValueError("Gemini API credentials not found in environment variables")
        self.api_key = settings.GEMINI_API_KEY
        self.api_secret = settings.GEMINI_API_SECRET.encode()
    
    def _generate_signature(self, payload: Dict) -> tuple[str, str, str]:
        """Generate required headers for Gemini API authentication"""
        t = datetime.now()
        payload_nonce = str(int(time.time() * 1000))
        payload.update({"request": "/v1/balances", "nonce": payload_nonce})
        
        encoded_payload = base64.b64encode(json.dumps(payload).encode())
        signature = hmac.new(self.api_secret, encoded_payload, hashlib.sha384).hexdigest()
        
        return encoded_payload.decode(), signature, payload_nonce
    
    async def _make_request(self, endpoint: str, method: str = "GET", payload: Dict = None) -> Dict:
        """Make authenticated request to Gemini API"""
        if payload is None:
            payload = {}
        
        encoded_payload, signature, nonce = self._generate_signature(payload)
        
        headers = {
            "Content-Type": "text/plain",
            "Content-Length": "0",
            "X-GEMINI-APIKEY": self.api_key,
            "X-GEMINI-PAYLOAD": encoded_payload,
            "X-GEMINI-SIGNATURE": signature,
            "Cache-Control": "no-cache"
        }
        
        async with aiohttp.ClientSession() as session:
            url = f"{self.BASE_URL}/{endpoint}"
            async with session.request(method, url, headers=headers) as response:
                if response.status not in (200, 201):
                    raise Exception(f"Gemini API request failed: {await response.text()}")
                return await response.json()
    
    async def get_balances(self) -> List[Dict]:
        """
        Fetch current cryptocurrency balances from Gemini.
        Returns list of positions with quantity and current value.
        """
        try:
            balances = await self._make_request("balances")
            positions = []
            
            # Get current prices for all assets with balance > 0
            for balance in balances:
                if float(balance["amount"]) > 0:
                    # Get current price
                    ticker = await self._make_request(f"pubticker/{balance['currency']}usd")
                    
                    positions.append({
                        "asset_symbol": balance["currency"],
                        "asset_type": AssetType.CRYPTO,
                        "quantity": float(balance["amount"]),
                        "current_price": float(ticker["last"]),
                        "average_price": float(balance.get("avg_price", 0)),
                        "platform": Platform.GEMINI
                    })
            
            return positions
        except Exception as e:
            raise Exception(f"Failed to fetch Gemini balances: {str(e)}")
    
    async def get_trades(self, symbol: Optional[str] = None) -> List[Dict]:
        """
        Fetch trading history from Gemini.
        Optionally filter by symbol.
        """
        try:
            payload = {}
            if symbol:
                payload["symbol"] = f"{symbol}USD"
            
            trades = await self._make_request("mytrades", payload=payload)
            transactions = []
            
            for trade in trades:
                transactions.append({
                    "transaction_type": "buy" if float(trade["amount"]) > 0 else "sell",
                    "asset_symbol": trade["symbol"][:3],  # Remove USD suffix
                    "quantity": abs(float(trade["amount"])),
                    "price": float(trade["price"]),
                    "timestamp": datetime.fromtimestamp(float(trade["timestamp"])),
                    "platform": Platform.GEMINI
                })
            
            return transactions
        except Exception as e:
            raise Exception(f"Failed to fetch Gemini trades: {str(e)}")

async def create_gemini_client() -> Optional[GeminiAPI]:
    """Create a Gemini API client using credentials from Doppler"""
    try:
        return GeminiAPI()
    except ValueError as e:
        print(f"Failed to create Gemini client: {str(e)}")
        return None 