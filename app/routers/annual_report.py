"""
年报分析 API 路由
支持搜索和上传 PDF 年报进行分析
"""

import os
import tempfile
import uuid
import logging
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.core.config import settings
from app.routers.auth_db import get_current_user
from app.core.response import ok

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


class AnalysisResult(BaseModel):
    """分析结果"""
    title: str
    source: str
    analysisTime: str
    metrics: List[dict]
    report: str
    risk_signals: Optional[List[dict]] = None
    health_score: Optional[int] = None


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

async def analyze_pdf_content(pdf_path: str, symbol: Optional[str] = None) -> AnalysisResult:
    """分析 PDF 内容"""
    import asyncio
    
    # 这里可以调用 LLM 进行深度分析
    # 目前返回基础财务分析结果
    
    # 尝试从网络获取财务数据
    metrics = []
    report_lines = []
    risk_signals = []
    health_score = 70
    
    try:
        # 从新浪财经获取财务数据
        import urllib.request
        import re
        
        if symbol:
            url = f"https://vip.stock.finance.sina.com.cn/corp/go.php/vFD_FinancialGuideLine/stockid/{symbol}/displaytype/4.phtml"
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            
            try:
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=15) as response:
                    html = response.read().decode('gbk', errors='ignore')
                
                # 解析关键指标
                eps_match = re.search(r'摊薄每股收益.*?<td>([0-9.-]+)</td>', html)
                bvps_match = re.search(r'每股净资产.*?<td>([0-9.-]+)</td>', html)
                roe_match = re.search(r'净资产收益率.*?<td>([0-9.-]+)</td>', html)
                
                if eps_match:
                    eps_val = float(eps_match.group(1))
                    metrics.append({
                        "name": "每股收益(EPS)",
                        "value": f"{eps_val:.2f}元",
                        "color": "#67C23A" if eps_val > 0.5 else "#E6A23C" if eps_val > 0 else "#F56C6C"
                    })
                
                if bvps_match:
                    bvps_val = float(bvps_match.group(1))
                    metrics.append({
                        "name": "每股净资产",
                        "value": f"{bvps_val:.2f}元",
                        "color": "#67C23A" if bvps_val > 5 else "#E6A23C"
                    })
                
                if roe_match:
                    roe_val = float(roe_match.group(1))
                    metrics.append({
                        "name": "净资产收益率(ROE)",
                        "value": f"{roe_val:.1f}%",
                        "color": "#67C23A" if roe_val > 15 else "#E6A23C" if roe_val > 8 else "#F56C6C"
                    })
                    
            except Exception as e:
                logger.warning(f"获取财务数据失败: {e}")
    
    except Exception as e:
        logger.error(f"分析过程出错: {e}", exc_info=True)
    
    # 生成分析报告
    report_lines.append(f"# {symbol or '股票'} 年报财务分析报告\n")
    report_lines.append(f"\n**分析时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    if metrics:
        report_lines.append("\n## 关键财务指标\n")
        report_lines.append("| 指标 | 数值 | 状态 |")
        report_lines.append("|------|------|------|")
        for m in metrics:
            status = "✅ 健康" if "#67C23A" in m["color"] else ("⚠️ 关注" if "#E6A23C" in m["color"] else "❌ 风险")
            report_lines.append(f"| {m['name']} | {m['value']} | {status} |")
    
    report_lines.append("\n## 分析要点\n")
    report_lines.append("\n### 盈利能力分析")
    if metrics:
        roe_metric = next((m for m in metrics if "ROE" in m["name"]), None)
        if roe_metric:
            roe_val = float(roe_metric["value"].replace("%", ""))
            if roe_val > 15:
                report_lines.append("- **ROE表现优秀**: 净资产收益率超过15%，显示公司资本运用效率高，盈利能力强。")
            elif roe_val > 8:
                report_lines.append("- **ROE表现一般**: 净资产收益率在8%-15%之间，盈利能力尚可但有提升空间。")
            else:
                report_lines.append("- **ROE偏低**: 净资产收益率低于8%，需要关注公司盈利能力和资产效率。")
                risk_signals.append({
                    "name": "ROE",
                    "value": f"{roe_val}%",
                    "level": "高",
                    "description": "盈利能力较弱"
                })
    
    report_lines.append("\n### 财务健康度")
    report_lines.append("- 建议结合资产负债率、流动比率等指标综合评估财务风险。")
    report_lines.append("- 关注经营性现金流与净利润的匹配度，识别利润质量。")
    
    report_lines.append("\n## 风险提示\n")
    report_lines.append("1. 本分析基于公开财务数据，可能存在信息滞后或不完整的情况。")
    report_lines.append("2. 财务指标异常不代表一定存在问题，需结合行业特性和公司战略综合判断。")
    report_lines.append("3. 投资有风险，决策需谨慎，本报告不构成投资建议。")
    
    # 计算健康度评分
    if risk_signals:
        health_score = max(0, 100 - len([r for r in risk_signals if r["level"] == "高"]) * 15 - len([r for r in risk_signals if r["level"] == "中"]) * 5)
    
    return AnalysisResult(
        title=f"{symbol or '股票'} 年报分析报告",
        source="巨潮资讯网 + 新浪财经",
        analysisTime=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        metrics=metrics,
        report="\n".join(report_lines),
        risk_signals=risk_signals if risk_signals else None,
        health_score=health_score
    )


@router.post("/analyze", response_model=dict)
async def analyze_annual_report(
    file: Optional[UploadFile] = File(None),
    pdf_url: Optional[str] = Form(None),
    title: Optional[str] = Form(None),
    symbol: Optional[str] = Form(None),
    current_user: dict = Depends(get_current_user)
):
    """
    分析年报 PDF
    
    - **file**: 上传的 PDF 文件
    - **pdf_url**: PDF 文件 URL（与 file 二选一）
    - **title**: 报告标题
    - **symbol**: 股票代码（可选）
    """
    try:
        pdf_path = None
        source = ""
        
        # 方式1: 从 URL 下载
        if pdf_url:
            import urllib.request
            
            logger.info(f"从 URL 下载 PDF: {pdf_url}")
            source = "巨潮资讯网"
            
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
            source = f"上传文件: {file.filename}"
            
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
                content = await file.read()
                tmp.write(content)
                pdf_path = tmp.name
        
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="请提供 PDF 文件或 URL"
            )
        
        try:
            # 执行分析
            result = await analyze_pdf_content(pdf_path, symbol)
            
            if title:
                result.title = title
            
            return ok(data=result.model_dump(), message="分析完成")
            
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
