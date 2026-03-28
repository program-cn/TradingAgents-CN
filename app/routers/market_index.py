"""
市场指数API - 获取A股、港股、美股主要指数行情和历史数据
"""
from typing import Optional, List
from fastapi import APIRouter, Query
from datetime import datetime, timedelta
import logging
import pandas as pd

from app.core.response import ok

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/market", tags=["market"])

# A股主要指数配置
CN_INDEXES = {
    'sh000001': {'name': '上证指数', 'market': 'CN', 'code_ak': '000001'},
    'sz399001': {'name': '深证成指', 'market': 'CN', 'code_ak': '399001'},
    'sz399006': {'name': '创业板指', 'market': 'CN', 'code_ak': '399006'},
    'sh000300': {'name': '沪深300', 'market': 'CN', 'code_ak': '000300'},
    'sh000016': {'name': '上证50', 'market': 'CN', 'code_ak': '000016'},
    'sh000905': {'name': '中证500', 'market': 'CN', 'code_ak': '000905'},
    'sh000688': {'name': '科创50', 'market': 'CN', 'code_ak': '000688'},
}

# 港股主要指数配置
HK_INDEXES = {
    'HSI': {'name': '恒生指数', 'market': 'HK', 'code_ak': 'HSI'},
    'HSCEI': {'name': '国企指数', 'market': 'HK', 'code_ak': 'HSCEI'},
    'HSTECH': {'name': '恒生科技', 'market': 'HK', 'code_ak': 'HSTECH'},
}

# 美股主要指数配置
US_INDEXES = {
    'DJIA': {'name': '道琼斯', 'market': 'US', 'code_ak': 'DJIA'},
    'NDX': {'name': '纳斯达克', 'market': 'US', 'code_ak': 'NDX'},
    'SPX': {'name': '标普500', 'market': 'US', 'code_ak': 'SPX'},
}


@router.get("/indexes", response_model=dict)
async def get_market_indexes():
    """
    获取主要市场指数实时行情
    
    返回A股、港股、美股主要指数的实时数据
    """
    try:
        import akshare as ak
    except ImportError:
        return ok(data=[], message="AKShare未安装")
    
    try:
        indexes = []
        
        # 1. 获取A股指数
        try:
            df_sh = ak.stock_zh_index_spot_em(symbol="上证系列指数")
            df_sz = ak.stock_zh_index_spot_em(symbol="深证系列指数")
            df_cn = pd.concat([df_sh, df_sz], ignore_index=True)
            
            for code, info in CN_INDEXES.items():
                row = df_cn[df_cn['代码'] == info['code_ak']]
                if not row.empty:
                    row = row.iloc[0]
                    change_pct = float(row.get('涨跌幅', 0))
                    indexes.append({
                        'code': code,
                        'name': info['name'],
                        'market': 'CN',
                        'price': float(row.get('最新价', 0)),
                        'change': float(row.get('涨跌点数', 0)),
                        'change_percent': round(change_pct, 2),
                        'volume': float(row.get('成交量', 0)),
                        'amount': float(row.get('成交额', 0)),
                        'high': float(row.get('最高', 0)),
                        'low': float(row.get('最低', 0)),
                        'open': float(row.get('今开', 0)),
                        'prev_close': float(row.get('昨收', 0)),
                        'is_up': change_pct > 0,
                        'is_down': change_pct < 0,
                    })
        except Exception as e:
            logger.warning(f"获取A股指数失败: {e}")
        
        # 2. 获取港股和美股指数（使用全球指数接口）
        try:
            df_global = ak.index_global_spot_em()
            
            # 港股指数
            for code, info in HK_INDEXES.items():
                row = df_global[df_global['代码'] == info['code_ak']]
                if not row.empty:
                    row = row.iloc[0]
                    change_pct = float(row.get('涨跌幅', 0))
                    indexes.append({
                        'code': code,
                        'name': info['name'],
                        'market': 'HK',
                        'price': float(row.get('最新价', 0)),
                        'change': float(row.get('涨跌额', 0)),
                        'change_percent': round(change_pct, 2),
                        'high': float(row.get('最高价', 0)),
                        'low': float(row.get('最低价', 0)),
                        'open': float(row.get('开盘价', 0)),
                        'prev_close': float(row.get('昨收价', 0)),
                        'is_up': change_pct > 0,
                        'is_down': change_pct < 0,
                    })
            
            # 美股指数
            for code, info in US_INDEXES.items():
                row = df_global[df_global['代码'] == info['code_ak']]
                if not row.empty:
                    row = row.iloc[0]
                    change_pct = float(row.get('涨跌幅', 0))
                    indexes.append({
                        'code': code,
                        'name': info['name'],
                        'market': 'US',
                        'price': float(row.get('最新价', 0)),
                        'change': float(row.get('涨跌额', 0)),
                        'change_percent': round(change_pct, 2),
                        'high': float(row.get('最高价', 0)),
                        'low': float(row.get('最低价', 0)),
                        'open': float(row.get('开盘价', 0)),
                        'prev_close': float(row.get('昨收价', 0)),
                        'is_up': change_pct > 0,
                        'is_down': change_pct < 0,
                    })
        except Exception as e:
            logger.warning(f"获取全球指数失败: {e}")
        
        return ok(data=indexes)
        
    except Exception as e:
        logger.error(f"获取市场指数失败: {e}")
        return ok(data=[], message=f"获取指数数据失败: {str(e)}")


