"""
市场概览服务
提供财联社新闻、资金流排行等功能
"""

import asyncio
import hashlib
import logging
import os
import json
import re
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger("webapi")

# HTML 标签清理正则表达式
HTML_TAG_PATTERN = re.compile(r'<[^>]+>')


def clean_html_tags(text: str) -> str:
    """移除 HTML 标签，保留纯文本"""
    if not text:
        return ""
    return HTML_TAG_PATTERN.sub('', text)

# 东方财富 API 配置
EASTMONEY_API_BASE = "https://push2.eastmoney.com/api/qt/clist/get"
EASTMONEY_API_COMMON_PARAMS = {
    "pz": "50",  # 返回50条
    "pn": "1",
    "np": "0",
    "ut": "b2884a393a59ad64002292a3e90d46a5",
    "fltt": "2",
    "invt": "2",
    "fields": "f12,f14,f2,f3,f62,f66,f69,f72,f75,f78,f81,f84,f87,f204,f205"
}
# 行业资金流 fs 参数
EASTMONEY_INDUSTRY_FS = "m:90+t:2"
# 概念板块资金流 fs 参数
EASTMONEY_CONCEPT_FS = "m:90+t:3"


@dataclass
class NewsItem:
    """新闻条目"""
    title: str
    content: str
    datetime: str
    source: str = "财联社"
    hash: Optional[str] = None


@dataclass
class FundFlowItem:
    """资金流条目"""
    name: str
    inflow: float  # 流入资金（亿元）
    outflow: float  # 流出资金（亿元）
    net_inflow: float  # 净流入（亿元）
    rank: int = 0


