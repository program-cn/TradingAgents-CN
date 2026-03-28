"""
机构分析师工具 - 北向资金、基金重仓、龙虎榜分析
A股特色数据获取和分析
"""

from langchain_core.tools import tool
from typing import Annotated, Dict, Any, List, Optional
import pandas as pd
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class InstitutionalDataFetcher:
    """机构数据获取器"""
    
    def __init__(self):
        self._akshare = None
    
    @property
    def akshare(self):
        """延迟加载 akshare"""
        if self._akshare is None:
            import akshare as ak
            self._akshare = ak
        return self._akshare
    
    def get_north_money_flow(self, days: int = 30) -> pd.DataFrame:
        """
        获取北向资金流向数据
        
        Args:
            days: 获取最近多少天的数据
            
        Returns:
            DataFrame: 北向资金流向数据
        """
        try:
            logger.info(f"📊 [北向资金] 获取最近 {days} 天的北向资金数据")

            # 使用 AKShare 获取北向资金数据（新接口）
            df = self.akshare.stock_hsgt_hist_em(symbol="北向资金")

            if df is not None and not df.empty:
                # 按日期排序，取最近N天
                df = df.sort_values('日期', ascending=False)
                # 过滤掉无效数据（NaN）
                df = df[df['当日成交净买额'].notna()].head(days)
                logger.info(f"✅ [北向资金] 获取成功，共 {len(df)} 条记录")
                return df
            else:
                logger.warning("⚠️ [北向资金] 数据为空")
                return None
                
        except Exception as e:
            logger.error(f"❌ [北向资金] 获取失败: {e}")
            return None
    
    def get_stock_north_money_holding(self, symbol: str) -> Dict[str, Any]:
        """
        获取个股北向资金持股数据

        Args:
            symbol: 股票代码（6位数字）

        Returns:
            Dict: 北向资金持股数据
        """
        try:
            logger.info(f"📊 [北向持股] 获取股票 {symbol} 的北向资金持股数据")

            # 使用新接口获取北向持股排行，然后筛选目标股票
            df = self.akshare.stock_hsgt_hold_stock_em(market="北向持股", indicator="今日排行")

            if df is not None and not df.empty:
                # 从排行中筛选目标股票
                stock_data = df[df['代码'] == symbol]

                if stock_data.empty:
                    logger.warning(f"⚠️ [北向持股] 股票 {symbol} 不在北向持股排行中")
                    return None

                latest = stock_data.iloc[0]
                result = {
                    'symbol': symbol,
                    'name': latest.get('名称', ''),
                    'holding_shares': latest.get('今日持股-股数', 0),
                    'holding_value': latest.get('今日持股-市值', 0),
                    'holding_ratio': latest.get('今日持股-占流通股比', 0),
                    'change_5d_shares': latest.get('5日增持估计-股数', 0),
                    'change_5d_value': latest.get('5日增持估计-市值', 0),
                    'latest_date': latest.get('日期', ''),
                }
                logger.info(f"✅ [北向持股] 获取成功，持股比例: {result['holding_ratio']:.2f}%")
                return result
            else:
                logger.warning(f"⚠️ [北向持股] 无法获取北向持股数据")
                return None

        except Exception as e:
            logger.error(f"❌ [北向持股] 获取失败: {e}")
            return None
    
    def get_fund_holdings(self, symbol: str, quarter: str = None) -> Dict[str, Any]:
        """
        获取基金持股数据

        Args:
            symbol: 股票代码（6位数字）
            quarter: 季度（如 "2024Q3"），默认取最新

        Returns:
            Dict: 基金持股数据
        """
        try:
            logger.info(f"📊 [基金持股] 获取股票 {symbol} 的基金持股数据")

            # 使用新接口获取基金持股数据
            df = self.akshare.stock_report_fund_hold(symbol=symbol)

            if df is not None and not df.empty:
                # 取最新数据
                latest = df.iloc[0] if len(df) > 0 else None

                result = {
                    'symbol': symbol,
                    'quarter': latest.get('季度', '') if latest is not None else '',
                    'fund_count': latest.get('基金家数', 0) if latest is not None else 0,
                    'holding_shares': latest.get('持股数量', 0) if latest is not None else 0,
                    'holding_value': latest.get('持股市值', 0) if latest is not None else 0,
                    'holding_ratio': latest.get('持股占流通股比', 0) if latest is not None else 0,
                    'change_ratio': latest.get('持股比例变化', 0) if latest is not None else 0,
                    'data': df.to_dict('records')[:5]  # 最近5条记录
                }
                logger.info(f"✅ [基金持股] 获取成功，共 {result['fund_count']} 只基金持有")
                return result
            else:
                logger.warning(f"⚠️ [基金持股] 股票 {symbol} 无基金持股数据")
                return None
                
        except Exception as e:
            logger.error(f"❌ [基金持股] 获取失败: {e}")
            return None
    
    def get_lhb_list(self, symbol: str = None, days: int = 30) -> pd.DataFrame:
        """
        获取龙虎榜数据
        
        Args:
            symbol: 股票代码（可选，不传则获取全部龙虎榜）
            days: 获取最近多少天的数据
            
        Returns:
            DataFrame: 龙虎榜数据
        """
        try:
            logger.info(f"📊 [龙虎榜] 获取龙虎榜数据，股票: {symbol or '全部'}")
            
            # 使用 AKShare 获取龙虎榜数据
            today = datetime.now()
            start_date = (today - timedelta(days=days)).strftime('%Y%m%d')
            end_date = today.strftime('%Y%m%d')
            
            df = self.akshare.stock_lhb_detail_em(start_date=start_date, end_date=end_date)
            
            if df is not None and not df.empty:
                # 如果指定了股票代码，过滤
                if symbol:
                    df = df[df['代码'] == symbol]
                
                logger.info(f"✅ [龙虎榜] 获取成功，共 {len(df)} 条记录")
                return df
            else:
                logger.warning("⚠️ [龙虎榜] 数据为空")
                return None
                
        except Exception as e:
            logger.error(f"❌ [龙虎榜] 获取失败: {e}")
            return None
    
    def get_stock_lhb_detail(self, symbol: str, days: int = 30) -> Dict[str, Any]:
        """
        获取个股龙虎榜详细数据
        
        Args:
            symbol: 股票代码（6位数字）
            days: 获取最近多少天的数据
            
        Returns:
            Dict: 龙虎榜详细数据
        """
        try:
            logger.info(f"📊 [龙虎榜详情] 获取股票 {symbol} 的龙虎榜详情")
            
            df = self.get_lhb_list(symbol=symbol, days=days)
            
            if df is not None and not df.empty:
                # 分析龙虎榜数据
                total_buy = df['买入额'].sum() if '买入额' in df.columns else 0
                total_sell = df['卖出额'].sum() if '卖出额' in df.columns else 0
                net_buy = total_buy - total_sell
                
                # 统计上榜次数
                list_count = len(df)
                
                # 获取最近一次上榜详情
                latest_record = df.iloc[0].to_dict() if len(df) > 0 else None
                
                result = {
                    'symbol': symbol,
                    'list_count': list_count,  # 上榜次数
                    'total_buy': total_buy,    # 总买入
                    'total_sell': total_sell,  # 总卖出
                    'net_buy': net_buy,        # 净买入
                    'latest_record': latest_record,
                    'all_records': df.to_dict('records')[:10]  # 最近10条记录
                }
                logger.info(f"✅ [龙虎榜详情] 获取成功，上榜 {list_count} 次，净买入 {net_buy:.2f} 万")
                return result
            else:
                logger.warning(f"⚠️ [龙虎榜详情] 股票 {symbol} 近 {days} 天未上龙虎榜")
                return None
                
        except Exception as e:
            logger.error(f"❌ [龙虎榜详情] 获取失败: {e}")
            return None


