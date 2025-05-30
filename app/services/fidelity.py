from typing import Dict, List, Optional
import aiohttp
from datetime import datetime
from app.core.config import settings
from app.models.portfolio import AssetType, Platform

class FidelityAPI:
    BASE_URL = "https://api.fidelity.com/api"  # Example URL, replace with actual Fidelity API endpoint
    
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None
        self.token_expires_at = None
    
    async def _get_access_token(self) -> str:
        """
        Get OAuth2 access token from Fidelity.
        Note: This is a placeholder implementation. Actual implementation will depend on Fidelity's OAuth flow.
        """
        if self.access_token and self.token_expires_at and self.token_expires_at > datetime.utcnow():
            return self.access_token
            
        async with aiohttp.ClientSession() as session:
            auth_url = f"{self.BASE_URL}/oauth/token"
            data = {
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret
            }
            
            async with session.post(auth_url, data=data) as response:
                if response.status != 200:
                    raise Exception("Failed to get access token from Fidelity")
                
                token_data = await response.json()
                self.access_token = token_data["access_token"]
                # Assuming token expires in 1 hour, adjust based on actual Fidelity API
                self.token_expires_at = datetime.utcnow() + datetime.timedelta(hours=1)
                return self.access_token
    
    async def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict:
        """Make authenticated request to Fidelity API"""
        access_token = await self._get_access_token()
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        async with aiohttp.ClientSession() as session:
            url = f"{self.BASE_URL}/{endpoint}"
            async with session.request(method, url, headers=headers, **kwargs) as response:
                if response.status not in (200, 201):
                    raise Exception(f"Fidelity API request failed: {await response.text()}")
                return await response.json()
    
    async def get_portfolio_positions(self) -> List[Dict]:
        """
        Fetch current portfolio positions from Fidelity.
        Returns list of positions with quantity and current value.
        """
        try:
            response = await self._make_request("GET", "positions")
            positions = []
            
            for position in response.get("positions", []):
                positions.append({
                    "asset_symbol": position["symbol"],
                    "asset_type": self._map_asset_type(position.get("securityType")),
                    "quantity": float(position["quantity"]),
                    "current_price": float(position["currentPrice"]),
                    "average_price": float(position.get("costBasis", 0) / float(position["quantity"]))
                    if float(position["quantity"]) > 0 else 0,
                    "platform": Platform.FIDELITY
                })
            
            return positions
        except Exception as e:
            raise Exception(f"Failed to fetch Fidelity positions: {str(e)}")
    
    async def get_transactions(self, start_date: Optional[datetime] = None) -> List[Dict]:
        """
        Fetch transaction history from Fidelity.
        Optionally filter by start date.
        """
        params = {}
        if start_date:
            params["startDate"] = start_date.strftime("%Y-%m-%d")
        
        try:
            response = await self._make_request("GET", "transactions", params=params)
            transactions = []
            
            for tx in response.get("transactions", []):
                transactions.append({
                    "transaction_type": tx["type"].lower(),  # buy/sell
                    "asset_symbol": tx["symbol"],
                    "quantity": float(tx["quantity"]),
                    "price": float(tx["price"]),
                    "timestamp": datetime.fromisoformat(tx["transactionDate"]),
                    "platform": Platform.FIDELITY
                })
            
            return transactions
        except Exception as e:
            raise Exception(f"Failed to fetch Fidelity transactions: {str(e)}")
    
    @staticmethod
    def _map_asset_type(fidelity_type: str) -> AssetType:
        """Map Fidelity asset types to our internal AssetType enum"""
        mapping = {
            "STOCK": AssetType.STOCK,
            "ETF": AssetType.ETF,
            "MUTUAL_FUND": AssetType.MUTUAL_FUND,
            "BOND": AssetType.BOND,
            "CASH": AssetType.CASH,
        }
        return mapping.get(fidelity_type.upper(), AssetType.STOCK)

async def create_fidelity_client() -> Optional[FidelityAPI]:
    """Create a Fidelity API client if credentials are configured"""
    if settings.FIDELITY_CLIENT_ID and settings.FIDELITY_CLIENT_SECRET:
        return FidelityAPI(
            client_id=settings.FIDELITY_CLIENT_ID,
            client_secret=settings.FIDELITY_CLIENT_SECRET
        )
    return None 