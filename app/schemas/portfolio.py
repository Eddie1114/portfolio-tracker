from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict
from datetime import datetime
from enum import Enum
from app.models.portfolio import AssetType, Platform

class Platform(str, Enum):
    GEMINI = "gemini"
    FIDELITY = "fidelity"

class AssetType(str, Enum):
    CRYPTO = "crypto"
    STOCK = "stock"
    ETF = "etf"
    MUTUAL_FUND = "mutual_fund"

class UserBase(BaseModel):
    email: EmailStr
    full_name: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class PortfolioBase(BaseModel):
    name: str
    description: Optional[str] = None

class PortfolioCreate(PortfolioBase):
    pass

class Portfolio(PortfolioBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class HoldingBase(BaseModel):
    asset_symbol: str
    asset_type: AssetType
    quantity: float
    average_price: float
    platform: Platform

class HoldingCreate(HoldingBase):
    portfolio_id: int

class Holding(HoldingBase):
    id: int
    portfolio_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class PortfolioRead(Portfolio):
    holdings: List[Holding] = []

class SyncResponse(BaseModel):
    success: List[str]
    errors: List[str]

class TransactionBase(BaseModel):
    transaction_type: str
    quantity: float
    price: float
    platform: Platform

class TransactionCreate(TransactionBase):
    holding_id: int

class Transaction(TransactionBase):
    id: int
    timestamp: datetime

    class Config:
        from_attributes = True

class PlatformCredentialBase(BaseModel):
    platform: Platform
    api_key: str
    api_secret: str

class PlatformCredentialCreate(PlatformCredentialBase):
    pass

class PlatformCredential(PlatformCredentialBase):
    id: int
    user_id: int
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    expires_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class PortfolioWithHoldings(Portfolio):
    holdings: List[Holding]

class HoldingWithTransactions(Holding):
    transactions: List[Transaction]

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None 