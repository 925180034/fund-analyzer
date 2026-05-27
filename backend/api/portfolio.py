from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload

from backend.database import get_db
from backend.models.portfolio import Portfolio, PortfolioHolding
from backend.services.portfolio_analyzer import analyze_portfolio

router = APIRouter(prefix="/portfolio", tags=["组合管理"])


# --------------- Pydantic schemas ---------------

class HoldingCreate(BaseModel):
    code: str
    weight: float


class PortfolioCreate(BaseModel):
    name: str
    description: Optional[str] = None
    holdings: List[HoldingCreate]


class HoldingOut(BaseModel):
    code: str
    weight: float

    class Config:
        from_attributes = True


class PortfolioOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    holdings: List[HoldingOut] = []

    class Config:
        from_attributes = True


# --------------- endpoints ---------------

@router.post("/create")
async def create_portfolio(
    body: PortfolioCreate,
    db: AsyncSession = Depends(get_db),
):
    """创建组合"""
    portfolio = Portfolio(name=body.name, description=body.description)
    db.add(portfolio)
    await db.flush()

    for h in body.holdings:
        holding = PortfolioHolding(
            portfolio_id=portfolio.id,
            fund_code=h.code,
            weight=h.weight,
        )
        db.add(holding)

    await db.commit()
    await db.refresh(portfolio)

    result = await db.execute(
        select(PortfolioHolding).where(PortfolioHolding.portfolio_id == portfolio.id)
    )
    holdings = result.scalars().all()

    return {
        "data": {
            "id": portfolio.id,
            "name": portfolio.name,
            "description": portfolio.description,
            "created_at": str(portfolio.created_at) if portfolio.created_at else None,
            "holdings": [{"code": h.fund_code, "weight": h.weight} for h in holdings],
        }
    }


@router.get("/list")
async def list_portfolios(db: AsyncSession = Depends(get_db)):
    """获取所有组合"""
    result = await db.execute(select(Portfolio).order_by(Portfolio.created_at.desc()))
    portfolios = result.scalars().all()

    data = []
    for p in portfolios:
        h_result = await db.execute(
            select(PortfolioHolding).where(PortfolioHolding.portfolio_id == p.id)
        )
        holdings = h_result.scalars().all()
        data.append({
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "created_at": str(p.created_at) if p.created_at else None,
            "holdings": [{"code": h.fund_code, "weight": h.weight} for h in holdings],
        })

    return {"data": data}


@router.get("/{portfolio_id}")
async def get_portfolio(portfolio_id: int, db: AsyncSession = Depends(get_db)):
    """获取单个组合"""
    result = await db.execute(select(Portfolio).where(Portfolio.id == portfolio_id))
    portfolio = result.scalar_one_or_none()
    if not portfolio:
        raise HTTPException(status_code=404, detail="组合不存在")

    h_result = await db.execute(
        select(PortfolioHolding).where(PortfolioHolding.portfolio_id == portfolio_id)
    )
    holdings = h_result.scalars().all()

    return {
        "data": {
            "id": portfolio.id,
            "name": portfolio.name,
            "description": portfolio.description,
            "created_at": str(portfolio.created_at) if portfolio.created_at else None,
            "holdings": [{"code": h.fund_code, "weight": h.weight} for h in holdings],
        }
    }


@router.delete("/{portfolio_id}")
async def delete_portfolio(portfolio_id: int, db: AsyncSession = Depends(get_db)):
    """删除组合"""
    result = await db.execute(select(Portfolio).where(Portfolio.id == portfolio_id))
    portfolio = result.scalar_one_or_none()
    if not portfolio:
        raise HTTPException(status_code=404, detail="组合不存在")

    # 先删持仓
    await db.execute(
        delete(PortfolioHolding).where(PortfolioHolding.portfolio_id == portfolio_id)
    )
    await db.delete(portfolio)
    await db.commit()

    return {"message": "删除成功"}


@router.get("/{portfolio_id}/analysis")
async def get_portfolio_analysis(portfolio_id: int, db: AsyncSession = Depends(get_db)):
    """组合分析"""
    result = await db.execute(select(Portfolio).where(Portfolio.id == portfolio_id))
    portfolio = result.scalar_one_or_none()
    if not portfolio:
        raise HTTPException(status_code=404, detail="组合不存在")

    h_result = await db.execute(
        select(PortfolioHolding).where(PortfolioHolding.portfolio_id == portfolio_id)
    )
    holdings = h_result.scalars().all()

    holdings_data = [(h.fund_code, h.weight) for h in holdings]
    analysis = await analyze_portfolio(db, holdings_data)
    return {"data": analysis}
