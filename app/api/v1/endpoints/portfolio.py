from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any
from app.core.database import get_db
from app.schemas.portfolio import (
    Portfolio, PortfolioCreate, PortfolioWithHoldings,
    Holding, HoldingCreate, PlatformCredential, PlatformCredentialCreate,
    PortfolioRead, SyncResponse
)
from app.models.portfolio import Portfolio as PortfolioModel, User
from app.models.portfolio import Holding as HoldingModel
from app.models.portfolio import PlatformCredential as PlatformCredentialModel
from app.core.security import decode_access_token, get_current_user
from fastapi.security import OAuth2PasswordBearer
from app.services.ai_insights import generate_portfolio_insights, analyze_transaction_history
from app.services.portfolio_sync import PortfolioSyncService

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user_id(token: str = Depends(oauth2_scheme)) -> int:
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload.get("sub")

@router.post("/", response_model=Portfolio)
async def create_portfolio(
    portfolio: PortfolioCreate,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    db_portfolio = PortfolioModel(
        **portfolio.dict(),
        user_id=current_user_id
    )
    db.add(db_portfolio)
    await db.commit()
    await db.refresh(db_portfolio)
    return db_portfolio

@router.get("/", response_model=List[PortfolioRead])
async def get_portfolios(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all portfolios for the current user"""
    result = await db.execute(
        Portfolio.__table__.select().where(Portfolio.user_id == current_user.id)
    )
    portfolios = result.scalars().all()
    return portfolios

@router.get("/{portfolio_id}", response_model=PortfolioWithHoldings)
async def read_portfolio(
    portfolio_id: int,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    result = await db.execute(
        PortfolioModel.select().where(
            PortfolioModel.id == portfolio_id,
            PortfolioModel.user_id == current_user_id
        )
    )
    portfolio = result.scalar_one_or_none()
    if portfolio is None:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return portfolio

@router.post("/{portfolio_id}/holdings", response_model=Holding)
async def create_holding(
    portfolio_id: int,
    holding: HoldingCreate,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    # Verify portfolio ownership
    result = await db.execute(
        PortfolioModel.select().where(
            PortfolioModel.id == portfolio_id,
            PortfolioModel.user_id == current_user_id
        )
    )
    portfolio = result.scalar_one_or_none()
    if portfolio is None:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    db_holding = HoldingModel(**holding.dict())
    db.add(db_holding)
    await db.commit()
    await db.refresh(db_holding)
    return db_holding

@router.get("/{portfolio_id}/insights", response_model=Dict[str, Any])
async def get_portfolio_insights(
    portfolio_id: int,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    # Verify portfolio ownership and get portfolio data
    result = await db.execute(
        PortfolioModel.select().where(
            PortfolioModel.id == portfolio_id,
            PortfolioModel.user_id == current_user_id
        )
    )
    portfolio = result.scalar_one_or_none()
    if portfolio is None:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    # Convert portfolio to dict for AI analysis
    portfolio_data = {
        "id": portfolio.id,
        "name": portfolio.name,
        "holdings": [
            {
                "asset_symbol": h.asset_symbol,
                "asset_type": h.asset_type.value,
                "quantity": h.quantity,
                "average_price": h.average_price,
                "platform": h.platform.value
            }
            for h in portfolio.holdings
        ]
    }
    
    insights = await generate_portfolio_insights(portfolio_data)
    return insights

@router.get("/{portfolio_id}/transaction-analysis", response_model=Dict[str, Any])
async def get_transaction_analysis(
    portfolio_id: int,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    # Verify portfolio ownership and get transactions
    result = await db.execute(
        PortfolioModel.select().where(
            PortfolioModel.id == portfolio_id,
            PortfolioModel.user_id == current_user_id
        )
    )
    portfolio = result.scalar_one_or_none()
    if portfolio is None:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    # Collect all transactions from all holdings
    transactions = []
    for holding in portfolio.holdings:
        for tx in holding.transactions:
            transactions.append({
                "asset_symbol": holding.asset_symbol,
                "transaction_type": tx.transaction_type,
                "quantity": tx.quantity,
                "price": tx.price,
                "timestamp": tx.timestamp,
                "platform": tx.platform.value
            })
    
    analysis = await analyze_transaction_history(transactions)
    return analysis

@router.post("/sync", response_model=SyncResponse)
async def sync_portfolios(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Sync portfolios from configured platforms.
    Credentials are fetched from Doppler environment variables.
    """
    sync_service = PortfolioSyncService(db)
    result = await sync_service.sync_user_portfolios(current_user.id)
    return result 