@router.get("/index/{code}/history", response_model=dict)
async def get_index_history(
    code: str,
    period: str = Query('1m', description="周期: 1d(1天), 1w(1周), 1m(1月), 1y(1年)")
):
    """
    获取指数历史K线数据
    
    参数：
    - code: 指数代码（如 sh000001, HSI, DJIA）
    - period: 周期 1d/1w/1m/1y
    
    返回K线数据用于绘制缩略图
    """
    try:
        import akshare as ak
    except ImportError:
        return ok(data=[], message="AKShare未安装")
    
    try:
        # 计算日期范围
        end_date = datetime.now()
        period_map = {
            '1d': 1,
            '1w': 7,
            '1m': 30,
            '1y': 365,
        }
        days = period_map.get(period, 30)
        start_date = end_date - timedelta(days=days)
        
        code_upper = code.upper()
        
        # A股指数
        if code.startswith(('sh', 'sz')):
            code_lower = code.lower()
            ak_code = code_lower[2:] if code_lower.startswith(('sh', 'sz')) else code_lower.zfill(6)
            market = 'sh' if code_lower.startswith('sh') else 'sz'
            df = ak.stock_zh_index_daily(symbol=f"{market}{ak_code}")
            
            if df is None or df.empty:
                return ok(data=[], message="未找到指数数据")
            
            df['date'] = pd.to_datetime(df['date'])
            df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]
            
            history = []
            for _, row in df.iterrows():
                history.append({
                    'date': row['date'].strftime('%Y-%m-%d'),
                    'timestamp': int(row['date'].timestamp() * 1000),
                    'open': float(row['open']),
                    'high': float(row['high']),
                    'low': float(row['low']),
                    'close': float(row['close']),
                    'volume': float(row.get('volume', 0)),
                })
            
            return ok(data=history)
        
        # 港股/美股指数（使用全球指数历史接口）
        else:
            try:
                # 获取历史数据
                df = ak.index_global_hist_em(symbol=code_upper)
                
                if df is None or df.empty:
                    return ok(data=[], message="未找到指数数据")
                
                # 筛选日期范围
                df['日期'] = pd.to_datetime(df['日期'])
                df = df[(df['日期'] >= start_date) & (df['日期'] <= end_date)]
                
                history = []
                for _, row in df.iterrows():
                    history.append({
                        'date': row['日期'].strftime('%Y-%m-%d'),
                        'open': float(row.get('今开', 0)),
                        'high': float(row.get('最高', 0)),
                        'low': float(row.get('最低', 0)),
                        'close': float(row.get('最新价', 0)),
                        'volume': 0,
                    })
                
                return ok(data=history)
            except Exception as e:
                logger.warning(f"获取全球指数历史数据失败: {e}")
                return ok(data=[], message=f"获取历史数据失败: {str(e)}")
        
    except Exception as e:
        logger.error(f"获取指数历史数据失败: {e}")
        return ok(data=[], message=f"获取历史数据失败: {str(e)}")