# 创建全局实例
_fetcher = InstitutionalDataFetcher()


@tool
def get_north_money_flow(
    days: Annotated[int, "获取最近多少天的北向资金数据，默认30天"] = 30
) -> str:
    """
    获取北向资金（外资）流向数据。
    北向资金是A股市场的重要风向标，代表外资对A股的态度。
    
    Args:
        days: 获取最近多少天的数据，默认30天
        
    Returns:
        str: 北向资金流向分析报告
    """
    logger.info(f"📈 [工具调用] get_north_money_flow, days={days}")
    
    try:
        df = _fetcher.get_north_money_flow(days)
        
        if df is None or df.empty:
            return "暂无北向资金数据"
        
        # 格式化输出
        report_lines = [
            "# 北向资金流向分析",
            "",
            f"**数据时间范围**: 最近 {days} 天",
            "",
            "## 最近5日流向数据",
            "",
            "| 日期 | 净流入(亿) | 累计净流入(亿) |",
            "|------|-----------|---------------|"
        ]
        
        for _, row in df.head(5).iterrows():
            date = row.get('日期', '')
            # 兼容新旧列名
            net_flow = row.get('当日成交净买额', row.get('当日净流入', 0)) or 0
            cumulative = row.get('历史累计净买额', row.get('当日资金流入', 0)) or 0

            # 格式化为亿元（数据已经是亿元单位）
            net_flow_yi = net_flow if isinstance(net_flow, (int, float)) else 0
            cumulative_yi = cumulative if isinstance(cumulative, (int, float)) else 0

            report_lines.append(f"| {date} | {net_flow_yi:.2f} | {cumulative_yi:.2f} |")

        # 计算统计指标（兼容新旧列名）
        net_flow_col = '当日成交净买额' if '当日成交净买额' in df.columns else '当日净流入'
        total_net_flow = df[net_flow_col].sum() if net_flow_col in df.columns else 0
        avg_net_flow = df[net_flow_col].mean() if net_flow_col in df.columns else 0
        positive_days = len(df[df[net_flow_col] > 0]) if net_flow_col in df.columns else 0
        
        report_lines.extend([
            "",
            "## 统计分析",
            "",
            f"- **统计周期**: {days} 天",
            f"- **累计净流入**: {total_net_flow:.2f} 亿元",
            f"- **日均净流入**: {avg_net_flow:.2f} 亿元",
            f"- **净流入天数**: {positive_days} 天 ({positive_days/days*100:.1f}%)",
            "",
            "## 解读建议",
            ""
        ])
        
        if total_net_flow > 0:
            report_lines.append("- ✅ 北向资金整体呈流入态势，外资看好A股市场")
        else:
            report_lines.append("- ⚠️ 北向资金整体呈流出态势，外资态度谨慎")
        
        if positive_days > days * 0.6:
            report_lines.append("- ✅ 净流入天数占比较高，流入趋势明显")
        elif positive_days < days * 0.4:
            report_lines.append("- ⚠️ 净流出天数占比较高，流出趋势明显")
        else:
            report_lines.append("- 📊 资金流向波动较大，趋势不明显")
        
        return "\n".join(report_lines)
        
    except Exception as e:
        logger.error(f"❌ 北向资金工具执行失败: {e}")
        return f"北向资金数据获取失败: {str(e)}"


