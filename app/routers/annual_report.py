"""
年报分析 API 路由
支持搜索和上传 PDF 年报进行分析
参考 OpenClaw annual-report-analyzer skill 实现
"""

import os
import tempfile
import logging
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, status
from pydantic import BaseModel

from app.core.config import settings
from app.routers.auth_db import get_current_user
from app.core.response import ok
from app.services.annual_report_service import analyze_stock, AnalysisResult

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/annual-report", tags=["年报分析"])


# ==================== 数据模型 ====================

class ReportInfo(BaseModel):
    """报告信息"""
    title: str
    report_type: str
    year: int
    announce_date: str
    pdf_url: str
    source: str = ""


class SearchResponse(BaseModel):
    """搜索响应"""
    reports: List[ReportInfo]
    total: int


class AnalysisResponse(BaseModel):
    """分析响应"""
    symbol: str
    name: str
    periods: List[str]
    metrics: dict
    risk_signals: List[dict]
    health_score: int
    report: str
    source: str
    analysis_time: str


# ==================== 年报搜索 ====================

REPORT_TYPES = {
    'annual': {'name': '年度报告', 'keywords': ['年度报告']},
    'semi': {'name': '半年度报告', 'keywords': ['半年度报告']},
    'q1': {'name': '第一季度报告', 'keywords': ['第一季度报告', '一季报']},
    'q3': {'name': '第三季度报告', 'keywords': ['第三季度报告', '三季度报告']},
}


async def search_reports_from_cninfo(symbol: str, report_type: str, year: Optional[str] = None) -> List[ReportInfo]:
    """从巨潮资讯搜索年报"""
    import urllib.request
    import urllib.parse
    import json
    import re
    
    reports = []
    
    try:
        # 1. 获取股票信息
        stock_name = symbol
        
        search_url = "https://www.cninfo.com.cn/new/information/top/search/query"
        data = urllib.parse.urlencode({
            "keyWord": symbol,
            "maxSecNum": 5,
            "maxListNum": 0
        }).encode()
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Content-Type": "application/x-www-form-urlencoded",
            "X-Requested-With": "XMLHttpRequest"
        }
        
        try:
            req = urllib.request.Request(search_url, data=data, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as resp:
                result = json.loads(resp.read().decode('utf-8'))
                stocks = result.get('keyBoardList') or []
                if stocks:
                    stock_name = stocks[0].get('zwjc') or stocks[0].get('shortName') or symbol
        except Exception:
            pass
        
        # 2. 全文搜索年报
        type_info = REPORT_TYPES.get(report_type, REPORT_TYPES['annual'])
        type_name = type_info['name']
        
        if year:
            searchkey = f"{stock_name} {year}年{type_name}"
        else:
            searchkey = f"{stock_name} {type_name}"
        
        url = (
            f"https://www.cninfo.com.cn/new/fulltextSearch/full"
            f"?searchkey={urllib.parse.quote(searchkey)}"
            f"&sdate=&edate=&isfulltext=false&sortName=time&sortType=desc&pageNum=1"
        )
        
        req = urllib.request.Request(url, headers={
            **headers,
            "Referer": "https://www.cninfo.com.cn/new/fulltextSearch",
        })
        
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read().decode('utf-8'))
        
        raw = result.get('announcements') or []
        flat = []
        for item in raw:
            if isinstance(item, list):
                flat.extend(item)
            elif isinstance(item, dict):
                flat.append(item)
        
        for item in flat:
            title = item.get('announcementTitle', '')
            
            # 过滤标题
            if not any(kw in title for kw in type_info['keywords']):
                continue
            if any(ex in title for ex in ['摘要', '英文版', '修订', '更正']):
                continue
            
            # 提取年份
            year_match = re.search(r'20\d{2}', title)
            report_year = int(year_match.group()) if year_match else 0
            if year and report_year != int(year):
                continue
            
            # 构建 PDF URL
            adjunct_url = item.get('adjunctUrl', '')
            if adjunct_url:
                pdf_url = f"http://static.cninfo.com.cn/{adjunct_url}"
            else:
                continue
            
            # 公告日期
            raw_time = item.get('announcementTime', 0)
            if raw_time:
                ts = raw_time / 1000 if raw_time > 1000000000000 else raw_time
                announce_date = datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
            else:
                announce_date = ''
            
            reports.append(ReportInfo(
                title=title,
                report_type=report_type,
                year=report_year,
                announce_date=announce_date,
                pdf_url=pdf_url,
                source="巨潮资讯网"
            ))
        
        # 按年份和日期排序
        reports.sort(key=lambda x: (x.year, x.announce_date), reverse=True)
        
    except Exception as e:
        logger.error(f"搜索年报失败: {e}", exc_info=True)
    
    return reports


