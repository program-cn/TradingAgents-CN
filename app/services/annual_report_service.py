"""
年报财务分析服务
支持 PDF 财报深度解析 + 五维度财务指标分析 + 风险预警
"""

import re
import json
import logging
import urllib.request
import urllib.error
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime

logger = logging.getLogger(__name__)


# ==================== 数据结构 ====================

@dataclass
class RiskSignal:
    """风险信号"""
    name: str
    value: str
    level: str  # 低/中/高
    description: str


@dataclass
class FinancialData:
    """财务报表数据 - 完整五维度指标"""
    # ==================== 资产负债表 ====================
    total_assets: Optional[float] = None  # 总资产
    total_liabilities: Optional[float] = None  # 总负债
    total_equity: Optional[float] = None  # 股东权益（净资产）
    current_assets: Optional[float] = None  # 流动资产
    current_liabilities: Optional[float] = None  # 流动负债
    non_current_assets: Optional[float] = None  # 非流动资产
    non_current_liabilities: Optional[float] = None  # 非流动负债
    cash: Optional[float] = None  # 货币资金
    trading_assets: Optional[float] = None  # 交易性金融资产
    notes_receivable: Optional[float] = None  # 应收票据
    accounts_receivable: Optional[float] = None  # 应收账款
    prepayments: Optional[float] = None  # 预付款项
    other_receivables: Optional[float] = None  # 其他应收款
    inventory: Optional[float] = None  # 存货
    contract_assets: Optional[float] = None  # 合同资产
    long_term_equity_investment: Optional[float] = None  # 长期股权投资
    fixed_assets: Optional[float] = None  # 固定资产
    construction_in_progress: Optional[float] = None  # 在建工程
    intangible_assets: Optional[float] = None  # 无形资产
    goodwill: Optional[float] = None  # 商誉
    short_term_borrowings: Optional[float] = None  # 短期借款
    notes_payable: Optional[float] = None  # 应付票据
    accounts_payable: Optional[float] = None  # 应付账款
    advance_receipts: Optional[float] = None  # 预收款项
    contract_liabilities: Optional[float] = None  # 合同负债
    employee_benefits_payable: Optional[float] = None  # 应付职工薪酬
    taxes_payable: Optional[float] = None  # 应交税费
    long_term_borrowings: Optional[float] = None  # 长期借款
    bonds_payable: Optional[float] = None  # 应付债券
    retained_earnings: Optional[float] = None  # 未分配利润
    
    # ==================== 利润表 ====================
    revenue: Optional[float] = None  # 营业收入
    operating_cost: Optional[float] = None  # 营业成本
    tax_surcharges: Optional[float] = None  # 税金及附加
    selling_expenses: Optional[float] = None  # 销售费用
    admin_expenses: Optional[float] = None  # 管理费用
    rd_expenses: Optional[float] = None  # 研发费用
    financial_expenses: Optional[float] = None  # 财务费用
    interest_expense: Optional[float] = None  # 利息支出
    interest_income: Optional[float] = None  # 利息收入
    asset_impairment_loss: Optional[float] = None  # 资产减值损失
    credit_impairment_loss: Optional[float] = None  # 信用减值损失
    other_income: Optional[float] = None  # 其他收益
    investment_income: Optional[float] = None  # 投资收益
    fair_value_change: Optional[float] = None  # 公允价值变动收益
    operating_profit: Optional[float] = None  # 营业利润
    non_operating_income: Optional[float] = None  # 营业外收入
    non_operating_expense: Optional[float] = None  # 营业外支出
    profit_before_tax: Optional[float] = None  # 利润总额
    income_tax_expense: Optional[float] = None  # 所得税费用
    net_profit: Optional[float] = None  # 净利润
    net_profit_attr: Optional[float] = None  # 归属母公司净利润
    minority_interest: Optional[float] = None  # 少数股东损益
    gross_profit: Optional[float] = None  # 毛利润（计算值）
    
    # ==================== 现金流量表 ====================
    operating_cash_flow: Optional[float] = None  # 经营活动现金流净额
    cash_received_sales: Optional[float] = None  # 销售商品收到的现金
    tax_refund: Optional[float] = None  # 收到的税费返还
    cash_paid_goods: Optional[float] = None  # 购买商品支付的现金
    cash_paid_employees: Optional[float] = None  # 支付给职工的现金
    taxes_paid: Optional[float] = None  # 支付的各项税费
    investing_cash_flow: Optional[float] = None  # 投资活动现金流净额
    cash_paid_capex: Optional[float] = None  # 购建固定资产支付的现金
    financing_cash_flow: Optional[float] = None  # 筹资活动现金流净额
    cash_from_borrowing: Optional[float] = None  # 取得借款收到的现金
    cash_paid_debt: Optional[float] = None  # 偿还债务支付的现金
    cash_paid_dividends: Optional[float] = None  # 分配股利支付的现金
    free_cash_flow: Optional[float] = None  # 自由现金流（计算值）
    
    # ==================== 每股指标 ====================
    eps: Optional[float] = None  # 基本每股收益(元)
    diluted_eps: Optional[float] = None  # 稀释每股收益(元)
    bvps: Optional[float] = None  # 每股净资产(元)
    cfps: Optional[float] = None  # 每股经营现金流(元)
    cfps_operating: Optional[float] = None  # 每股经营活动现金流(元)
    retained_eps: Optional[float] = None  # 每股未分配利润(元)
    capital_reserve_ps: Optional[float] = None  # 每股资本公积(元)
    total_shares: Optional[float] = None  # 总股本(万股)
    
    # ==================== 盈利能力指标 ====================
    roe: Optional[float] = None  # 净资产收益率ROE(%)
    roe_diluted: Optional[float] = None  # 稀释净资产收益率(%)
    roa: Optional[float] = None  # 总资产收益率ROA(%)
    gross_margin: Optional[float] = None  # 销售毛利率(%)
    net_margin: Optional[float] = None  # 销售净利率(%)
    operating_margin: Optional[float] = None  # 营业利润率(%)
    ebit_margin: Optional[float] = None  # EBIT利润率(%)
    roic: Optional[float] = None  # 投入资本回报率(%)
    
    # ==================== 偿债能力指标 ====================
    debt_ratio: Optional[float] = None  # 资产负债率(%)
    equity_multiplier: Optional[float] = None  # 权益乘数
    current_ratio: Optional[float] = None  # 流动比率
    quick_ratio: Optional[float] = None  # 速动比率
    cash_ratio: Optional[float] = None  # 现金比率
    interest_coverage: Optional[float] = None  # 利息保障倍数
    times_interest_earned: Optional[float] = None  # 已获利息倍数
    debt_to_equity: Optional[float] = None  # 产权比率
    
    # ==================== 成长能力指标 ====================
    revenue_growth: Optional[float] = None  # 营业收入增长率(%)
    net_profit_growth: Optional[float] = None  # 净利润增长率(%)
    operating_profit_growth: Optional[float] = None  # 营业利润增长率(%)
    total_assets_growth: Optional[float] = None  # 总资产增长率(%)
    net_assets_growth: Optional[float] = None  # 净资产增长率(%)
    eps_growth: Optional[float] = None  # 每股收益增长率(%)
    
    # ==================== 运营能力指标 ====================
    inventory_turnover: Optional[float] = None  # 存货周转率(次)
    inventory_turnover_days: Optional[float] = None  # 存货周转天数(天)
    accounts_receivable_turnover: Optional[float] = None  # 应收账款周转率(次)
    accounts_receivable_turnover_days: Optional[float] = None  # 应收账款周转天数(天)
    total_assets_turnover: Optional[float] = None  # 总资产周转率(次)
    fixed_assets_turnover: Optional[float] = None  # 固定资产周转率(次)
    accounts_payable_turnover: Optional[float] = None  # 应付账款周转率(次)
    accounts_payable_turnover_days: Optional[float] = None  # 应付账款周转天数(天)
    operating_cycle: Optional[float] = None  # 营业周期(天)
    
    # ==================== 现金流质量指标 ====================
    net_cash_ratio: Optional[float] = None  # 净现比(经营现金流/净利润)
    cash_to_sales: Optional[float] = None  # 销售现金比率(销售商品收到现金/营业收入)
    cash_to_operating_profit: Optional[float] = None  # 经营现金流/营业利润


@dataclass
class AnalysisResult:
    """分析结果"""
    symbol: str = ""
    name: str = ""
    periods: List[str] = field(default_factory=list)
    metrics: Dict[str, Dict[str, List[Optional[str]]]] = field(default_factory=dict)
    financial_data: Dict[str, Any] = field(default_factory=dict)
    risk_signals: List[Dict] = field(default_factory=list)
    health_score: int = 0
    report: str = ""
    source: str = ""
    analysis_time: str = ""
    pdf_extracted: bool = False


# ==================== PDF 解析 ====================