@tool
def get_stock_north_holding(
    symbol: Annotated[str, "股票代码，6位数字，如 000001"]
) -> str:
    """
    获取个股北向资金持股情况。
    分析外资对该股票的持仓变化，判断外资态度。
    
    Args:
        symbol: 股票代码（6位数字）
        
    Returns:
        str: 北向资金持股分析报告
    """
    logger.info(f"📈 [工具调用] get_stock_north_holding, symbol={symbol}")
    
    try:
        data = _fetcher.get_stock_north_money_holding(symbol)
        
        if data is None:
            return f"股票 {symbol} 暂无北向资金持股数据，可能原因：\n1. 该股票未被纳入港股通标的\n2. 外资尚未持有该股票"
        
        holding_ratio = data.get('holding_ratio', 0)
        change_5d = data.get('change_5d_shares', 0)

        report_lines = [
            f"# {symbol} 北向资金持股分析",
            "",
            f"**股票名称**: {data.get('name', '')}",
            f"**最新数据日期**: {data.get('latest_date', '未知')}",
            "",
            "## 持股概况",
            "",
            f"- **持股数量**: {data.get('holding_shares', 0):,.0f} 股",
            f"- **持股市值**: {data.get('holding_value', 0):,.2f} 万元",
            f"- **持股比例**: {holding_ratio:.2f}%",
            f"- **5日增持**: {change_5d:+,.0f} 股",
            "",
            "## 投资启示",
            ""
        ]

        if holding_ratio > 5:
            report_lines.append("- ✅ 北向资金持股比例较高，外资认可度强")
        elif holding_ratio > 1:
            report_lines.append("- 📊 北向资金持股比例适中，有一定外资关注")
        else:
            report_lines.append("- ⚠️ 北向资金持股比例较低，外资关注度有限")

        if change_5d > 0:
            report_lines.append("- ✅ 近5日北向资金增持，外资看好该股票")
        elif change_5d < 0:
            report_lines.append("- ⚠️ 近5日北向资金减持，外资态度谨慎")
        else:
            report_lines.append("- 📊 近5日北向资金持股稳定")
        
        return "\n".join(report_lines)
        
    except Exception as e:
        logger.error(f"❌ 北向持股工具执行失败: {e}")
        return f"北向持股数据获取失败: {str(e)}"


