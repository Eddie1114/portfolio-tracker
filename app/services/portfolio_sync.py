from typing import List, Dict, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.fidelity import create_fidelity_client
from app.services.gemini import create_gemini_client
from app.models.portfolio import (
    Portfolio, Holding, Transaction,
    Platform, PlatformCredential
)

class PortfolioSyncService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def sync_user_portfolios(self, user_id: int) -> Dict[str, List[str]]:
        """
        Synchronize all portfolios for a user from connected platforms.
        Returns a dictionary with success and error messages.
        """
        result = {
            "success": [],
            "errors": []
        }
        
        # Try to sync Gemini portfolio
        try:
            gemini_client = await create_gemini_client()
            if gemini_client:
                await self._sync_gemini(user_id)
                result["success"].append("Successfully synced Gemini portfolio")
            else:
                result["errors"].append("Gemini credentials not configured in Doppler")
        except Exception as e:
            result["errors"].append(f"Failed to sync Gemini portfolio: {str(e)}")
        
        return result
    
    async def _sync_gemini(self, user_id: int):
        """Sync Gemini portfolio data"""
        client = await create_gemini_client()
        if not client:
            raise Exception("Gemini client configuration not found")
        
        # Get or create Gemini portfolio
        result = await self.db.execute(
            Portfolio.select().where(
                Portfolio.user_id == user_id,
                Portfolio.name == "Gemini Portfolio"
            )
        )
        portfolio = result.scalar_one_or_none()
        
        if not portfolio:
            portfolio = Portfolio(
                user_id=user_id,
                name="Gemini Portfolio",
                description="Automatically synced Gemini portfolio"
            )
            self.db.add(portfolio)
            await self.db.commit()
            await self.db.refresh(portfolio)
        
        # Fetch current balances
        positions = await client.get_balances()
        
        # Update holdings
        for position in positions:
            result = await self.db.execute(
                Holding.select().where(
                    Holding.portfolio_id == portfolio.id,
                    Holding.asset_symbol == position["asset_symbol"]
                )
            )
            holding = result.scalar_one_or_none()
            
            if holding:
                # Update existing holding
                holding.quantity = position["quantity"]
                holding.average_price = position["average_price"]
                holding.last_updated = datetime.utcnow()
            else:
                # Create new holding
                holding = Holding(
                    portfolio_id=portfolio.id,
                    asset_symbol=position["asset_symbol"],
                    asset_type=position["asset_type"],
                    quantity=position["quantity"],
                    average_price=position["average_price"],
                    platform=Platform.GEMINI
                )
                self.db.add(holding)
        
        await self.db.commit() 