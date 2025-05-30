from fastapi import APIRouter
from app.api.v1.endpoints import portfolio, auth

api_router = APIRouter()

api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["auth"]
)

api_router.include_router(
    portfolio.router,
    prefix="/portfolios",
    tags=["portfolios"]
) 