@tool
def get_stock_fund_holding(
    symbol: Annotated[str, "股票代码，6位数字，如 000001"],
    quarter: Annotated[str, "季度，如 2024Q3，默认取最新"] = None
) -> str:
    """
    获取基金持股数据。
    分析公募基金对该股票的持仓情况，判断机构认可度。
    
    Args:
        symbol: 股票代码（6位数字）
        quarter: 季度（如 2024Q3），默认取最新
        
    Returns:
        str: 基金持股分析报告
    """
    logger.info(f"📈 [工具调用] get_stock_fund_holding, symbol={symbol}, quarter={quarter}")
    
    try:
        data = _fetcher.get_fund_holdings(symbol, quarter)
        
        if data is None:
            return f"股票 {symbol} 暂无基金持股数据"
        
        report_lines = [
            f"# {symbol} 基金持股分析",
            "",
            f"**数据季度**: {data.get('quarter', '最新')}",
            "",
            "## 持股概况",
            "",
            f"- **持有基金数量**: {data.get('fund_count', 0)} 只",
            f"- **持股总量**: {data.get('holding_shares', 0):,.0f} 股",
            f"- **持股市值**: {data.get('holding_value', 0):,.2f} 万元",
            f"- **持股占流通股比**: {data.get('holding_ratio', 0):.2f}%",
            "",
            "## 投资启示",
            ""
        ]

        fund_count = data.get('fund_count', 0)
        if fund_count > 50:
            report_lines.append("- ✅ 基金持股数量多，机构认可度高")
        elif fund_count > 20:
            report_lines.append("- 📊 基金持股数量适中，有一定机构关注")
        elif fund_count > 5:
            report_lines.append("- ⚠️ 基金持股数量较少，机构关注度一般")
        else:
            report_lines.append("- ❌ 基金持股数量很少，机构认可度低")
        
        return "\n".join(report_lines)
        
    except Exception as e:
        logger.error(f"❌ 基金持股工具执行失败: {e}")
        return f"基金持股数据获取失败: {str(e)}"


