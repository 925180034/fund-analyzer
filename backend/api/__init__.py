from fastapi import APIRouter
from backend.api.fund import router as fund_router
from backend.api.screen import router as screen_router
from backend.api.backtest import router as backtest_router

router = APIRouter(prefix="/api")
router.include_router(fund_router)
router.include_router(screen_router)
router.include_router(backtest_router)