def extract_text_from_pdf(pdf_path: str) -> str:
    """从 PDF 提取文本内容"""
    try:
        import fitz  # PyMuPDF
        text = ""
        with fitz.open(pdf_path) as doc:
            for page in doc:
                text += page.get_text()
        return text
    except ImportError:
        logger.warning("PyMuPDF 未安装，尝试使用 pdfplumber")
        try:
            import pdfplumber
            text = ""
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            return text
        except ImportError:
            logger.error("PyMuPDF 和 pdfplumber 都未安装")
            return ""
    except Exception as e:
        logger.error(f"PDF 文本提取失败: {e}")
        return ""


def parse_chinese_number(text: str) -> Optional[float]:
    """解析中文数字格式"""
    if not text:
        return None
    
    text = text.strip()
    
    # 处理中文单位
    multipliers = {
        '万亿': 1e12,
        '亿': 1e8,
        '万': 1e4,
        '千': 1e3,
        '百': 1e2,
    }
    
    for unit, mult in multipliers.items():
        if unit in text:
            num_str = text.replace(unit, '').strip()
            try:
                return float(num_str) * mult
            except:
                continue
    
    # 尝试直接解析
    try:
        # 移除逗号和空格
        text = text.replace(',', '').replace(' ', '').replace('元', '')
        return float(text)
    except:
        return None


