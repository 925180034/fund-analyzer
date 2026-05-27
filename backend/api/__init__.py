from fastapi import APIRouter
from backend.api.fund import router as fund_router
from backend.api.screen import router as screen_router
from backend.api.backtest import router as backtest_router
from backend.api.portfolio import router as portfolio_router
from backend.api.monitor import router as monitor_router
from backend.api.report import router as report_router

router = APIRouter(prefix="/api")
router.include_router(fund_router)
router.include_router(screen_router)
router.include_router(backtest_router)
router.include_router(portfolio_router)
router.include_router(monitor_router)
router.include_router(report_router)