@tool
def get_stock_lhb_analysis(
    symbol: Annotated[str, "股票代码，6位数字，如 000001"],
    days: Annotated[int, "查询最近多少天，默认30天"] = 30
) -> str:
    """
    获取龙虎榜分析数据。
    龙虎榜是A股特色数据，展示大额交易和异动股票的买卖席位。
    
    Args:
        symbol: 股票代码（6位数字）
        days: 查询最近多少天，默认30天
        
    Returns:
        str: 龙虎榜分析报告
    """
    logger.info(f"📈 [工具调用] get_stock_lhb_analysis, symbol={symbol}, days={days}")
    
    try:
        data = _fetcher.get_stock_lhb_detail(symbol, days)
        
        if data is None:
            return f"股票 {symbol} 近 {days} 天未登上龙虎榜，属于正常情况"
        
        report_lines = [
            f"# {symbol} 龙虎榜分析",
            "",
            f"**查询周期**: 近 {days} 天",
            "",
            "## 龙虎榜概况",
            "",
            f"- **上榜次数**: {data.get('list_count', 0)} 次",
            f"- **总买入额**: {data.get('total_buy', 0):,.2f} 万元",
            f"- **总卖出额**: {data.get('total_sell', 0):,.2f} 万元",
            f"- **净买入额**: {data.get('net_buy', 0):+,.2f} 万元",
            ""
        ]
        
        # 最新上榜详情
        latest = data.get('latest_record')
        if latest:
            report_lines.extend([
                "## 最新上榜详情",
                "",
                f"- **上榜日期**: {latest.get('日期', '')}",
                f"- **收盘价**: {latest.get('收盘价', 0)} 元",
                f"- **涨跌幅**: {latest.get('涨跌幅', 0)}%",
                f"- **买入额**: {latest.get('买入额', 0):,.2f} 万元",
                f"- **卖出额**: {latest.get('卖出额', 0):,.2f} 万元",
                ""
            ])
        
        # 历史上榜记录
        records = data.get('all_records', [])
        if records:
            report_lines.extend([
                "## 历史上榜记录",
                "",
                "| 日期 | 涨跌幅 | 买入额(万) | 卖出额(万) | 净买入(万) |",
                "|------|-------|-----------|-----------|-----------|"
            ])
            for r in records[:10]:
                net = (r.get('买入额', 0) or 0) - (r.get('卖出额', 0) or 0)
                report_lines.append(
                    f"| {r.get('日期', '')} | {r.get('涨跌幅', 0)}% | "
                    f"{r.get('买入额', 0):,.0f} | {r.get('卖出额', 0):,.0f} | {net:+,.0f} |"
                )
        
        # 分析解读
        net_buy = data.get('net_buy', 0)
        list_count = data.get('list_count', 0)
        
        report_lines.extend([
            "",
            "## 投资启示",
            ""
        ])
        
        if list_count >= 3:
            report_lines.append("- ⚠️ 近期频繁上榜，股票活跃度高，注意风险")
        elif list_count >= 1:
            report_lines.append("- 📊 近期有上榜记录，市场关注度增加")
        
        if net_buy > 0:
            report_lines.append("- ✅ 龙虎榜净买入为正，资金流入明显")
        elif net_buy < 0:
            report_lines.append("- ⚠️ 龙虎榜净卖出，资金流出明显")
        
        report_lines.extend([
            "",
            "**风险提示**: 龙虎榜数据反映的是短期大额交易，不能单独作为投资依据。"
        ])
        
        return "\n".join(report_lines)
        
    except Exception as e:
        logger.error(f"❌ 龙虎榜工具执行失败: {e}")
        return f"龙虎榜数据获取失败: {str(e)}"


