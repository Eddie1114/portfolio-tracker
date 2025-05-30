from typing import Dict, List, Optional
import numpy as np
from datetime import datetime, timedelta
from app.services.alpaca_service import create_alpaca_service
from app.services.ai_insights import generate_portfolio_insights
from app.models.portfolio import Portfolio, Holding

class PortfolioAnalytics:
    def __init__(self):
        self.alpaca_service = None
    
    async def initialize(self):
        """Initialize services"""
        self.alpaca_service = await create_alpaca_service()
        if not self.alpaca_service:
            raise Exception("Failed to initialize Alpaca service")
    
    async def calculate_portfolio_metrics(self, portfolio: Portfolio) -> Dict:
        """Calculate key portfolio metrics"""
        total_value = 0
        holdings_data = []
        
        # Get current prices and calculate metrics
        for holding in portfolio.holdings:
            try:
                stock_data = await self.alpaca_service.get_stock_price(holding.asset_symbol)
                current_price = stock_data['current_price']
                holding_value = current_price * holding.quantity
                gain_loss = (current_price - holding.average_price) * holding.quantity
                gain_loss_pct = ((current_price - holding.average_price) / holding.average_price) * 100
                
                holdings_data.append({
                    "symbol": holding.asset_symbol,
                    "quantity": holding.quantity,
                    "current_price": current_price,
                    "average_price": holding.average_price,
                    "current_value": holding_value,
                    "gain_loss": gain_loss,
                    "gain_loss_percentage": gain_loss_pct
                })
                
                total_value += holding_value
            except Exception as e:
                print(f"Error processing {holding.asset_symbol}: {str(e)}")
        
        # Calculate portfolio diversification
        diversification = self._calculate_diversification(holdings_data, total_value)
        
        # Calculate historical performance
        historical_performance = await self._calculate_historical_performance(portfolio.holdings)
        
        # Get AI insights
        portfolio_data = {
            "holdings": holdings_data,
            "total_value": total_value,
            "diversification": diversification
        }
        ai_insights = await generate_portfolio_insights(portfolio_data)
        
        return {
            "total_value": total_value,
            "holdings": holdings_data,
            "diversification": diversification,
            "historical_performance": historical_performance,
            "risk_metrics": await self._calculate_risk_metrics(portfolio.holdings),
            "ai_insights": ai_insights
        }
    
    def _calculate_diversification(self, holdings_data: List[Dict], total_value: float) -> Dict:
        """Calculate portfolio diversification metrics"""
        if not holdings_data or total_value == 0:
            return {"error": "No holdings data available"}
        
        # Calculate allocation percentages
        allocations = [
            {
                "symbol": holding["symbol"],
                "percentage": (holding["current_value"] / total_value) * 100
            }
            for holding in holdings_data
        ]
        
        # Calculate concentration metrics
        sorted_allocations = sorted(allocations, key=lambda x: x["percentage"], reverse=True)
        top_holdings = sorted_allocations[:3]
        
        return {
            "allocations": allocations,
            "top_holdings": top_holdings,
            "concentration_risk": len([a for a in allocations if a["percentage"] > 20]),
            "number_of_holdings": len(holdings_data)
        }
    
    async def _calculate_historical_performance(self, holdings: List[Holding]) -> Dict:
        """Calculate historical performance metrics"""
        try:
            # Get 1-year historical data for each holding
            performance_data = []
            for holding in holdings:
                bars = await self.alpaca_service.get_stock_bars(
                    holding.asset_symbol,
                    timeframe="1D",
                    limit=252  # Approximately 1 year of trading days
                )
                
                if bars:
                    returns = [
                        (bar["close"] - bar["open"]) / bar["open"] * 100
                        for bar in bars
                    ]
                    performance_data.append({
                        "symbol": holding.asset_symbol,
                        "avg_daily_return": np.mean(returns),
                        "volatility": np.std(returns),
                        "max_drawdown": min(returns)
                    })
            
            return {
                "holdings_performance": performance_data,
                "portfolio_volatility": np.std([p["avg_daily_return"] for p in performance_data])
            }
        except Exception as e:
            return {"error": f"Failed to calculate historical performance: {str(e)}"}
    
    async def _calculate_risk_metrics(self, holdings: List[Holding]) -> Dict:
        """Calculate portfolio risk metrics"""
        try:
            # Get S&P 500 (SPY) data for beta calculation
            spy_bars = await self.alpaca_service.get_stock_bars("SPY", timeframe="1D", limit=252)
            spy_returns = [
                (bar["close"] - bar["open"]) / bar["open"] * 100
                for bar in spy_bars
            ]
            
            portfolio_betas = []
            for holding in holdings:
                bars = await self.alpaca_service.get_stock_bars(
                    holding.asset_symbol,
                    timeframe="1D",
                    limit=252
                )
                
                if bars:
                    stock_returns = [
                        (bar["close"] - bar["open"]) / bar["open"] * 100
                        for bar in bars
                    ]
                    
                    # Calculate beta
                    covariance = np.cov(stock_returns, spy_returns)[0][1]
                    variance = np.var(spy_returns)
                    beta = covariance / variance
                    
                    portfolio_betas.append({
                        "symbol": holding.asset_symbol,
                        "beta": beta
                    })
            
            # Calculate portfolio beta (weighted average)
            portfolio_beta = np.mean([b["beta"] for b in portfolio_betas])
            
            return {
                "portfolio_beta": portfolio_beta,
                "individual_betas": portfolio_betas,
                "risk_level": "High" if portfolio_beta > 1.2 else "Medium" if portfolio_beta > 0.8 else "Low"
            }
        except Exception as e:
            return {"error": f"Failed to calculate risk metrics: {str(e)}"}

async def create_portfolio_analytics() -> Optional[PortfolioAnalytics]:
    """Create and initialize portfolio analytics service"""
    try:
        analytics = PortfolioAnalytics()
        await analytics.initialize()
        return analytics
    except Exception as e:
        print(f"Failed to create portfolio analytics service: {str(e)}")
        return None 