def extract_number_near_keyword(text: str, keyword: str, max_distance: int = 100) -> Optional[float]:
    """提取关键词附近的数字"""
    # 多种匹配模式
    patterns = [
        rf'{keyword}[：:\s]*([0-9,，.．]+)\s*(万亿|亿|万|元)?',
        rf'{keyword}.*?([0-9,，.．]+)\s*(万亿|亿|万|元)?',
        rf'{keyword}[：:\s]*([一二三四五六七八九十百千万亿]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            num_str = match.group(1).replace('，', ',').replace('．', '.')
            unit = match.group(2) if len(match.groups()) > 1 else ''
            
            # 处理中文数字
            if any(c in num_str for c in '一二三四五六七八九十百千万亿'):
                return parse_chinese_number(num_str + unit)
            
            try:
                num = float(num_str.replace(',', ''))
                if unit:
                    multipliers = {'万亿': 1e12, '亿': 1e8, '万': 1e4}
                    for u, m in multipliers.items():
                        if u in unit:
                            num *= m
                            break
                return num
            except:
                continue
    
    return None


def extract_table_data(text: str) -> Dict[str, str]:
    """从文本中提取表格数据 - 完整五维度财务指标"""
    data = {}
    
    # ==================== 资产负债表指标 ====================
    balance_sheet_keywords = [
        # 资产
        ('total_assets', ['资产总计', '总资产', '资产合计']),
        ('current_assets', ['流动资产合计', '流动资产总计']),
        ('non_current_assets', ['非流动资产合计', '非流动资产总计']),
        ('cash', ['货币资金', '现金及现金等价物余额']),
        ('trading_assets', ['交易性金融资产']),
        ('notes_receivable', ['应收票据']),
        ('accounts_receivable', ['应收账款']),
        ('prepayments', ['预付款项', '预付账款']),
        ('other_receivables', ['其他应收款']),
        ('inventory', ['存货']),
        ('contract_assets', ['合同资产']),
        ('long_term_equity_investment', ['长期股权投资']),
        ('fixed_assets', ['固定资产', '固定资产净额', '固定资产原价']),
        ('construction_in_progress', ['在建工程']),
        ('intangible_assets', ['无形资产']),
        ('goodwill', ['商誉']),
        
        # 负债
        ('total_liabilities', ['负债合计', '负债总计', '总负债']),
        ('current_liabilities', ['流动负债合计', '流动负债总计']),
        ('non_current_liabilities', ['非流动负债合计', '非流动负债总计']),
        ('short_term_borrowings', ['短期借款']),
        ('notes_payable', ['应付票据']),
        ('accounts_payable', ['应付账款']),
        ('advance_receipts', ['预收款项', '预收账款']),
        ('contract_liabilities', ['合同负债']),
        ('employee_benefits_payable', ['应付职工薪酬']),
        ('taxes_payable', ['应交税费']),
        ('long_term_borrowings', ['长期借款']),
        ('bonds_payable', ['应付债券']),
        
        # 所有者权益
        ('total_equity', ['股东权益合计', '所有者权益合计', '净资产', '归属于母公司股东权益合计']),
        ('retained_earnings', ['未分配利润']),
    ]
    
    # ==================== 利润表指标 ====================
    income_statement_keywords = [
        ('revenue', ['营业收入', '主营业务收入']),
        ('operating_cost', ['营业成本', '主营业务成本']),
        ('tax_surcharges', ['税金及附加']),
        ('selling_expenses', ['销售费用']),
        ('admin_expenses', ['管理费用']),
        ('rd_expenses', ['研发费用']),
        ('financial_expenses', ['财务费用']),
        ('interest_expense', ['利息支出']),
        ('asset_impairment_loss', ['资产减值损失']),
        ('credit_impairment_loss', ['信用减值损失']),
        ('other_income', ['其他收益']),
        ('investment_income', ['投资收益']),
        ('fair_value_change', ['公允价值变动收益']),
        ('operating_profit', ['营业利润']),
        ('non_operating_income', ['营业外收入']),
        ('non_operating_expense', ['营业外支出']),
        ('profit_before_tax', ['利润总额']),
        ('income_tax_expense', ['所得税费用']),
        ('net_profit', ['净利润', '净收益']),
        ('net_profit_attr', ['归属于母公司股东的净利润', '归属母公司股东的净利润', '归属净利润']),
        ('minority_interest', ['少数股东损益']),
    ]
    
    # ==================== 现金流量表指标 ====================
    cashflow_keywords = [
        ('operating_cash_flow', ['经营活动产生的现金流量净额', '经营活动现金流净额', '经营现金流净额']),
        ('cash_received_sales', ['销售商品、提供劳务收到的现金']),
        ('tax_refund', ['收到的税费返还']),
        ('cash_paid_goods', ['购买商品、接受劳务支付的现金']),
        ('cash_paid_employees', ['支付给职工以及为职工支付的现金']),
        ('taxes_paid', ['支付的各项税费']),
        ('investing_cash_flow', ['投资活动产生的现金流量净额', '投资活动现金流净额']),
        ('cash_paid_capex', ['购建固定资产、无形资产和其他长期资产支付的现金']),
        ('financing_cash_flow', ['筹资活动产生的现金流量净额', '筹资活动现金流净额']),
        ('cash_from_borrowing', ['取得借款收到的现金']),
        ('cash_paid_debt', ['偿还债务支付的现金']),
        ('cash_paid_dividends', ['分配股利、利润或偿付利息支付的现金']),
    ]
    
    # ==================== 每股指标 ====================
    per_share_keywords = [
        ('eps', ['基本每股收益', '每股收益']),
        ('diluted_eps', ['稀释每股收益']),
        ('bvps', ['每股净资产', '归属于母公司股东的每股净资产']),
        ('cfps', ['每股经营活动产生的现金流量净额', '每股经营现金流']),
        ('retained_eps', ['每股未分配利润']),
        ('capital_reserve_ps', ['每股资本公积']),
        ('total_shares', ['股本', '总股本']),
    ]
    
    # ==================== 盈利能力指标 ====================
    profitability_keywords = [
        ('roe', ['净资产收益率', '加权平均净资产收益率', 'ROE']),
        ('roe_diluted', ['稀释净资产收益率']),
        ('roa', ['总资产收益率', '总资产净利率', 'ROA']),
        ('gross_margin', ['销售毛利率', '毛利率']),
        ('net_margin', ['销售净利率', '净利率']),
        ('operating_margin', ['营业利润率']),
        ('roic', ['投入资本回报率']),
    ]
    
    # ==================== 偿债能力指标 ====================
    solvency_keywords = [
        ('debt_ratio', ['资产负债率']),
        ('current_ratio', ['流动比率']),
        ('quick_ratio', ['速动比率']),
        ('cash_ratio', ['现金比率']),
        ('interest_coverage', ['利息保障倍数', '已获利息倍数']),
        ('debt_to_equity', ['产权比率']),
    ]
    
    # ==================== 成长能力指标 ====================
    growth_keywords = [
        ('revenue_growth', ['营业收入增长率', '营收增长率']),
        ('net_profit_growth', ['净利润增长率']),
        ('operating_profit_growth', ['营业利润增长率']),
        ('total_assets_growth', ['总资产增长率']),
        ('net_assets_growth', ['净资产增长率']),
        ('eps_growth', ['每股收益增长率']),
    ]
    
    # ==================== 运营能力指标 ====================
    operation_keywords = [
        ('inventory_turnover', ['存货周转率']),
        ('inventory_turnover_days', ['存货周转天数']),
        ('accounts_receivable_turnover', ['应收账款周转率']),
        ('accounts_receivable_turnover_days', ['应收账款周转天数']),
        ('total_assets_turnover', ['总资产周转率']),
        ('fixed_assets_turnover', ['固定资产周转率']),
        ('accounts_payable_turnover', ['应付账款周转率']),
        ('accounts_payable_turnover_days', ['应付账款周转天数']),
    ]
    
    # 合并所有关键词
    all_keywords = (
        balance_sheet_keywords + 
        income_statement_keywords + 
        cashflow_keywords + 
        per_share_keywords +
        profitability_keywords +
        solvency_keywords +
        growth_keywords +
        operation_keywords
    )
    
    for key, kw_list in all_keywords:
        for kw in kw_list:
            value = extract_number_near_keyword(text, kw)
            if value is not None:
                data[key] = value
                break
    
    return data


def parse_pdf_financial_data(pdf_path: str) -> Tuple[FinancialData, bool]:
    """解析 PDF 财务数据 - 完整五维度指标计算"""
    text = extract_text_from_pdf(pdf_path)
    
    if not text:
        return FinancialData(), False
    
    logger.info(f"PDF 文本长度: {len(text)} 字符")
    
    # 提取表格数据
    extracted = extract_table_data(text)
    
    logger.info(f"从 PDF 提取到 {len(extracted)} 个指标: {list(extracted.keys())}")
    
    # 构建 FinancialData
    data = FinancialData()
    for key, value in extracted.items():
        if hasattr(data, key):
            setattr(data, key, value)
    
    # ==================== 计算派生指标 ====================
    
    # === 毛利润 ===
    if data.revenue and data.operating_cost:
        data.gross_profit = data.revenue - data.operating_cost
    
    # === 自由现金流 ===
    if data.operating_cash_flow:
        capex = data.cash_paid_capex if data.cash_paid_capex else abs(data.operating_cash_flow) * 0.2
        data.free_cash_flow = data.operating_cash_flow - abs(capex)
    
    # ==================== 一、每股指标计算 ====================
    # 如果没有从PDF提取到每股指标，尝试计算
    
    # 每股收益 EPS（如果未提取）
    if data.eps is None and data.net_profit_attr and data.total_shares:
        data.eps = data.net_profit_attr / (data.total_shares * 10000)  # 总股本单位是万股
    
    # 每股净资产 BVPS
    if data.bvps is None and data.total_equity and data.total_shares:
        data.bvps = data.total_equity / (data.total_shares * 10000)
    
    # 每股经营现金流 CFPS
    if data.cfps is None and data.operating_cash_flow and data.total_shares:
        data.cfps = data.operating_cash_flow / (data.total_shares * 10000)
    
    # ==================== 二、盈利能力指标计算 ====================
    
    # 毛利率
    if data.gross_margin is None and data.gross_profit and data.revenue:
        data.gross_margin = (data.gross_profit / data.revenue) * 100
    
    # 净利率
    if data.net_margin is None and data.net_profit and data.revenue:
        data.net_margin = (data.net_profit / data.revenue) * 100
    
    # 营业利润率
    if data.operating_margin is None and data.operating_profit and data.revenue:
        data.operating_margin = (data.operating_profit / data.revenue) * 100
    
    # ROE 净资产收益率
    if data.roe is None and data.net_profit and data.total_equity:
        data.roe = (data.net_profit / data.total_equity) * 100
    
    # ROA 总资产收益率
    if data.roa is None and data.net_profit and data.total_assets:
        data.roa = (data.net_profit / data.total_assets) * 100
    
    # 投入资本回报率 ROIC（简化计算）
    if data.roic is None and data.net_profit and data.total_equity and data.total_liabilities:
        invested_capital = data.total_equity + (data.total_liabilities - (data.accounts_payable or 0))
        if invested_capital > 0:
            data.roic = (data.operating_profit or data.net_profit) / invested_capital * 100
    
    # ==================== 三、偿债能力指标计算 ====================
    
    # 资产负债率
    if data.debt_ratio is None and data.total_liabilities and data.total_assets:
        data.debt_ratio = (data.total_liabilities / data.total_assets) * 100
    
    # 流动比率
    if data.current_ratio is None and data.current_assets and data.current_liabilities:
        data.current_ratio = data.current_assets / data.current_liabilities
    
    # 速动比率 = (流动资产 - 存货) / 流动负债
    if data.quick_ratio is None and data.current_assets and data.current_liabilities:
        quick_assets = data.current_assets - (data.inventory or 0)
        data.quick_ratio = quick_assets / data.current_liabilities
    
    # 现金比率 = (货币资金 + 交易性金融资产) / 流动负债
    if data.cash_ratio is None and data.current_liabilities:
        cash_equivalents = (data.cash or 0) + (data.trading_assets or 0)
        data.cash_ratio = cash_equivalents / data.current_liabilities
    
    # 利息保障倍数 = (营业利润 + 利息费用) / 利息费用
    if data.interest_coverage is None and data.interest_expense and data.interest_expense > 0:
        ebit = (data.operating_profit or data.net_profit or 0) + data.interest_expense
        data.interest_coverage = ebit / data.interest_expense
        data.times_interest_earned = data.interest_coverage
    
    # 产权比率 = 总负债 / 股东权益
    if data.debt_to_equity is None and data.total_liabilities and data.total_equity:
        data.debt_to_equity = data.total_liabilities / data.total_equity
    
    # 权益乘数 = 总资产 / 股东权益
    if data.equity_multiplier is None and data.total_assets and data.total_equity:
        data.equity_multiplier = data.total_assets / data.total_equity
    
    # ==================== 四、运营能力指标计算 ====================
    
    # 存货周转率 = 营业成本 / 平均存货（简化用期末存货）
    if data.inventory_turnover is None and data.operating_cost and data.inventory and data.inventory > 0:
        data.inventory_turnover = data.operating_cost / data.inventory
        data.inventory_turnover_days = 365 / data.inventory_turnover
    
    # 应收账款周转率 = 营业收入 / 平均应收账款
    if data.accounts_receivable_turnover is None and data.revenue:
        ar = data.accounts_receivable or 0
        if ar > 0:
            data.accounts_receivable_turnover = data.revenue / ar
            data.accounts_receivable_turnover_days = 365 / data.accounts_receivable_turnover
    
    # 总资产周转率 = 营业收入 / 平均总资产
    if data.total_assets_turnover is None and data.revenue and data.total_assets and data.total_assets > 0:
        data.total_assets_turnover = data.revenue / data.total_assets
    
    # 固定资产周转率 = 营业收入 / 固定资产
    if data.fixed_assets_turnover is None and data.revenue and data.fixed_assets and data.fixed_assets > 0:
        data.fixed_assets_turnover = data.revenue / data.fixed_assets
    
    # 应付账款周转率 = 营业成本 / 平均应付账款
    if data.accounts_payable_turnover is None and data.operating_cost and data.accounts_payable and data.accounts_payable > 0:
        data.accounts_payable_turnover = data.operating_cost / data.accounts_payable
        data.accounts_payable_turnover_days = 365 / data.accounts_payable_turnover
    
    # 营业周期 = 存货周转天数 + 应收账款周转天数
    if data.operating_cycle is None:
        days = (data.inventory_turnover_days or 0) + (data.accounts_receivable_turnover_days or 0)
        if days > 0:
            data.operating_cycle = days
    
    # ==================== 五、现金流质量指标计算 ====================
    
    # 净现比 = 经营现金流 / 净利润
    if data.net_cash_ratio is None and data.operating_cash_flow and data.net_profit and data.net_profit != 0:
        data.net_cash_ratio = data.operating_cash_flow / data.net_profit
    
    # 销售现金比率 = 销售商品收到现金 / 营业收入
    if data.cash_to_sales is None and data.cash_received_sales and data.revenue and data.revenue != 0:
        data.cash_to_sales = data.cash_received_sales / data.revenue
    
    # 经营现金流 / 营业利润
    if data.cash_to_operating_profit is None and data.operating_cash_flow and data.operating_profit and data.operating_profit != 0:
        data.cash_to_operating_profit = data.operating_cash_flow / data.operating_profit
    
    return data, len(extracted) > 5


# ==================== 网络数据获取 ====================

def fetch_financial_data(symbol: str) -> str:
    """从新浪财经获取财务数据HTML"""
    url = f"https://vip.stock.finance.sina.com.cn/corp/go.php/vFD_FinancialGuideLine/stockid/{symbol}/displaytype/4.phtml"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            return response.read().decode('gbk', errors='ignore')
    except urllib.error.URLError as e:
        raise RuntimeError(f"网络请求失败: {e}")


def fetch_stock_info(symbol: str) -> Tuple[str, float, float]:
    """获取股票名称和实时价格"""
    url = f"https://push2.eastmoney.com/api/qt/stock/get?secid=0.{symbol}&fields=f58,f43,f44"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read().decode('utf-8'))
            if 'data' in result and result['data']:
                d = result['data']
                name = d.get('f58', symbol)
                price = d.get('f43', 0) / 100 if d.get('f43') else 0
                change = d.get('f44', 0) / 100 if d.get('f44') else 0
                return name, price, change
    except Exception as e:
        logger.warning(f"获取股票信息失败: {e}")
    return symbol, 0, 0


def parse_table_rows(html: str) -> List[tuple]:
    """解析HTML表格数据"""
    pattern = r'<tr><td[^>]*>(.*?)</td><td>(.*?)</td><td>(.*?)</td><td>(.*?)</td><td>(.*?)</td></tr>'
    return re.findall(pattern, html, re.DOTALL)


