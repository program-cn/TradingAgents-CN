"""
市场概览 API 路由
提供财联社新闻、资金流排行等接口
"""

from fastapi import APIRouter, HTTPException, Query, Depends, status
from typing import Optional
from datetime import datetime
import logging

from app.routers.auth_db import get_current_user
from app.core.response import ok
from app.services.market_overview_service import get_market_overview_service

router = APIRouter(prefix="/api/market-overview", tags=["市场概览"])
logger = logging.getLogger("webapi")


@router.get("/news", response_model=dict)
async def get_news(
    limit: int = Query(30, description="返回数量限制", ge=1, le=100),
    hours_back: int = Query(24, description="回溯小时数", ge=1, le=168),
    current_user: dict = Depends(get_current_user)
):
    """
    获取财联社新闻
    
    Args:
        limit: 返回数量限制
        hours_back: 回溯小时数
        
    Returns:
        新闻列表
    """
    try:
        service = get_market_overview_service()
        news_list = await service.get_cla_news(limit=limit, hours_back=hours_back)
        
        return ok(data={
            "news": news_list,
            "total_count": len(news_list),
            "limit": limit,
            "hours_back": hours_back,
            "update_time": datetime.utcnow().isoformat()
        }, message=f"获取新闻成功，返回 {len(news_list)} 条")
        
    except Exception as e:
        logger.error(f"获取新闻失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取新闻失败: {str(e)}"
        )


@router.get("/fund-flow/industry", response_model=dict)
async def get_industry_fund_flow(
    top_n: int = Query(15, description="返回前N个", ge=1, le=50),
    flow_type: str = Query("inflow", description="流向类型: inflow(净流入) 或 outflow(净流出)"),
    current_user: dict = Depends(get_current_user)
):
    """
    获取行业资金流排行

    Args:
        top_n: 返回前N个
        flow_type: 流向类型 - inflow(净流入) 或 outflow(净流出)

    Returns:
        行业资金流列表
    """
    try:
        service = get_market_overview_service()
        flow_list = await service.get_industry_fund_flow(top_n=top_n, flow_type=flow_type)

        return ok(data={
            "industry_fund_flow": flow_list,
            "total_count": len(flow_list),
            "flow_type": flow_type,
            "update_time": datetime.utcnow().isoformat()
        }, message=f"获取行业资金流成功，返回 {len(flow_list)} 个行业")

    except Exception as e:
        logger.error(f"获取行业资金流失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取行业资金流失败: {str(e)}"
        )


@router.get("/fund-flow/concept", response_model=dict)
async def get_concept_fund_flow(
    top_n: int = Query(15, description="返回前N个", ge=1, le=50),
    flow_type: str = Query("inflow", description="流向类型: inflow(净流入) 或 outflow(净流出)"),
    current_user: dict = Depends(get_current_user)
):
    """
    获取概念板块资金流排行

    Args:
        top_n: 返回前N个
        flow_type: 流向类型 - inflow(净流入) 或 outflow(净流出)

    Returns:
        概念板块资金流列表
    """
    try:
        service = get_market_overview_service()
        flow_list = await service.get_concept_fund_flow(top_n=top_n, flow_type=flow_type)

        return ok(data={
            "concept_fund_flow": flow_list,
            "total_count": len(flow_list),
            "flow_type": flow_type,
            "update_time": datetime.utcnow().isoformat()
        }, message=f"获取概念板块资金流成功，返回 {len(flow_list)} 个概念")

    except Exception as e:
        logger.error(f"获取概念板块资金流失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取概念板块资金流失败: {str(e)}"
        )


@router.get("/overview", response_model=dict)
async def get_market_overview(
    flow_type: str = Query("inflow", description="流向类型: inflow(净流入) 或 outflow(净流出)"),
    current_user: dict = Depends(get_current_user)
):
    """
    获取市场概览（聚合数据）

    Args:
        flow_type: 流向类型 - inflow(净流入) 或 outflow(净流出)

    Returns:
        包含新闻和资金流的聚合数据
    """
    try:
        service = get_market_overview_service()
        overview = await service.get_market_overview(flow_type=flow_type)

        return ok(data=overview, message="获取市场概览成功")

    except Exception as e:
        logger.error(f"获取市场概览失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取市场概览失败: {str(e)}"
        )