class MarketOverviewService:
    """市场概览服务"""

    def __init__(self, cache_dir: str = "data/market_overview"):
        self.cache_dir = cache_dir
        self._cache: Dict[str, Any] = {}
        self._cache_time: Dict[str, datetime] = {}
        self._cache_ttl = 300  # 缓存 5 分钟

        # 确保缓存目录存在
        os.makedirs(cache_dir, exist_ok=True)

    def _is_cache_valid(self, key: str) -> bool:
        """检查缓存是否有效"""
        if key not in self._cache or key not in self._cache_time:
            return False
        return (datetime.utcnow() - self._cache_time[key]).total_seconds() < self._cache_ttl

    async def get_cla_news(self, limit: int = 50, hours_back: int = 24) -> List[Dict[str, Any]]:
        """
        获取财联社新闻
        
        Args:
            limit: 返回数量限制
            hours_back: 回溯小时数
            
        Returns:
            新闻列表
        """
        cache_key = f"cla_news_{limit}_{hours_back}"
        
        # 检查缓存
        if self._is_cache_valid(cache_key):
            return self._cache[cache_key]

        try:
            # 在线程池中执行同步的 AKShare 调用
            news_list = await asyncio.to_thread(self._fetch_cla_news_sync, limit, hours_back)
            
            # 更新缓存
            self._cache[cache_key] = news_list
            self._cache_time[cache_key] = datetime.utcnow()
            
            return news_list
            
        except Exception as e:
            logger.error(f"获取财联社新闻失败: {e}", exc_info=True)
            return []

    def _fetch_cla_news_sync(self, limit: int, hours_back: int) -> List[Dict[str, Any]]:
        """同步获取财联社新闻"""
        try:
            import akshare as ak
            
            # 获取财联社新闻
            df = ak.stock_info_global_cls(symbol="全部")
            
            if df is None or df.empty:
                return []
            
            news_list = []
            cutoff_time = datetime.utcnow() - timedelta(hours=hours_back)
            
            for _, row in df.iterrows():
                try:
                    # 解析时间
                    pub_date = str(row.get("发布日期", ""))
                    pub_time = str(row.get("发布时间", ""))
                    datetime_str = f"{pub_date} {pub_time}"
                    
                    # 尝试解析时间过滤
                    try:
                        news_time = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")
                        if news_time < cutoff_time:
                            continue
                    except ValueError:
                        pass  # 无法解析时间则不过滤
                    
                    content = clean_html_tags(str(row.get("内容", "")))
                    title = clean_html_tags(str(row.get("标题", "")))
                    
                    # 计算内容哈希
                    content_hash = hashlib.md5(content.encode('utf-8')).hexdigest()
                    
                    news_list.append({
                        "title": title,
                        "content": content,
                        "datetime": datetime_str,
                        "source": "财联社",
                        "hash": content_hash
                    })
                    
                except Exception as e:
                    logger.warning(f"处理新闻条目失败: {e}")
                    continue
            
            # 按时间倒序排序并限制数量
            news_list.sort(key=lambda x: x.get("datetime", ""), reverse=True)
            return news_list[:limit]
            
        except Exception as e:
            logger.error(f"同步获取财联社新闻失败: {e}", exc_info=True)
            return []

    async def get_industry_fund_flow(self, top_n: int = 15, flow_type: str = "inflow") -> Dict[str, Any]:
        """
        获取行业资金流排行

        Args:
            top_n: 返回前N个
            flow_type: 流向类型 - "inflow"(净流入) 或 "outflow"(净流出)

        Returns:
            包含流入和流出两个榜单的字典
        """
        cache_key = f"industry_fund_flow_{top_n}"

        if self._is_cache_valid(cache_key):
            cached = self._cache[cache_key]
            return cached.get(flow_type, cached.get("inflow", []))

        try:
            result = await asyncio.to_thread(self._fetch_industry_fund_flow_sync, top_n)

            self._cache[cache_key] = result
            self._cache_time[cache_key] = datetime.utcnow()

            return result.get(flow_type, result.get("inflow", []))

        except Exception as e:
            logger.error(f"获取行业资金流失败: {e}", exc_info=True)
            return []

    def _fetch_industry_fund_flow_sync(self, top_n: int) -> Dict[str, List[Dict[str, Any]]]:
        """同步获取行业资金流，直接调用东方财富 API"""
        try:
            import requests

            # 流入榜单：po=1 表示降序排列（正数在前）
            inflow_params = EASTMONEY_API_COMMON_PARAMS.copy()
            inflow_params["fid"] = "f62"
            inflow_params["po"] = "1"  # 降序
            inflow_params["fs"] = EASTMONEY_INDUSTRY_FS

            resp_inflow = requests.get(EASTMONEY_API_BASE, params=inflow_params, timeout=10)
            resp_inflow.raise_for_status()
            data_inflow = resp_inflow.json()

            # 流出榜单：po=0 表示升序排列（负数在前）
            outflow_params = EASTMONEY_API_COMMON_PARAMS.copy()
            outflow_params["fid"] = "f62"
            outflow_params["po"] = "0"  # 升序
            outflow_params["fs"] = EASTMONEY_INDUSTRY_FS

            resp_outflow = requests.get(EASTMONEY_API_BASE, params=outflow_params, timeout=10)
            resp_outflow.raise_for_status()
            data_outflow = resp_outflow.json()

            # 解析流入榜单
            inflow_list = []
            if data_inflow.get("rc") == 0 and data_inflow.get("data", {}).get("diff"):
                diff = data_inflow["data"]["diff"]
                items = list(diff.values()) if isinstance(diff, dict) else diff
                # 过滤正值
                positive_items = [x for x in items if x.get("f62") and x["f62"] > 0]
                for idx, item in enumerate(positive_items[:top_n], 1):
                    net_inflow = round((item.get("f62", 0) or 0) / 100000000, 2)
                    inflow_list.append({
                        "rank": idx,
                        "name": item.get("f14", "未知"),
                        "inflow": net_inflow,
                        "unit": "亿元"
                    })

            # 解析流出榜单
            outflow_list = []
            if data_outflow.get("rc") == 0 and data_outflow.get("data", {}).get("diff"):
                diff = data_outflow["data"]["diff"]
                items = list(diff.values()) if isinstance(diff, dict) else diff
                # 过滤负值
                negative_items = [x for x in items if x.get("f62") and x["f62"] < 0]
                for idx, item in enumerate(negative_items[:top_n], 1):
                    net_inflow = round((item.get("f62", 0) or 0) / 100000000, 2)
                    outflow_list.append({
                        "rank": idx,
                        "name": item.get("f14", "未知"),
                        "inflow": net_inflow,
                        "unit": "亿元"
                    })

            return {"inflow": inflow_list, "outflow": outflow_list}

        except Exception as e:
            logger.error(f"获取行业资金流失败: {e}", exc_info=True)
            return {"inflow": [], "outflow": []}

    async def get_concept_fund_flow(self, top_n: int = 15, flow_type: str = "inflow") -> List[Dict[str, Any]]:
        """
        获取概念板块资金流排行

        Args:
            top_n: 返回前N个
            flow_type: 流向类型 - "inflow"(净流入) 或 "outflow"(净流出)

        Returns:
            概念板块资金流列表
        """
        cache_key = f"concept_fund_flow_{top_n}"

        if self._is_cache_valid(cache_key):
            cached = self._cache[cache_key]
            return cached.get(flow_type, cached.get("inflow", []))

        try:
            result = await asyncio.to_thread(self._fetch_concept_fund_flow_sync, top_n)

            self._cache[cache_key] = result
            self._cache_time[cache_key] = datetime.utcnow()

            return result.get(flow_type, result.get("inflow", []))

        except Exception as e:
            logger.error(f"获取概念板块资金流失败: {e}", exc_info=True)
            return []

    def _fetch_concept_fund_flow_sync(self, top_n: int) -> Dict[str, List[Dict[str, Any]]]:
        """同步获取概念板块资金流，直接调用东方财富 API"""
        try:
            import requests

            # 流入榜单：po=1 表示降序排列（正数在前）
            inflow_params = EASTMONEY_API_COMMON_PARAMS.copy()
            inflow_params["fid"] = "f62"
            inflow_params["po"] = "1"  # 降序
            inflow_params["fs"] = EASTMONEY_CONCEPT_FS

            resp_inflow = requests.get(EASTMONEY_API_BASE, params=inflow_params, timeout=10)
            resp_inflow.raise_for_status()
            data_inflow = resp_inflow.json()

            # 流出榜单：po=0 表示升序排列（负数在前）
            outflow_params = EASTMONEY_API_COMMON_PARAMS.copy()
            outflow_params["fid"] = "f62"
            outflow_params["po"] = "0"  # 升序
            outflow_params["fs"] = EASTMONEY_CONCEPT_FS

            resp_outflow = requests.get(EASTMONEY_API_BASE, params=outflow_params, timeout=10)
            resp_outflow.raise_for_status()
            data_outflow = resp_outflow.json()

            # 解析流入榜单
            inflow_list = []
            if data_inflow.get("rc") == 0 and data_inflow.get("data", {}).get("diff"):
                diff = data_inflow["data"]["diff"]
                items = list(diff.values()) if isinstance(diff, dict) else diff
                # 过滤正值
                positive_items = [x for x in items if x.get("f62") and x["f62"] > 0]
                for idx, item in enumerate(positive_items[:top_n], 1):
                    net_inflow = round((item.get("f62", 0) or 0) / 100000000, 2)
                    inflow_list.append({
                        "rank": idx,
                        "name": item.get("f14", "未知"),
                        "inflow": net_inflow,
                        "unit": "亿元"
                    })

            # 解析流出榜单
            outflow_list = []
            if data_outflow.get("rc") == 0 and data_outflow.get("data", {}).get("diff"):
                diff = data_outflow["data"]["diff"]
                items = list(diff.values()) if isinstance(diff, dict) else diff
                # 过滤负值
                negative_items = [x for x in items if x.get("f62") and x["f62"] < 0]
                for idx, item in enumerate(negative_items[:top_n], 1):
                    net_inflow = round((item.get("f62", 0) or 0) / 100000000, 2)
                    outflow_list.append({
                        "rank": idx,
                        "name": item.get("f14", "未知"),
                        "inflow": net_inflow,
                        "unit": "亿元"
                    })

            return {"inflow": inflow_list, "outflow": outflow_list}

        except Exception as e:
            logger.error(f"获取概念板块资金流失败: {e}", exc_info=True)
            return {"inflow": [], "outflow": []}

    async def get_market_overview(self, flow_type: str = "inflow") -> Dict[str, Any]:
        """
        获取市场概览（聚合数据）

        Args:
            flow_type: 流向类型 - "inflow"(净流入) 或 "outflow"(净流出)

        Returns:
            包含新闻和资金流的聚合数据
        """
        try:
            # 并行获取数据
            news_task = self.get_cla_news(limit=30, hours_back=24)
            industry_task = self.get_industry_fund_flow(top_n=15, flow_type=flow_type)
            concept_task = self.get_concept_fund_flow(top_n=15, flow_type=flow_type)

            news, industry_flow, concept_flow = await asyncio.gather(
                news_task, industry_task, concept_task
            )

            return {
                "news": news,
                "industry_fund_flow": industry_flow,
                "concept_fund_flow": concept_flow,
                "flow_type": flow_type,
                "update_time": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"获取市场概览失败: {e}", exc_info=True)
            return {
                "news": [],
                "industry_fund_flow": [],
                "concept_fund_flow": [],
                "flow_type": flow_type,
                "update_time": datetime.utcnow().isoformat(),
                "error": str(e)
            }


# 全局单例
_market_overview_service: Optional[MarketOverviewService] = None


def get_market_overview_service() -> MarketOverviewService:
    """获取市场概览服务单例"""
    global _market_overview_service
    if _market_overview_service is None:
        _market_overview_service = MarketOverviewService()
    return _market_overview_service
