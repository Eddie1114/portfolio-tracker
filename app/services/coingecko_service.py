from typing import Dict, List, Optional
import aiohttp
from datetime import datetime, timedelta

class CoinGeckoService:
    BASE_URL = "https://api.coingecko.com/api/v3"
    
    async def get_crypto_price(self, coin_id: str) -> Dict:
        """Get current crypto price and market data"""
        async with aiohttp.ClientSession() as session:
            try:
                # Get current price and market data
                url = f"{self.BASE_URL}/simple/price"
                params = {
                    "ids": coin_id,
                    "vs_currencies": "usd",
                    "include_market_cap": "true",
                    "include_24hr_vol": "true",
                    "include_24hr_change": "true",
                    "include_last_updated_at": "true"
                }
                
                async with session.get(url, params=params) as response:
                    if response.status != 200:
                        raise Exception(f"CoinGecko API error: {await response.text()}")
                    
                    data = await response.json()
                    if coin_id not in data:
                        raise Exception(f"Crypto {coin_id} not found")
                    
                    coin_data = data[coin_id]
                    return {
                        "id": coin_id,
                        "current_price": coin_data["usd"],
                        "market_cap": coin_data["usd_market_cap"],
                        "volume_24h": coin_data["usd_24h_vol"],
                        "price_change_24h": coin_data["usd_24h_change"],
                        "last_updated": datetime.fromtimestamp(coin_data["last_updated_at"])
                    }
            
            except Exception as e:
                raise Exception(f"Failed to fetch crypto price for {coin_id}: {str(e)}")
    
    async def get_crypto_history(self, coin_id: str, days: int = 30) -> List[Dict]:
        """Get historical price data"""
        async with aiohttp.ClientSession() as session:
            try:
                url = f"{self.BASE_URL}/coins/{coin_id}/market_chart"
                params = {
                    "vs_currency": "usd",
                    "days": str(days),
                    "interval": "daily"
                }
                
                async with session.get(url, params=params) as response:
                    if response.status != 200:
                        raise Exception(f"CoinGecko API error: {await response.text()}")
                    
                    data = await response.json()
                    prices = data["prices"]  # [[timestamp, price], ...]
                    
                    return [
                        {
                            "timestamp": datetime.fromtimestamp(price[0] / 1000),
                            "price": price[1]
                        }
                        for price in prices
                    ]
            
            except Exception as e:
                raise Exception(f"Failed to fetch price history for {coin_id}: {str(e)}")
    
    async def get_multiple_cryptos(self, coin_ids: List[str]) -> List[Dict]:
        """Get current prices for multiple cryptocurrencies"""
        async with aiohttp.ClientSession() as session:
            try:
                url = f"{self.BASE_URL}/simple/price"
                params = {
                    "ids": ",".join(coin_ids),
                    "vs_currencies": "usd",
                    "include_market_cap": "true",
                    "include_24hr_vol": "true",
                    "include_24hr_change": "true",
                    "include_last_updated_at": "true"
                }
                
                async with session.get(url, params=params) as response:
                    if response.status != 200:
                        raise Exception(f"CoinGecko API error: {await response.text()}")
                    
                    data = await response.json()
                    results = []
                    
                    for coin_id in coin_ids:
                        if coin_id in data:
                            coin_data = data[coin_id]
                            results.append({
                                "id": coin_id,
                                "current_price": coin_data["usd"],
                                "market_cap": coin_data["usd_market_cap"],
                                "volume_24h": coin_data["usd_24h_vol"],
                                "price_change_24h": coin_data["usd_24h_change"],
                                "last_updated": datetime.fromtimestamp(coin_data["last_updated_at"])
                            })
                    
                    return results
            
            except Exception as e:
                raise Exception(f"Failed to fetch multiple crypto prices: {str(e)}")

async def create_coingecko_service() -> Optional[CoinGeckoService]:
    """Create a CoinGecko service instance"""
    try:
        return CoinGeckoService()
    except Exception as e:
        print(f"Failed to create CoinGecko service: {str(e)}")
        return None 