def extract_metric_name(cell: str) -> str:
    """提取指标名称，去除HTML标签"""
    return re.sub(r'<[^>]+>', '', cell).strip()


def parse_financial_data(html: str, periods: int = 4) -> Dict[str, Dict[str, List[Optional[str]]]]:
    """解析财务数据"""
    rows = parse_table_rows(html)
    
    # 指标分类定义
    metric_categories = {
        '每股指标': ['每股收益', '每股净资产', '每股经营', '每股未分配', '每股资本'],
        '盈利能力': ['净资产收益率', '毛利率', '净利率', '营业利润率', '总资产报酬率', 'ROE', 'ROA', '总资产净利率'],
        '偿债能力': ['资产负债率', '流动比率', '速动比率', '利息保障', '有息负债'],
        '运营能力': ['周转率', '周转天数'],
        '成长能力': ['增长率', '增长比']
    }
    
    metrics = {cat: {} for cat in metric_categories.keys()}
    periods_list = []
    
    for row in rows:
        name = extract_metric_name(row[0])
        values = [row[1], row[2], row[3], row[4]]
        values = [v if v != '--' else None for v in values]
        
        # 提取报告期
        if '报告日期' in name:
            periods_list = [v for v in values[:periods] if v]
            continue
        
        # 分类指标
        for category, keywords in metric_categories.items():
            if any(kw in name for kw in keywords):
                clean_name = name.replace(category, '').strip()
                if clean_name not in metrics[category]:
                    metrics[category][clean_name] = values[:periods]
                break
    
    return metrics, periods_list


# ==================== 风险分析 ====================

def safe_float(value) -> Optional[float]:
    """安全转换为浮点数"""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.replace(',', '').replace('%', ''))
        except:
            return None
    return None