@router.get("/indexes/with-sparkline", response_model=dict)
async def get_indexes_with_sparkline(
    period: str = Query('1m', description="周期: 1d/1w/1m/1y")
):
    """
    获取主要指数及缩略曲线数据（一次性获取所有数据，减少请求次数）
    """
    try:
        import akshare as ak
        import pandas as pd
    except ImportError:
        return ok(data=[], message="AKShare未安装")
    
    try:
        indexes = []
        
        # 计算日期范围
        end_date = datetime.now()
        period_map = {
            '1d': 1,
            '1w': 7,
            '1m': 30,
            '1y': 365,
        }
        days = period_map.get(period, 30)
        start_date = end_date - timedelta(days=days)
        
        # 1. 获取A股指数及历史数据
        try:
            df_sh = ak.stock_zh_index_spot_em(symbol="上证系列指数")
            df_sz = ak.stock_zh_index_spot_em(symbol="深证系列指数")
            df_cn = pd.concat([df_sh, df_sz], ignore_index=True)
            
            for code, info in CN_INDEXES.items():
                index_data = {
                    'code': code,
                    'name': info['name'],
                    'market': 'CN',
                    'sparkline': []
                }
                
                # 获取实时行情
                row = df_cn[df_cn['代码'] == info['code_ak']]
                if not row.empty:
                    row = row.iloc[0]
                    change_pct = float(row.get('涨跌幅', 0))
                    index_data.update({
                        'price': float(row.get('最新价', 0)),
                        'change': float(row.get('涨跌点数', 0)),
                        'change_percent': round(change_pct, 2),
                        'is_up': change_pct > 0,
                        'is_down': change_pct < 0,
                    })
                else:
                    index_data.update({
                        'price': 0,
                        'change': 0,
                        'change_percent': 0,
                        'is_up': False,
                        'is_down': False,
                    })
                
                # 获取历史数据用于缩略图
                try:
                    ak_code = info['code_ak']
                    market = 'sh' if code.startswith('sh') else 'sz'
                    df_hist = ak.stock_zh_index_daily(symbol=f"{market}{ak_code}")
                    
                    if df_hist is not None and not df_hist.empty:
                        df_hist['date'] = pd.to_datetime(df_hist['date'])
                        df_hist = df_hist[(df_hist['date'] >= start_date) & (df_hist['date'] <= end_date)]
                        
                        sparkline = []
                        for _, r in df_hist.iterrows():
                            sparkline.append({
                                'date': r['date'].strftime('%m-%d'),
                                'value': float(r['close'])
                            })
                        
                        index_data['sparkline'] = sparkline[-30:]
                        
                except Exception as e:
                    logger.warning(f"获取{code}历史数据失败: {e}")
                
                indexes.append(index_data)
        except Exception as e:
            logger.warning(f"获取A股指数失败: {e}")
        
        # 2. 获取港股和美股指数（使用全球指数接口）
        try:
            df_global = ak.index_global_spot_em()
            # 港股指数还需要从港股指数接口获取HSTECH
            df_hk = ak.stock_hk_index_spot_em()
            
            # 港股指数
            for code, info in HK_INDEXES.items():
                index_data = {
                    'code': code,
                    'name': info['name'],
                    'market': 'HK',
                    'sparkline': []
                }
                
                # 先从全球指数接口获取
                row = df_global[df_global['代码'] == info['code_ak']]
                if not row.empty:
                    row = row.iloc[0]
                    change_pct = float(row.get('涨跌幅', 0))
                    index_data.update({
                        'price': float(row.get('最新价', 0)),
                        'change': float(row.get('涨跌额', 0)),
                        'change_percent': round(change_pct, 2),
                        'is_up': change_pct > 0,
                        'is_down': change_pct < 0,
                    })
                else:
                    # 尝试从港股指数接口获取（如HSTECH）
                    row = df_hk[df_hk['代码'] == info['code_ak']]
                    if not row.empty:
                        row = row.iloc[0]
                        change_pct = float(row.get('涨跌幅', 0))
                        index_data.update({
                            'price': float(row.get('最新价', 0)),
                            'change': float(row.get('涨跌点数', 0)),
                            'change_percent': round(change_pct, 2),
                            'is_up': change_pct > 0,
                            'is_down': change_pct < 0,
                        })
                    else:
                        index_data.update({
                            'price': 0,
                            'change': 0,
                            'change_percent': 0,
                            'is_up': False,
                            'is_down': False,
                        })
                
                # 获取历史数据
                try:
                    df_hist = ak.index_global_hist_em(symbol=info['name'])
                    if df_hist is not None and not df_hist.empty:
                        # 筛选日期范围
                        df_hist['日期'] = pd.to_datetime(df_hist['日期'])
                        df_hist = df_hist[(df_hist['日期'] >= start_date) & (df_hist['日期'] <= end_date)]
                        sparkline = []
                        for _, r in df_hist.iterrows():
                            date_str = r['日期'].strftime('%m-%d')
                            sparkline.append({
                                'date': date_str,
                                'value': float(r['最新价'])
                            })
                        index_data['sparkline'] = sparkline[-30:]
                except Exception as e:
                    logger.warning(f"获取{code}历史数据失败: {e}")
                
                indexes.append(index_data)
            
            # 美股指数
            for code, info in US_INDEXES.items():
                index_data = {
                    'code': code,
                    'name': info['name'],
                    'market': 'US',
                    'sparkline': []
                }
                
                row = df_global[df_global['代码'] == info['code_ak']]
                if not row.empty:
                    row = row.iloc[0]
                    change_pct = float(row.get('涨跌幅', 0))
                    index_data.update({
                        'price': float(row.get('最新价', 0)),
                        'change': float(row.get('涨跌额', 0)),
                        'change_percent': round(change_pct, 2),
                        'is_up': change_pct > 0,
                        'is_down': change_pct < 0,
                    })
                else:
                    index_data.update({
                        'price': 0,
                        'change': 0,
                        'change_percent': 0,
                        'is_up': False,
                        'is_down': False,
                    })
                
                # 获取历史数据
                try:
                    df_hist = ak.index_global_hist_em(symbol=info['name'])
                    if df_hist is not None and not df_hist.empty:
                        # 筛选日期范围
                        df_hist['日期'] = pd.to_datetime(df_hist['日期'])
                        df_hist = df_hist[(df_hist['日期'] >= start_date) & (df_hist['日期'] <= end_date)]
                        sparkline = []
                        for _, r in df_hist.iterrows():
                            date_str = r['日期'].strftime('%m-%d')
                            sparkline.append({
                                'date': date_str,
                                'value': float(r['最新价'])
                            })
                        index_data['sparkline'] = sparkline[-30:]
                except Exception as e:
                    logger.warning(f"获取{code}历史数据失败: {e}")
                
                indexes.append(index_data)
                
        except Exception as e:
            logger.warning(f"获取全球指数失败: {e}")
        
        return ok(data=indexes)
        
    except Exception as e:
        logger.error(f"获取指数数据失败: {e}")
        return ok(data=[], message=f"获取数据失败: {str(e)}")
