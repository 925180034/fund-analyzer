from fastapi import APIRouter
import logging

from backend.services.report_generator import generate_fund_report

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/report", tags=["基金报告"])


@router.get("/fund/{code}")
async def get_fund_report(code: str):
    """生成基金诊断报告"""
    report = await generate_fund_report(code)
    if "error" in report:
        return report
    return {"data": report}