def analyze_financial_data(data: FinancialData, metrics: Dict) -> List[RiskSignal]:
    """分析财务数据，生成风险信号 - 完整五维度分析"""
    signals = []
    
    # ==================== 一、每股指标分析 ====================
    
    # 每股收益 EPS 分析
    eps_val = safe_float(data.eps)
    if eps_val is None:
        eps_val = safe_float(metrics.get('每股指标', {}).get('基本每股收益(元)', [None])[0])
    
    if eps_val is not None:
        if eps_val >= 1.0:
            signals.append(RiskSignal('每股收益EPS', f'{eps_val:.2f}元', '低',
                f'EPS {eps_val:.2f}元，每股盈利能力强'))
        elif eps_val >= 0.3:
            signals.append(RiskSignal('每股收益EPS', f'{eps_val:.2f}元', '中',
                f'EPS {eps_val:.2f}元，盈利能力一般'))
        elif eps_val > 0:
            signals.append(RiskSignal('每股收益EPS', f'{eps_val:.2f}元', '高',
                f'EPS {eps_val:.2f}元，每股盈利较弱'))
        else:
            signals.append(RiskSignal('每股收益EPS', f'{eps_val:.2f}元', '高',
                f'EPS {eps_val:.2f}元，每股亏损'))
    
    # 每股净资产 BVPS 分析
    bvps_val = safe_float(data.bvps)
    if bvps_val is None:
        bvps_val = safe_float(metrics.get('每股指标', {}).get('每股净资产(元)', [None])[0])
    
    if bvps_val is not None:
        if bvps_val >= 10:
            signals.append(RiskSignal('每股净资产', f'{bvps_val:.2f}元', '低',
                f'BPS {bvps_val:.2f}元，每股净资产雄厚'))
        elif bvps_val >= 5:
            signals.append(RiskSignal('每股净资产', f'{bvps_val:.2f}元', '中',
                f'BPS {bvps_val:.2f}元，每股净资产一般'))
        else:
            signals.append(RiskSignal('每股净资产', f'{bvps_val:.2f}元', '高',
                f'BPS {bvps_val:.2f}元，每股净资产较低'))
    
    # ==================== 二、盈利能力分析 ====================
    
    # ROE 分析（核心指标）
    roe_val = safe_float(data.roe)
    if roe_val is None:
        roe_val = safe_float(metrics.get('盈利能力', {}).get('净资产收益率(%)', [None])[0])
    
    if roe_val is not None:
        if roe_val >= 20:
            signals.append(RiskSignal('ROE净资产收益率', f'{roe_val:.2f}%', '低',
                f'ROE {roe_val:.2f}% >= 20%，盈利能力优秀，巴菲特选股标准'))
        elif roe_val >= 15:
            signals.append(RiskSignal('ROE净资产收益率', f'{roe_val:.2f}%', '低',
                f'ROE {roe_val:.2f}% >= 15%，盈利能力良好'))
        elif roe_val >= 8:
            signals.append(RiskSignal('ROE净资产收益率', f'{roe_val:.2f}%', '中',
                f'ROE {roe_val:.2f}%，盈利能力一般，有提升空间'))
        else:
            signals.append(RiskSignal('ROE净资产收益率', f'{roe_val:.2f}%', '高',
                f'ROE {roe_val:.2f}% < 8%，盈利能力弱，需重点关注'))
    
    # ROA 分析
    roa_val = safe_float(data.roa)
    if roa_val is None:
        roa_val = safe_float(metrics.get('盈利能力', {}).get('总资产净利率(%)', [None])[0])
    
    if roa_val is not None:
        if roa_val >= 10:
            signals.append(RiskSignal('ROA总资产收益率', f'{roa_val:.2f}%', '低',
                f'ROA {roa_val:.2f}% >= 10%，资产运营效率优秀'))
        elif roa_val >= 5:
            signals.append(RiskSignal('ROA总资产收益率', f'{roa_val:.2f}%', '中',
                f'ROA {roa_val:.2f}%，资产运营效率良好'))
        elif roa_val >= 2:
            signals.append(RiskSignal('ROA总资产收益率', f'{roa_val:.2f}%', '中',
                f'ROA {roa_val:.2f}%，资产运营效率一般'))
        else:
            signals.append(RiskSignal('ROA总资产收益率', f'{roa_val:.2f}%', '高',
                f'ROA {roa_val:.2f}% < 2%，资产运营效率低'))
    
    # 毛利率分析
    gm_val = safe_float(data.gross_margin)
    if gm_val is None:
        gm_val = safe_float(metrics.get('盈利能力', {}).get('销售毛利率(%)', [None])[0])
    
    if gm_val is not None:
        if gm_val >= 50:
            signals.append(RiskSignal('销售毛利率', f'{gm_val:.2f}%', '低',
                f'毛利率 {gm_val:.2f}% >= 50%，产品核心竞争力强'))
        elif gm_val >= 30:
            signals.append(RiskSignal('销售毛利率', f'{gm_val:.2f}%', '低',
                f'毛利率 {gm_val:.2f}% >= 30%，产品竞争力良好'))
        elif gm_val >= 15:
            signals.append(RiskSignal('销售毛利率', f'{gm_val:.2f}%', '中',
                f'毛利率 {gm_val:.2f}%，行业竞争一般'))
        else:
            signals.append(RiskSignal('销售毛利率', f'{gm_val:.2f}%', '高',
                f'毛利率 {gm_val:.2f}% < 15%，产品竞争力弱或成本控制差'))
    
    # 净利率分析
    nm_val = safe_float(data.net_margin)
    if nm_val is None:
        nm_val = safe_float(metrics.get('盈利能力', {}).get('销售净利率(%)', [None])[0])
    
    if nm_val is not None:
        if nm_val >= 15:
            signals.append(RiskSignal('销售净利率', f'{nm_val:.2f}%', '低',
                f'净利率 {nm_val:.2f}% >= 15%，盈利质量优秀'))
        elif nm_val >= 8:
            signals.append(RiskSignal('销售净利率', f'{nm_val:.2f}%', '低',
                f'净利率 {nm_val:.2f}% >= 8%，盈利质量良好'))
        elif nm_val >= 3:
            signals.append(RiskSignal('销售净利率', f'{nm_val:.2f}%', '中',
                f'净利率 {nm_val:.2f}%，盈利质量一般'))
        else:
            signals.append(RiskSignal('销售净利率', f'{nm_val:.2f}%', '高',
                f'净利率 {nm_val:.2f}% < 3%，费用率偏高或主业盈利弱'))
    
    # 营业利润率分析
    opm_val = safe_float(data.operating_margin)
    if opm_val is not None:
        if opm_val >= 15:
            signals.append(RiskSignal('营业利润率', f'{opm_val:.2f}%', '低',
                f'营业利润率 {opm_val:.2f}%，主业盈利能力强'))
        elif opm_val >= 5:
            signals.append(RiskSignal('营业利润率', f'{opm_val:.2f}%', '中',
                f'营业利润率 {opm_val:.2f}%，主业盈利能力一般'))
        else:
            signals.append(RiskSignal('营业利润率', f'{opm_val:.2f}%', '高',
                f'营业利润率 {opm_val:.2f}%，主业盈利能力弱'))
    
    # ==================== 三、偿债能力分析 ====================
    
    # 资产负债率
    debt_val = safe_float(data.debt_ratio)
    if debt_val is None:
        debt_val = safe_float(metrics.get('偿债能力', {}).get('资产负债率(%)', [None])[0])
    
    if debt_val is not None:
        if debt_val <= 40:
            signals.append(RiskSignal('资产负债率', f'{debt_val:.2f}%', '低',
                f'资产负债率 {debt_val:.2f}% <= 40%，财务结构非常稳健'))
        elif debt_val <= 60:
            signals.append(RiskSignal('资产负债率', f'{debt_val:.2f}%', '低',
                f'资产负债率 {debt_val:.2f}%，财务结构稳健'))
        elif debt_val <= 70:
            signals.append(RiskSignal('资产负债率', f'{debt_val:.2f}%', '中',
                f'资产负债率 {debt_val:.2f}%，需关注债务压力'))
        else:
            signals.append(RiskSignal('资产负债率', f'{debt_val:.2f}%', '高',
                f'资产负债率 {debt_val:.2f}% > 70%，杠杆风险高'))
    
    # 流动比率
    cr_val = safe_float(data.current_ratio)
    if cr_val is None:
        cr_val = safe_float(metrics.get('偿债能力', {}).get('流动比率', [None])[0])
    
    if cr_val is not None:
        if cr_val >= 2.0:
            signals.append(RiskSignal('流动比率', f'{cr_val:.2f}', '低',
                f'流动比率 {cr_val:.2f} >= 2，短期偿债能力优秀'))
        elif cr_val >= 1.5:
            signals.append(RiskSignal('流动比率', f'{cr_val:.2f}', '低',
                f'流动比率 {cr_val:.2f} >= 1.5，短期偿债能力良好'))
        elif cr_val >= 1.0:
            signals.append(RiskSignal('流动比率', f'{cr_val:.2f}', '中',
                f'流动比率 {cr_val:.2f}，短期偿债能力尚可'))
        else:
            signals.append(RiskSignal('流动比率', f'{cr_val:.2f}', '高',
                f'流动比率 {cr_val:.2f} < 1，短期偿债压力大'))
    
    # 速动比率
    qr_val = safe_float(data.quick_ratio)
    if qr_val is None:
        qr_val = safe_float(metrics.get('偿债能力', {}).get('速动比率', [None])[0])
    
    if qr_val is not None:
        if qr_val >= 1.5:
            signals.append(RiskSignal('速动比率', f'{qr_val:.2f}', '低',
                f'速动比率 {qr_val:.2f} >= 1.5，流动性非常充足'))
        elif qr_val >= 1.0:
            signals.append(RiskSignal('速动比率', f'{qr_val:.2f}', '低',
                f'速动比率 {qr_val:.2f} >= 1，流动性充足'))
        else:
            signals.append(RiskSignal('速动比率', f'{qr_val:.2f}', '高',
                f'速动比率 {qr_val:.2f} < 1，需警惕流动性风险'))
    
    # 利息保障倍数
    ic_val = safe_float(data.interest_coverage)
    if ic_val is None:
        ic_val = safe_float(metrics.get('偿债能力', {}).get('利息保障倍数', [None])[0])
    
    if ic_val is not None:
        if ic_val >= 5:
            signals.append(RiskSignal('利息保障倍数', f'{ic_val:.2f}', '低',
                f'利息保障倍数 {ic_val:.2f} >= 5，偿债能力很强'))
        elif ic_val >= 3:
            signals.append(RiskSignal('利息保障倍数', f'{ic_val:.2f}', '中',
                f'利息保障倍数 {ic_val:.2f}，偿债能力尚可'))
        elif ic_val >= 1:
            signals.append(RiskSignal('利息保障倍数', f'{ic_val:.2f}', '高',
                f'利息保障倍数 {ic_val:.2f}，偿债压力较大'))
        else:
            signals.append(RiskSignal('利息保障倍数', f'{ic_val:.2f}', '高',
                f'利息保障倍数 {ic_val:.2f} < 1，无法覆盖利息支出'))
    
    # ==================== 四、成长能力分析 ====================
    
    # 营业收入增长率
    rg_val = safe_float(data.revenue_growth)
    if rg_val is None:
        rg_val = safe_float(metrics.get('成长能力', {}).get('营业收入增长率(%)', [None])[0])
    
    if rg_val is not None:
        if rg_val >= 30:
            signals.append(RiskSignal('营业收入增长率', f'{rg_val:.2f}%', '低',
                f'营收增长 {rg_val:.2f}% >= 30%，高增长'))
        elif rg_val >= 10:
            signals.append(RiskSignal('营业收入增长率', f'{rg_val:.2f}%', '低',
                f'营收增长 {rg_val:.2f}% >= 10%，稳定增长'))
        elif rg_val >= 0:
            signals.append(RiskSignal('营业收入增长率', f'{rg_val:.2f}%', '中',
                f'营收增长 {rg_val:.2f}%，增长放缓'))
        else:
            signals.append(RiskSignal('营业收入增长率', f'{rg_val:.2f}%', '高',
                f'营收增长 {rg_val:.2f}% < 0，主营业务收缩'))
    
    # 净利润增长率
    pg_val = safe_float(data.net_profit_growth)
    if pg_val is None:
        pg_val = safe_float(metrics.get('成长能力', {}).get('净利润增长率(%)', [None])[0])
    
    if pg_val is not None:
        if pg_val >= 30:
            signals.append(RiskSignal('净利润增长率', f'{pg_val:.2f}%', '低',
                f'净利润增长 {pg_val:.2f}% >= 30%，业绩高速增长'))
        elif pg_val >= 10:
            signals.append(RiskSignal('净利润增长率', f'{pg_val:.2f}%', '低',
                f'净利润增长 {pg_val:.2f}% >= 10%，稳定增长'))
        elif pg_val >= 0:
            signals.append(RiskSignal('净利润增长率', f'{pg_val:.2f}%', '中',
                f'净利润增长 {pg_val:.2f}%，增长放缓'))
        else:
            signals.append(RiskSignal('净利润增长率', f'{pg_val:.2f}%', '高',
                f'净利润增长 {pg_val:.2f}% < 0，业绩下滑'))
    
    # ==================== 五、运营能力分析 ====================
    
    # 存货周转率
    it_val = safe_float(data.inventory_turnover)
    if it_val is None:
        it_val = safe_float(metrics.get('运营能力', {}).get('存货周转率(次)', [None])[0])
    
    if it_val is not None:
        if it_val >= 6:
            signals.append(RiskSignal('存货周转率', f'{it_val:.2f}次', '低',
                f'存货周转率 {it_val:.2f}次 >= 6，存货管理效率高'))
        elif it_val >= 3:
            signals.append(RiskSignal('存货周转率', f'{it_val:.2f}次', '中',
                f'存货周转率 {it_val:.2f}次，存货管理效率一般'))
        else:
            signals.append(RiskSignal('存货周转率', f'{it_val:.2f}次', '高',
                f'存货周转率 {it_val:.2f}次 < 3，存货积压风险'))
    
    # 应收账款周转率
    ar_val = safe_float(data.accounts_receivable_turnover)
    if ar_val is None:
        ar_val = safe_float(metrics.get('运营能力', {}).get('应收账款周转率(次)', [None])[0])
    
    if ar_val is not None:
        if ar_val >= 10:
            signals.append(RiskSignal('应收账款周转率', f'{ar_val:.2f}次', '低',
                f'应收账款周转率 {ar_val:.2f}次 >= 10，回款能力强'))
        elif ar_val >= 5:
            signals.append(RiskSignal('应收账款周转率', f'{ar_val:.2f}次', '中',
                f'应收账款周转率 {ar_val:.2f}次，回款能力一般'))
        else:
            signals.append(RiskSignal('应收账款周转率', f'{ar_val:.2f}次', '高',
                f'应收账款周转率 {ar_val:.2f}次 < 5，回款风险高'))
    
    # 总资产周转率
    ta_val = safe_float(data.total_assets_turnover)
    if ta_val is None:
        ta_val = safe_float(metrics.get('运营能力', {}).get('总资产周转率(次)', [None])[0])
    
    if ta_val is not None:
        if ta_val >= 1.0:
            signals.append(RiskSignal('总资产周转率', f'{ta_val:.2f}次', '低',
                f'总资产周转率 {ta_val:.2f}次 >= 1，资产运营效率高'))
        elif ta_val >= 0.5:
            signals.append(RiskSignal('总资产周转率', f'{ta_val:.2f}次', '中',
                f'总资产周转率 {ta_val:.2f}次，资产运营效率一般'))
        else:
            signals.append(RiskSignal('总资产周转率', f'{ta_val:.2f}次', '高',
                f'总资产周转率 {ta_val:.2f}次 < 0.5，资产运营效率低'))
    
    # 营业周期
    oc_val = safe_float(data.operating_cycle)
    if oc_val is None:
        itd = safe_float(data.inventory_turnover_days)
        ard = safe_float(data.accounts_receivable_turnover_days)
        if itd and ard:
            oc_val = itd + ard
    
    if oc_val is not None:
        if oc_val <= 60:
            signals.append(RiskSignal('营业周期', f'{oc_val:.0f}天', '低',
                f'营业周期 {oc_val:.0f}天 <= 60天，资金周转快'))
        elif oc_val <= 120:
            signals.append(RiskSignal('营业周期', f'{oc_val:.0f}天', '中',
                f'营业周期 {oc_val:.0f}天，资金周转一般'))
        else:
            signals.append(RiskSignal('营业周期', f'{oc_val:.0f}天', '高',
                f'营业周期 {oc_val:.0f}天 > 120天，资金周转慢'))
    
    # ==================== 六、现金流质量分析 ====================
    
    # 净现比分析（核心指标 - 财务造假预警）
    ncr_val = safe_float(data.net_cash_ratio)
    if ncr_val is None:
        cfps_val = safe_float(data.cfps)
        eps_val = safe_float(data.eps)
        if eps_val is None:
            eps_val = safe_float(metrics.get('每股指标', {}).get('基本每股收益(元)', [None])[0])
        if cfps_val is None:
            cfps_val = safe_float(metrics.get('每股指标', {}).get('每股经营现金流(元)', [None])[0])
        if eps_val and cfps_val and eps_val > 0:
            ncr_val = cfps_val / eps_val
    
    if ncr_val is not None:
        if ncr_val >= 1.2:
            signals.append(RiskSignal('净现比', f'{ncr_val:.2f}', '低',
                f'净现比 {ncr_val:.2f} >= 1.2，利润有充足现金支撑，质量高'))
        elif ncr_val >= 1.0:
            signals.append(RiskSignal('净现比', f'{ncr_val:.2f}', '低',
                f'净现比 {ncr_val:.2f} >= 1，利润有现金支撑'))
        elif ncr_val >= 0.7:
            signals.append(RiskSignal('净现比', f'{ncr_val:.2f}', '中',
                f'净现比 {ncr_val:.2f}，利润含金量一般，需关注'))
        else:
            signals.append(RiskSignal('净现比', f'{ncr_val:.2f}', '高',
                f'净现比 {ncr_val:.2f} < 0.7，利润含金量低（马氏定律预警）'))
    
    # 销售现金比率
    cts_val = safe_float(data.cash_to_sales)
    if cts_val is not None:
        if cts_val >= 1.1:
            signals.append(RiskSignal('销售现金比率', f'{cts_val:.2f}', '低',
                f'销售现金比率 {cts_val:.2f} >= 1.1，销售回款好'))
        elif cts_val >= 1.0:
            signals.append(RiskSignal('销售现金比率', f'{cts_val:.2f}', '中',
                f'销售现金比率 {cts_val:.2f}，销售回款正常'))
        else:
            signals.append(RiskSignal('销售现金比率', f'{cts_val:.2f}', '高',
                f'销售现金比率 {cts_val:.2f} < 1，应收款占比高'))
    
    return signals