@router.get("/search", response_model=dict)
async def search_annual_reports(
    symbol: str = Query(..., description="股票代码"),
    type: str = Query("annual", description="报告类型: annual/semi/q1/q3"),
    year: Optional[str] = Query(None, description="年份"),
    current_user: dict = Depends(get_current_user)
):
    """
    搜索上市公司年报
    
    - **symbol**: 6位股票代码
    - **type**: annual(年报)/semi(半年报)/q1(一季报)/q3(三季报)
    - **year**: 可选，指定年份
    """
    try:
        reports = await search_reports_from_cninfo(symbol, type, year)
        
        return ok(data={
            "symbol": symbol,
            "reports": [r.model_dump() for r in reports],
            "total": len(reports)
        }, message=f"找到 {len(reports)} 份报告")
        
    except Exception as e:
        logger.error(f"搜索年报失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"搜索失败: {str(e)}"
        )


# ==================== 年报分析 ====================

@router.post("/analyze", response_model=dict)
async def analyze_annual_report(
    file: Optional[UploadFile] = File(None),
    pdf_url: Optional[str] = Form(None),
    title: Optional[str] = Form(None),
    symbol: Optional[str] = Form(None),
    periods: int = Form(4, description="报告期数量"),
    current_user: dict = Depends(get_current_user)
):
    """
    分析年报
    
    支持两种方式：
    1. 上传 PDF 文件
    2. 提供 PDF URL（从巨潮资讯搜索结果获取）
    
    分析内容包括：
    - 五维度财务指标分析（每股、盈利、偿债、运营、成长）
    - 现金流质量分析（净现比）
    - 财务造假信号识别
    - 风险预警报告
    
    - **file**: 上传的 PDF 文件
    - **pdf_url**: PDF 文件 URL（与 file 二选一）
    - **title**: 报告标题
    - **symbol**: 股票代码（推荐提供）
    - **periods**: 报告期数量（默认4）
    """
    try:
        pdf_path = None
        
        # 方式1: 从 URL 下载
        if pdf_url:
            import urllib.request
            
            logger.info(f"从 URL 下载 PDF: {pdf_url}")
            
            # 下载到临时文件
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
                req = urllib.request.Request(pdf_url, headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                })
                with urllib.request.urlopen(req, timeout=60) as resp:
                    tmp.write(resp.read())
                pdf_path = tmp.name
        
        # 方式2: 使用上传的文件
        elif file:
            logger.info(f"使用上传的文件: {file.filename}")
            
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
                content = await file.read()
                tmp.write(content)
                pdf_path = tmp.name
        
        # 方式3: 仅使用股票代码（无需PDF）
        elif symbol:
            logger.info(f"仅使用股票代码分析: {symbol}")
        
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="请提供股票代码、PDF 文件或 URL"
            )
        
        try:
            # 执行分析
            result = await analyze_stock(
                symbol=symbol or "",
                pdf_path=pdf_path,
                periods=periods
            )
            
            # 转换为字典返回
            return ok(data={
                "symbol": result.symbol,
                "name": result.name,
                "periods": result.periods,
                "metrics": result.metrics,
                "risk_signals": result.risk_signals,
                "health_score": result.health_score,
                "report": result.report,
                "source": result.source,
                "analysis_time": result.analysis_time
            }, message="分析完成")
            
        finally:
            # 清理临时文件
            if pdf_path and os.path.exists(pdf_path):
                os.unlink(pdf_path)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"分析年报失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"分析失败: {str(e)}"
        )


@router.get("/analyze/{symbol}", response_model=dict)
async def analyze_by_symbol(
    symbol: str,
    periods: int = Query(4, description="报告期数量"),
    current_user: dict = Depends(get_current_user)
):
    """
    通过股票代码快速分析
    
    直接使用股票代码进行财务分析，无需上传PDF
    
    - **symbol**: 6位股票代码
    - **periods**: 报告期数量（默认4）
    """
    try:
        result = await analyze_stock(
            symbol=symbol,
            pdf_path=None,
            periods=periods
        )
        
        return ok(data={
            "symbol": result.symbol,
            "name": result.name,
            "periods": result.periods,
            "metrics": result.metrics,
            "risk_signals": result.risk_signals,
            "health_score": result.health_score,
            "report": result.report,
            "source": result.source,
            "analysis_time": result.analysis_time
        }, message="分析完成")
        
    except Exception as e:
        logger.error(f"分析年报失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"分析失败: {str(e)}"
        )
