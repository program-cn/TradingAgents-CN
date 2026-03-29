#!/usr/bin/env python3
"""
App 缓存读取适配器（TradingAgents -> app MongoDB 集合）
- 基本信息集合：stock_basic_info
- 行情集合：market_quotes

当启用 ta_use_app_cache 时，作为优先数据源；未命中部分由上层继续回退到直连数据源。
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from datetime import datetime

import pandas as pd
import logging

_logger = logging.getLogger('dataflows')

try:
    from tradingagents.config.database_manager import get_mongodb_client
except Exception:  # pragma: no cover - 弱依赖
    get_mongodb_client = None  # type: ignore


BASICS_COLLECTION = "stock_basic_info"
QUOTES_COLLECTION = "market_quotes"


def _normalize_code_for_query(symbol: str) -> str:
    """
    根据市场类型规范化股票代码用于查询
    
    A股: 填充到6位 (如 600036, 000001)
    港股: 保持原样 (如 700, 1810, 02533)
    美股: 保持原样 (如 AAPL, MSFT)
    """
    try:
        from tradingagents.utils.stock_utils import StockUtils, StockMarket
        market = StockUtils.identify_stock_market(symbol)
        
        if market == StockMarket.CHINA_A:
            # A股代码填充到6位
            return str(symbol).zfill(6)
        else:
            # 港股和美股保持原样
            return str(symbol)
    except Exception:
        # 降级：默认填充到6位（兼容旧逻辑）
        return str(symbol).zfill(6)


def get_basics_from_cache(stock_code: Optional[str] = None) -> Optional[Dict[str, Any] | List[Dict[str, Any]]]:
    """从 app 的 stock_basic_info 读取基础信息。"""
    if get_mongodb_client is None:
        return None
    client = get_mongodb_client()
    if not client:
        return None
    try:
        # 数据库名取自 DatabaseManager 内部配置
        db_name = None
        try:
            # 访问 DatabaseManager 暴露的配置
            from tradingagents.config.database_manager import get_database_manager  # type: ignore
            db_name = get_database_manager().mongodb_config.get("database", "tradingagents")
        except Exception:
            db_name = "tradingagents"
        db = client[db_name]
        coll = db[BASICS_COLLECTION]
        if stock_code:
            # 🔥 根据市场类型规范化代码（港股不填充）
            normalized_code = _normalize_code_for_query(stock_code)
            try:
                _logger.debug(f"[app_cache] 查询基础信息 | db={db_name} coll={BASICS_COLLECTION} code={normalized_code}")
            except Exception:
                pass
            # 同时查询 symbol 和 code 字段，确保兼容新旧数据格式
            doc = coll.find_one({"$or": [{"symbol": normalized_code}, {"code": normalized_code}]})
            if not doc:
                try:
                    _logger.debug(f"[app_cache] 基础信息未命中 | db={db_name} coll={BASICS_COLLECTION} code={normalized_code}")
                except Exception:
                    pass
            return doc or None
        else:
            cursor = coll.find({})
            docs = list(cursor)
            return docs or None
    except Exception as e:
        try:
            _logger.debug(f"[app_cache] 基础信息读取异常（忽略）: {e}")
        except Exception:
            pass
        return None


def get_market_quote_dataframe(symbol: str) -> Optional[pd.DataFrame]:
    """从 app 的 market_quotes 读取单只股票的最新一条快照，并转为 DataFrame。"""
    if get_mongodb_client is None:
        return None
    client = get_mongodb_client()
    if not client:
        return None
    try:
        # 获取数据库
        from tradingagents.config.database_manager import get_database_manager  # type: ignore
        db_name = get_database_manager().mongodb_config.get("database", "tradingagents")
        db = client[db_name]
        coll = db[QUOTES_COLLECTION]
        # 🔥 根据市场类型规范化代码（港股不填充）
        normalized_code = _normalize_code_for_query(symbol)
        try:
            _logger.debug(f"[app_cache] 查询行情 | db={db_name} coll={QUOTES_COLLECTION} code={normalized_code}")
        except Exception:
            pass
        doc = coll.find_one({"code": normalized_code})
        if not doc:
            try:
                _logger.debug(f"[app_cache] 行情未命中 | db={db_name} coll={QUOTES_COLLECTION} code={normalized_code}")
            except Exception:
                pass
            return None
        # 构造 DataFrame，字段对齐 tushare 标准化映射
        row = {
            "code": normalized_code,
            "date": doc.get("trade_date"),  # YYYYMMDD
            "open": doc.get("open"),
            "high": doc.get("high"),
            "low": doc.get("low"),
            "close": doc.get("close"),
            "volume": doc.get("volume"),
            "amount": doc.get("amount"),
            "pct_chg": doc.get("pct_chg"),
            "change": None,
        }
        df = pd.DataFrame([row])
        return df
    except Exception as e:
        try:
            _logger.debug(f"[app_cache] 行情读取异常（忽略）: {e}")
        except Exception:
            pass
        return None

