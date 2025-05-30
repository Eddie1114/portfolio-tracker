from typing import Dict, List, Optional
from datetime import datetime, timedelta
import alpaca_trade_api as tradeapi
from app.core.config import settings

class AlpacaService:
    def __init__(self):
        self.api = tradeapi.REST(
            key_id=settings.ALPACA_API_KEY,
            secret_key=settings.ALPACA_SECRET_KEY,
            base_url='https://paper-api.alpaca.markets'  # Use paper trading URL for market data
        )
    
    async def get_stock_price(self, symbol: str) -> Dict:
        """Get current stock price and basic info"""
        try:
            # Get latest trade
            trade = self.api.get_latest_trade(symbol)
            # Get company info
            asset = self.api.get_asset(symbol)
            
            return {
                "symbol": symbol,
                "current_price": float(trade.price),
                "timestamp": trade.timestamp,
                "name": asset.name,
                "exchange": asset.exchange
            }
        except Exception as e:
            raise Exception(f"Failed to fetch stock price for {symbol}: {str(e)}")
    
    async def get_stock_bars(self, symbol: str, timeframe: str = '1D', limit: int = 30) -> List[Dict]:
        """Get historical price bars"""
        try:
            bars = self.api.get_bars(symbol, timeframe, limit=limit)
            return [
                {
                    "timestamp": bar.t,
                    "open": float(bar.o),
                    "high": float(bar.h),
                    "low": float(bar.l),
                    "close": float(bar.c),
                    "volume": int(bar.v)
                }
                for bar in bars
            ]
        except Exception as e:
            raise Exception(f"Failed to fetch price bars for {symbol}: {str(e)}")
    
    async def get_multiple_stocks(self, symbols: List[str]) -> List[Dict]:
        """Get current prices for multiple stocks"""
        try:
            trades = self.api.get_latest_trades(symbols)
            assets = {asset.symbol: asset for asset in self.api.list_assets()}
            
            results = []
            for symbol in symbols:
                if symbol in trades and symbol in assets:
                    results.append({
                        "symbol": symbol,
                        "current_price": float(trades[symbol].price),
                        "timestamp": trades[symbol].timestamp,
                        "name": assets[symbol].name,
                        "exchange": assets[symbol].exchange
                    })
            return results
        except Exception as e:
            raise Exception(f"Failed to fetch multiple stock prices: {str(e)}")

async def create_alpaca_service() -> Optional[AlpacaService]:
    """Create an Alpaca service instance"""
    try:
        return AlpacaService()
    except Exception as e:
        print(f"Failed to create Alpaca service: {str(e)}")
        return None 