# ==================== 报告生成 ====================

def format_large_number(value: Optional[float]) -> str:
    """格式化大数字"""
    if value is None:
        return 'N/A'
    
    abs_val = abs(value)
    sign = '-' if value < 0 else ''
    
    if abs_val >= 1e12:
        return f"{sign}{abs_val/1e12:.2f}万亿"
    elif abs_val >= 1e8:
        return f"{sign}{abs_val/1e8:.2f}亿"
    elif abs_val >= 1e4:
        return f"{sign}{abs_val/1e4:.2f}万"
    else:
        return f"{sign}{abs_val:.2f}"


def generate_markdown_report(
    symbol: str,
    name: str,
    data: FinancialData,
    metrics: Dict,
    risk_signals: List[RiskSignal],
    health_score: int,
    source: str,
    analysis_time: str,
    periods: List[str],
    pdf_extracted: bool
) -> str:
    """生成 Markdown 格式的分析报告 - 完整五维度分析"""
    lines = []
    
    # 标题
    lines.append(f"# {name}({symbol}) 年报财务分析报告")
    lines.append("")
    lines.append(f"**分析时间**: {analysis_time}")
    lines.append(f"**数据来源**: {source}")
    lines.append("")
    
    # 数据来源声明
    lines.append("## 📊 数据来源声明")
    lines.append("")
    if pdf_extracted:
        lines.append("```")
        lines.append("✅ 本报告基于财报 PDF 文件深度解析")
        lines.append(f"   来源: {source}")
        lines.append(f"   报告期: {periods[0] if periods else 'N/A'}")
        lines.append("```")
    else:
        lines.append("```")
        lines.append("📈 数据来源: 网络公开财务数据")
        lines.append(f"   来源: {source}")
        lines.append(f"   报告期: {periods[0] if periods else 'N/A'}")
        lines.append("```")
    lines.append("")
    
    # 健康度评分
    lines.append("## 🎯 财务健康度评分")
    lines.append("")
    score = health_score
    if score >= 80:
        emoji = "🟢"
        status = "健康"
    elif score >= 60:
        emoji = "🟡"
        status = "一般"
    else:
        emoji = "🔴"
        status = "风险"
    lines.append(f"**{emoji} {score}/100 - {status}**")
    lines.append("")
    
    # ==================== 一、每股指标 ====================
    lines.append("## 一、每股指标分析")
    lines.append("")
    lines.append("每股指标反映公司每股股票的盈利和净资产情况，是投资者关注的重点。")
    lines.append("")
    lines.append("| 指标 | 数值 | 分析 |")
    lines.append("|------|------|------|")
    
    if data.eps is not None:
        eps_analysis = "盈利能力强" if data.eps >= 1 else ("盈利能力一般" if data.eps >= 0.3 else "盈利能力弱")
        lines.append(f"| 基本每股收益(EPS) | {data.eps:.4f} 元 | {eps_analysis} |")
    
    if data.diluted_eps is not None:
        lines.append(f"| 稀释每股收益 | {data.diluted_eps:.4f} 元 | - |")
    
    if data.bvps is not None:
        bvps_analysis = "净资产雄厚" if data.bvps >= 10 else ("净资产一般" if data.bvps >= 5 else "净资产较低")
        lines.append(f"| 每股净资产(BPS) | {data.bvps:.4f} 元 | {bvps_analysis} |")
    
    if data.cfps is not None:
        cfps_analysis = "现金流好" if data.cfps > 0 else "现金流需关注"
        lines.append(f"| 每股经营现金流 | {data.cfps:.4f} 元 | {cfps_analysis} |")
    
    if data.retained_eps is not None:
        lines.append(f"| 每股未分配利润 | {data.retained_eps:.4f} 元 | - |")
    
    lines.append("")
    
    # ==================== 二、盈利能力分析 ====================
    lines.append("## 二、盈利能力分析")
    lines.append("")
    lines.append("盈利能力是公司持续经营的核心，反映公司创造利润的能力。")
    lines.append("")
    lines.append("| 指标 | 数值 | 行业标准 | 分析 |")
    lines.append("|------|------|----------|------|")
    
    if data.roe is not None:
        roe_analysis = "优秀(≥15%)" if data.roe >= 15 else ("一般(8-15%)" if data.roe >= 8 else "较弱(<8%)")
        lines.append(f"| ROE(净资产收益率) | {data.roe:.2f}% | ≥15%优秀 | {roe_analysis} |")
    
    if data.roa is not None:
        roa_analysis = "优秀(≥8%)" if data.roa >= 8 else ("一般(4-8%)" if data.roa >= 4 else "较弱(<4%)")
        lines.append(f"| ROA(总资产收益率) | {data.roa:.2f}% | ≥8%优秀 | {roa_analysis} |")
    
    if data.gross_margin is not None:
        gm_analysis = "竞争力强(≥40%)" if data.gross_margin >= 40 else ("竞争力一般(20-40%)" if data.gross_margin >= 20 else "竞争力弱(<20%)")
        lines.append(f"| 销售毛利率 | {data.gross_margin:.2f}% | ≥40%优秀 | {gm_analysis} |")
    
    if data.net_margin is not None:
        nm_analysis = "盈利质量好(≥10%)" if data.net_margin >= 10 else ("盈利质量一般(5-10%)" if data.net_margin >= 5 else "盈利质量差(<5%)")
        lines.append(f"| 销售净利率 | {data.net_margin:.2f}% | ≥10%优秀 | {nm_analysis} |")
    
    if data.operating_margin is not None:
        opm_analysis = "主业盈利强" if data.operating_margin >= 15 else ("主业盈利一般" if data.operating_margin >= 5 else "主业盈利弱")
        lines.append(f"| 营业利润率 | {data.operating_margin:.2f}% | ≥15%优秀 | {opm_analysis} |")
    
    if data.roic is not None:
        lines.append(f"| ROIC(投入资本回报率) | {data.roic:.2f}% | ≥10%优秀 | - |")
    
    lines.append("")
    lines.append("### 📖 核心指标解读")
    lines.append("")
    lines.append("**ROE（净资产收益率）** - 巴菲特最看重的指标")
    lines.append("```")
    lines.append("ROE = 净利润 / 净资产 × 100%")
    lines.append("")
    lines.append("判断标准：")
    lines.append("  ≥20%：优秀，具有持续竞争优势")
    lines.append("  15-20%：良好，盈利能力较强")
    lines.append("  8-15%：一般，需分析原因")
    lines.append("  <8%：较弱，需重点关注")
    lines.append("```")
    lines.append("")
    
    # ==================== 三、偿债能力分析 ====================
    lines.append("## 三、偿债能力分析")
    lines.append("")
    lines.append("偿债能力反映公司偿还债务的能力，是财务安全的重要保障。")
    lines.append("")
    lines.append("| 指标 | 数值 | 行业标准 | 分析 |")
    lines.append("|------|------|----------|------|")
    
    if data.debt_ratio is not None:
        debt_analysis = "稳健(≤60%)" if data.debt_ratio <= 60 else ("需关注(60-70%)" if data.debt_ratio <= 70 else "高风险(>70%)")
        lines.append(f"| 资产负债率 | {data.debt_ratio:.2f}% | ≤60%稳健 | {debt_analysis} |")
    
    if data.current_ratio is not None:
        cr_analysis = "良好(≥1.5)" if data.current_ratio >= 1.5 else ("尚可(1.0-1.5)" if data.current_ratio >= 1 else "压力大(<1.0)")
        lines.append(f"| 流动比率 | {data.current_ratio:.2f} | ≥1.5良好 | {cr_analysis} |")
    
    if data.quick_ratio is not None:
        qr_analysis = "充足(≥1.0)" if data.quick_ratio >= 1 else "需警惕(<1.0)"
        lines.append(f"| 速动比率 | {data.quick_ratio:.2f} | ≥1.0充足 | {qr_analysis} |")
    
    if data.cash_ratio is not None:
        lines.append(f"| 现金比率 | {data.cash_ratio:.2f} | ≥0.2安全 | - |")
    
    if data.interest_coverage is not None:
        ic_analysis = "很强(≥5)" if data.interest_coverage >= 5 else ("尚可(3-5)" if data.interest_coverage >= 3 else "压力大(<3)")
        lines.append(f"| 利息保障倍数 | {data.interest_coverage:.2f} | ≥5很强 | {ic_analysis} |")
    
    if data.debt_to_equity is not None:
        lines.append(f"| 产权比率 | {data.debt_to_equity:.2f} | ≤1安全 | - |")
    
    if data.equity_multiplier is not None:
        lines.append(f"| 权益乘数 | {data.equity_multiplier:.2f} | - | - |")
    
    lines.append("")
    lines.append("### 📖 核心指标解读")
    lines.append("")
    lines.append("**杜邦分析 - ROE分解**")
    lines.append("```")
    lines.append("ROE = 净利率 × 总资产周转率 × 权益乘数")
    lines.append("     = 净利率 × 总资产周转率 × (1 / (1 - 资产负债率))")
    lines.append("")
    lines.append("三个驱动因素：")
    lines.append("  1. 净利率 → 盈利能力")
    lines.append("  2. 总资产周转率 → 运营效率")
    lines.append("  3. 权益乘数 → 财务杠杆")
    lines.append("```")
    lines.append("")
    
    # ==================== 四、成长能力分析 ====================
    lines.append("## 四、成长能力分析")
    lines.append("")
    lines.append("成长能力反映公司的业务扩张和盈利增长潜力。")
    lines.append("")
    lines.append("| 指标 | 数值 | 行业标准 | 分析 |")
    lines.append("|------|------|----------|------|")
    
    if data.revenue_growth is not None:
        rg_analysis = "高增长(≥30%)" if data.revenue_growth >= 30 else ("稳定增长(10-30%)" if data.revenue_growth >= 10 else ("增长放缓(0-10%)" if data.revenue_growth >= 0 else "收缩(<0%)"))
        lines.append(f"| 营业收入增长率 | {data.revenue_growth:.2f}% | ≥10%稳定 | {rg_analysis} |")
    
    if data.net_profit_growth is not None:
        pg_analysis = "高增长(≥30%)" if data.net_profit_growth >= 30 else ("稳定增长(10-30%)" if data.net_profit_growth >= 10 else ("增长放缓(0-10%)" if data.net_profit_growth >= 0 else "下滑(<0%)"))
        lines.append(f"| 净利润增长率 | {data.net_profit_growth:.2f}% | ≥10%稳定 | {pg_analysis} |")
    
    if data.operating_profit_growth is not None:
        lines.append(f"| 营业利润增长率 | {data.operating_profit_growth:.2f}% | - | - |")
    
    if data.total_assets_growth is not None:
        lines.append(f"| 总资产增长率 | {data.total_assets_growth:.2f}% | - | - |")
    
    if data.net_assets_growth is not None:
        lines.append(f"| 净资产增长率 | {data.net_assets_growth:.2f}% | - | - |")
    
    if data.eps_growth is not None:
        lines.append(f"| 每股收益增长率 | {data.eps_growth:.2f}% | - | - |")
    
    lines.append("")
    
    # ==================== 五、运营能力分析 ====================
    lines.append("## 五、运营能力分析")
    lines.append("")
    lines.append("运营能力反映公司资产管理的效率，体现公司的经营水平。")
    lines.append("")
    lines.append("| 指标 | 数值 | 行业标准 | 分析 |")
    lines.append("|------|------|----------|------|")
    
    if data.inventory_turnover is not None:
        it_analysis = "效率高(≥6次)" if data.inventory_turnover >= 6 else ("效率一般(3-6次)" if data.inventory_turnover >= 3 else "积压风险(<3次)")
        lines.append(f"| 存货周转率 | {data.inventory_turnover:.2f}次 | ≥6次高效 | {it_analysis} |")
    
    if data.inventory_turnover_days is not None:
        lines.append(f"| 存货周转天数 | {data.inventory_turnover_days:.0f}天 | ≤60天良好 | - |")
    
    if data.accounts_receivable_turnover is not None:
        ar_analysis = "回款强(≥10次)" if data.accounts_receivable_turnover >= 10 else ("回款一般(5-10次)" if data.accounts_receivable_turnover >= 5 else "回款风险(<5次)")
        lines.append(f"| 应收账款周转率 | {data.accounts_receivable_turnover:.2f}次 | ≥10次良好 | {ar_analysis} |")
    
    if data.accounts_receivable_turnover_days is not None:
        lines.append(f"| 应收账款周转天数 | {data.accounts_receivable_turnover_days:.0f}天 | ≤36天良好 | - |")
    
    if data.total_assets_turnover is not None:
        ta_analysis = "效率高(≥1次)" if data.total_assets_turnover >= 1 else ("效率一般(0.5-1次)" if data.total_assets_turnover >= 0.5 else "效率低(<0.5次)")
        lines.append(f"| 总资产周转率 | {data.total_assets_turnover:.2f}次 | ≥1次高效 | {ta_analysis} |")
    
    if data.fixed_assets_turnover is not None:
        lines.append(f"| 固定资产周转率 | {data.fixed_assets_turnover:.2f}次 | - | - |")
    
    if data.accounts_payable_turnover is not None:
        lines.append(f"| 应付账款周转率 | {data.accounts_payable_turnover:.2f}次 | - | - |")
    
    if data.operating_cycle is not None:
        oc_analysis = "周转快(≤60天)" if data.operating_cycle <= 60 else ("周转一般(60-120天)" if data.operating_cycle <= 120 else "周转慢(>120天)")
        lines.append(f"| 营业周期 | {data.operating_cycle:.0f}天 | ≤60天良好 | {oc_analysis} |")
    
    lines.append("")
    lines.append("### 📖 核心指标解读")
    lines.append("")
    lines.append("**营业周期**")
    lines.append("```")
    lines.append("营业周期 = 存货周转天数 + 应收账款周转天数")
    lines.append("")
    lines.append("营业周期越短，资金周转越快，经营效率越高")
    lines.append("```")
    lines.append("")
    
    # ==================== 六、现金流质量分析 ====================
    lines.append("## 六、现金流质量分析")
    lines.append("")
    lines.append("现金流质量是识别财务造假的核心指标，反映利润的含金量。")
    lines.append("")
    lines.append("| 指标 | 数值 | 行业标准 | 分析 |")
    lines.append("|------|------|----------|------|")
    
    if data.net_cash_ratio is not None:
        ncr_analysis = "质量高(≥1.2)" if data.net_cash_ratio >= 1.2 else ("质量良好(1.0-1.2)" if data.net_cash_ratio >= 1 else ("需关注(0.7-1.0)" if data.net_cash_ratio >= 0.7 else "⚠️预警(<0.7)"))
        lines.append(f"| 净现比 | {data.net_cash_ratio:.2f} | ≥1.0健康 | {ncr_analysis} |")
    
    if data.cash_to_sales is not None:
        cts_analysis = "回款好(≥1.1)" if data.cash_to_sales >= 1.1 else ("回款正常(1.0-1.1)" if data.cash_to_sales >= 1 else "应收款多(<1.0)")
        lines.append(f"| 销售现金比率 | {data.cash_to_sales:.2f} | ≥1.0正常 | {cts_analysis} |")
    
    if data.cash_to_operating_profit is not None:
        lines.append(f"| 经营现金流/营业利润 | {data.cash_to_operating_profit:.2f} | - | - |")
    
    lines.append("")
    lines.append("### 📖 马氏定律（财务造假识别）")
    lines.append("")
    lines.append("```")
    lines.append("净现比 = 经营活动现金流净额 / 净利润")
    lines.append("")
    lines.append("判断标准：")
    lines.append("  ≥1.2：利润有充足现金支撑，质量高")
    lines.append("  1.0-1.2：利润有现金支撑，质量良好")
    lines.append("  0.7-1.0：利润含金量一般，需关注")
    lines.append("  <0.7：⚠️ 利润含金量低，可能存在虚增利润")
    lines.append("")
    lines.append("【马氏定律】")
    lines.append("长期净现比低于0.7，需警惕利润造假风险！")
    lines.append("```")
    lines.append("")
    
    # ==================== 核心财务数据 ====================
    if pdf_extracted:
        lines.append("## 📋 核心财务数据（PDF提取）")
        lines.append("")
        
        # 资产负债表
        lines.append("### 资产负债表主要项目（单位：元）")
        lines.append("")
        lines.append("| 项目 | 金额 |")
        lines.append("|------|------|")
        lines.append(f"| 总资产 | {format_large_number(data.total_assets)} |")
        lines.append(f"| 总负债 | {format_large_number(data.total_liabilities)} |")
        lines.append(f"| 股东权益 | {format_large_number(data.total_equity)} |")
        lines.append(f"| 流动资产 | {format_large_number(data.current_assets)} |")
        lines.append(f"| 流动负债 | {format_large_number(data.current_liabilities)} |")
        lines.append(f"| 货币资金 | {format_large_number(data.cash)} |")
        lines.append(f"| 存货 | {format_large_number(data.inventory)} |")
        lines.append(f"| 应收账款 | {format_large_number(data.accounts_receivable)} |")
        lines.append(f"| 固定资产 | {format_large_number(data.fixed_assets)} |")
        lines.append("")
        
        # 利润表
        lines.append("### 利润表主要项目（单位：元）")
        lines.append("")
        lines.append("| 项目 | 金额 |")
        lines.append("|------|------|")
        lines.append(f"| 营业收入 | {format_large_number(data.revenue)} |")
        lines.append(f"| 营业成本 | {format_large_number(data.operating_cost)} |")
        lines.append(f"| 毛利润 | {format_large_number(data.gross_profit)} |")
        lines.append(f"| 营业利润 | {format_large_number(data.operating_profit)} |")
        lines.append(f"| 净利润 | {format_large_number(data.net_profit)} |")
        lines.append(f"| 归属净利润 | {format_large_number(data.net_profit_attr)} |")
        lines.append("")
        
        # 现金流量表
        lines.append("### 现金流量表主要项目（单位：元）")
        lines.append("")
        lines.append("| 项目 | 金额 |")
        lines.append("|------|------|")
        lines.append(f"| 经营现金流 | {format_large_number(data.operating_cash_flow)} |")
        lines.append(f"| 投资现金流 | {format_large_number(data.investing_cash_flow)} |")
        lines.append(f"| 筹资现金流 | {format_large_number(data.financing_cash_flow)} |")
        lines.append(f"| 自由现金流 | {format_large_number(data.free_cash_flow)} |")
        lines.append("")
    
    # 历史指标对比
    if metrics:
        lines.append("## 📊 历史指标对比")
        lines.append("")
        
        period_header = " | ".join(periods[:4]) if periods else "N/A"
        
        for category in ['每股指标', '盈利能力', '偿债能力', '成长能力', '运营能力']:
            if category in metrics and metrics[category]:
                lines.append(f"### {category}")
                lines.append("")
                lines.append(f"| 指标 | {period_header} |")
                lines.append("|------|" + "|".join(["------|"] * min(4, len(periods))))
                
                for name, values in metrics[category].items():
                    formatted = [v if v else 'N/A' for v in values]
                    lines.append(f"| {name} | " + " | ".join(formatted) + " |")
                lines.append("")
    
    # 风险信号汇总
    lines.append("## ⚠️ 风险信号扫描")
    lines.append("")
    if risk_signals:
        lines.append("| 指标 | 当前值 | 风险等级 | 说明 |")
        lines.append("|------|--------|----------|------|")
        for signal in risk_signals:
            level_mark = "🔴" if signal.level == '高' else ("🟡" if signal.level == '中' else "🟢")
            lines.append(f"| {signal.name} | {signal.value} | {level_mark} {signal.level} | {signal.description} |")
    else:
        lines.append("暂无风险信号")
    lines.append("")
    
    # 综合评估
    lines.append("## 📝 综合评估")
    lines.append("")
    
    positives = [s for s in risk_signals if s.level == '低']
    negatives = [s for s in risk_signals if s.level in ['中', '高']]
    
    if positives:
        lines.append("### ✅ 有利因素")
        lines.append("")
        for s in positives[:8]:
            lines.append(f"- {s.description}")
        lines.append("")
    
    if negatives:
        lines.append("### ⚠️ 风险因素")
        lines.append("")
        for s in negatives[:8]:
            mark = "🔴" if s.level == '高' else "🟡"
            lines.append(f"- {mark} {s.description}")
        lines.append("")
    
    # 投资建议框架
    lines.append("### 💡 分析建议")
    lines.append("")
    lines.append("1. **盈利能力**：关注 ROE 是否稳定在 15% 以上，毛利率是否高于行业平均")
    lines.append("2. **偿债安全**：资产负债率控制在 60% 以内，流动比率保持在 1.5 以上")
    lines.append("3. **成长潜力**：营收和净利润增长率持续为正，且高于行业平均")
    lines.append("4. **现金流质量**：净现比长期高于 0.7，确保利润有现金支撑")
    lines.append("5. **运营效率**：周转率指标保持稳定或改善趋势")
    lines.append("")
    
    # 风险提示
    lines.append("## ⚖️ 风险提示")
    lines.append("")
    lines.append("1. 本分析基于公开财务数据，可能存在信息滞后或不完整的情况。")
    lines.append("2. 财务指标异常不代表一定存在问题，需结合行业特性和公司战略综合判断。")
    lines.append("3. 投资有风险，决策需谨慎，本报告不构成投资建议。")
    
    return "\n".join(lines)