@tool
def get_industry_comparison(
    symbol: Annotated[str, "股票代码，6位数字，如 000001"]
) -> str:
    """
    获取行业对比分析数据。
    将目标股票与同行业股票进行估值、财务指标对比分析。
    
    Args:
        symbol: 股票代码（6位数字）
        
    Returns:
        str: 行业对比分析报告
    """
    logger.info(f"📈 [工具调用] get_industry_comparison, symbol={symbol}")
    
    try:
        import akshare as ak
        
        # 1. 获取股票所属行业
        try:
            stock_info = ak.stock_individual_info_em(symbol=symbol)
            if stock_info is not None and not stock_info.empty:
                industry = stock_info[stock_info['item'] == '行业'].iloc[0]['value'] if len(stock_info[stock_info['item'] == '行业']) > 0 else '未知'
            else:
                industry = '未知'
        except:
            industry = '未知'
        
        report_lines = [
            f"# {symbol} 行业对比分析",
            "",
            f"**所属行业**: {industry}",
            ""
        ]
        
        # 2. 获取个股财务指标
        try:
            financial_df = ak.stock_financial_analysis_indicator(symbol=symbol)
            
            if financial_df is not None and not financial_df.empty:
                latest = financial_df.iloc[0]
                
                report_lines.extend([
                    "## 个股财务指标",
                    "",
                    "| 指标 | 数值 |",
                    "|------|------|"
                ])
                
                # 主要财务指标
                key_indicators = [
                    ('净资产收益率', 'roe'),
                    ('净利润率', 'net_profit_margin'),
                    ('资产负债率', 'debt_to_assets'),
                    ('流动比率', 'current_ratio'),
                ]
                
                indicator_values = {}
                for cn_name, en_name in key_indicators:
                    try:
                        value = latest.get(cn_name, 'N/A')
                        if value != 'N/A':
                            indicator_values[cn_name] = value
                            report_lines.append(f"| {cn_name} | {value} |")
                    except:
                        pass
                
        except Exception as e:
            report_lines.append(f"个股财务指标获取失败: {e}")
        
        # 3. 获取同行业股票进行对比
        try:
            # 获取行业成分股
            if industry != '未知':
                try:
                    industry_stocks = ak.stock_board_industry_cons_em(symbol=industry)
                    
                    if industry_stocks is not None and not industry_stocks.empty:
                        # 取行业龙头对比（市值前5）
                        top_stocks = industry_stocks.head(5)
                        
                        report_lines.extend([
                            "",
                            "## 同行业龙头对比",
                            "",
                            "| 股票代码 | 股票名称 | 最新价 | 涨跌幅 | 市值(亿) |",
                            "|---------|---------|-------|-------|---------|"
                        ])
                        
                        for _, row in top_stocks.iterrows():
                            code = row.get('代码', '')
                            name = row.get('名称', '')
                            price = row.get('最新价', 0)
                            change = row.get('涨跌幅', 0)
                            mv = row.get('总市值', 0)
                            report_lines.append(
                                f"| {code} | {name} | {price} | {change}% | {mv/100000000:.2f} |"
                            )
                        
                except Exception as e:
                    logger.warning(f"获取行业成分股失败: {e}")
                    
        except Exception as e:
            report_lines.append(f"同行业对比获取失败: {e}")
        
        # 4. 分析解读
        report_lines.extend([
            "",
            "## 分析建议",
            "",
            "1. **估值比较**: 与行业平均PE/PB对比，判断估值高低",
            "2. **成长性比较**: 与行业龙头对比营收和利润增速",
            "3. **盈利能力比较**: 对比ROE、毛利率等指标",
            "4. **财务健康比较**: 对比资产负债率、流动比率等",
            "",
            f"*注：当前股票所属行业为「{industry}」，建议重点关注行业龙头动态*"
        ])
        
        return "\n".join(report_lines)
        
    except Exception as e:
        logger.error(f"❌ 行业对比工具执行失败: {e}")
        return f"行业对比数据获取失败: {str(e)}"


# 导出工具列表
INSTITUTIONAL_TOOLS = [
    get_north_money_flow,
    get_stock_north_holding,
    get_stock_fund_holding,
    get_stock_lhb_analysis,
    get_industry_comparison,
]