# ==================== 主分析函数 ====================

async def analyze_stock(
    symbol: str,
    pdf_path: Optional[str] = None,
    periods: int = 4
) -> AnalysisResult:
    """
    分析股票财务数据
    
    Args:
        symbol: 股票代码
        pdf_path: PDF 文件路径（可选）
        periods: 报告期数量
    
    Returns:
        AnalysisResult: 分析结果
    """
    symbol = symbol.zfill(6)
    
    # 获取股票信息
    name, price, change = fetch_stock_info(symbol)
    
    result = AnalysisResult()
    result.symbol = symbol
    result.name = name
    result.analysis_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # 初始化 FinancialData
    fin_data = FinancialData()
    
    # 1. 优先从 PDF 提取数据
    if pdf_path:
        logger.info(f"从 PDF 提取财务数据: {pdf_path}")
        fin_data, pdf_success = parse_pdf_financial_data(pdf_path)
        if pdf_success:
            result.source = "财报PDF深度解析"
            result.pdf_extracted = True
            logger.info(f"PDF 提取成功，获得 {len([v for v in asdict(fin_data).values() if v is not None])} 个指标")
        else:
            logger.warning("PDF 提取不完整，补充网络数据")
    
    # 2. 补充网络数据
    try:
        html = fetch_financial_data(symbol)
        metrics, periods_list = parse_financial_data(html, periods)
        result.metrics = metrics
        result.periods = periods_list
        
        if not result.pdf_extracted:
            result.source = "新浪财经"
    except Exception as e:
        logger.error(f"获取网络财务数据失败: {e}")
        if not result.pdf_extracted:
            result.source = "数据获取失败"
    
    # 3. 分析风险信号
    risk_signals = analyze_financial_data(fin_data, result.metrics)
    result.risk_signals = [asdict(s) for s in risk_signals]
    
    # 4. 计算健康度评分
    score = 100
    for signal in risk_signals:
        if signal.level == '高':
            score -= 15
        elif signal.level == '中':
            score -= 5
    result.health_score = max(0, min(100, score))
    
    # 5. 存储 FinancialData
    result.financial_data = asdict(fin_data)
    
    # 6. 生成报告
    result.report = generate_markdown_report(
        symbol=result.symbol,
        name=result.name,
        data=fin_data,
        metrics=result.metrics,
        risk_signals=risk_signals,
        health_score=result.health_score,
        source=result.source,
        analysis_time=result.analysis_time,
        periods=result.periods,
        pdf_extracted=result.pdf_extracted
    )
    
    return result
