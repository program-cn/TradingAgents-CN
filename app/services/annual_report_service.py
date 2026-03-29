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


def extract_year_value_from_table(text: str, keyword: str, prefer_annual: bool = True) -> Optional[float]:
    """
    从表格文本中智能提取年度数据（优先）
    
    年报PDF通常包含多列数据：
    - 年度报表：本期数/上期数 或 本年数/上年数
    - 季度报表：本期数/上期数
    - 分季度数据：第一季度/第二季度...
    
    此函数优先提取年度报表中的本期/本年数据
    """
    # 查找关键词位置
    keyword_pos = text.find(keyword)
    if keyword_pos == -1:
        return None
    
    # 从关键词位置向后查找数值
    search_start = keyword_pos + len(keyword)
    search_text = text[search_start:search_start + 500]  # 向后查找500字符
    
    # 尝试多种表格格式匹配
    
    # 格式1: 标准表格格式 "项目  本期数  上期数" 或 "项目  本年数  上年数"
    # 匹配数字（含负号），优先取第一个（本期/本年数据）
    # 注意：负号可能是 "-" 或 "—" 或括号表示 "(xxx)"
    number_pattern = r'([\(（]?[-—]?[0-9,，.．]+[\)）]?)\s*(万亿|亿|万)?'
    matches = re.findall(number_pattern, search_text[:200])
    
    # 过滤掉明显不是数值的结果（如页码、年份等）
    valid_values = []
    for num_str, unit in matches:
        num_str = num_str.replace('，', ',').replace('．', '.').replace(',', '')
        
        # 检测负数：括号表示法 或 显式负号
        is_negative = False
        if num_str.startswith('(') or num_str.startswith('（'):
            is_negative = True
            num_str = num_str[1:-1] if num_str.endswith(')') or num_str.endswith('）') else num_str[1:]
        elif num_str.startswith('-') or num_str.startswith('—'):
            is_negative = True
            num_str = num_str[1:]
        
        try:
            num = float(num_str)
            # 排除年份（1900-2100范围）和页码（小于100的小整数）
            if 1900 <= num <= 2100:
                continue
            if num < 100 and num == int(num):
                continue  # 排除小整数
            
            # 应用负号
            if is_negative:
                num = -num
            
            # 处理单位
            if unit:
                multipliers = {'万亿': 1e12, '亿': 1e8, '万': 1e4}
                for u, m in multipliers.items():
                    if u in unit:
                        num *= m
                        break
            
            valid_values.append(num)
        except:
            continue
    
    if valid_values:
        return valid_values[0]  # 返回第一个有效数值（通常是本期/本年数据）
    
    return None


def identify_report_section(text: str, keyword: str) -> str:
    """
    识别关键词所在的报表区域类型
    
    Returns:
        'annual' - 年度报表区域
        'quarterly' - 季度报表区域  
        'segment' - 分季度数据区域
        'unknown' - 未知
    """
    # 向前查找最近的报表标题
    keyword_pos = text.find(keyword)
    if keyword_pos == -1:
        return 'unknown'
    
    # 向前搜索2000字符，查找报表标识
    prefix = text[max(0, keyword_pos - 2000):keyword_pos]
    
    # 季度报表标识
    quarterly_markers = ['第一季度', '第二季度', '第三季度', '第四季度', '一季度', '二季度', '三季度', '四季度',
                         '分季度', '季度报告', '季报']
    for marker in quarterly_markers:
        if marker in prefix:
            return 'quarterly'
    
    # 年度报表标识
    annual_markers = ['合并资产负债表', '合并利润表', '合并现金流量表', 
                      '资产负债表', '利润表', '现金流量表',
                      '本年数', '本期数', '年末余额', '期末余额']
    for marker in annual_markers:
        if marker in prefix:
            return 'annual'
    
    return 'unknown'


def extract_table_data(text: str) -> Dict[str, str]:
    """从文本中提取表格数据 - 优化版本，优先年度数据"""
    data = {}
    
    # 首先定位年报核心财务数据区域（合并报表）
    # 这些关键词之间的数据是核心年报数据
    annual_section_markers = [
        ('合并资产负债表', '合并利润表'),
        ('合并利润表', '合并现金流量表'),
        ('资产负债表', '利润表'),
    ]
    
    # 提取年度报表区域文本
    annual_text = ""
    for start_marker, end_marker in annual_section_markers:
        start_pos = text.find(start_marker)
        end_pos = text.find(end_marker)
        if start_pos != -1:
            if end_pos > start_pos:
                annual_text += text[start_pos:end_pos + 2000]
            else:
                annual_text += text[start_pos:start_pos + 5000]
    
    # 如果没找到合并报表，使用全文但排除分季度区域
    if not annual_text:
        annual_text = text
        # 尝试排除分季度数据区域
        quarterly_pattern = r'分季度.*?(?=合并|$)'
        annual_text = re.sub(quarterly_pattern, '', annual_text, flags=re.DOTALL)
    
    # ==================== 资产负债表指标 ====================
    balance_sheet_keywords = [
        # 资产
        ('total_assets', ['资产总计', '总资产']),
        ('current_assets', ['流动资产合计']),
        ('non_current_assets', ['非流动资产合计']),
        ('cash', ['货币资金']),
        ('trading_assets', ['交易性金融资产']),
        ('notes_receivable', ['应收票据']),
        ('accounts_receivable', ['应收账款']),
        ('prepayments', ['预付款项']),
        ('other_receivables', ['其他应收款']),
        ('inventory', ['存货']),
        ('contract_assets', ['合同资产']),
        ('long_term_equity_investment', ['长期股权投资']),
        ('fixed_assets', ['固定资产']),
        ('construction_in_progress', ['在建工程']),
        ('intangible_assets', ['无形资产']),
        ('goodwill', ['商誉']),
        
        # 负债
        ('total_liabilities', ['负债合计', '负债总计']),
        ('current_liabilities', ['流动负债合计']),
        ('non_current_liabilities', ['非流动负债合计', '非流动负债', '非流动负债总额', '非流动负债小计']),
        ('short_term_borrowings', ['短期借款']),
        ('notes_payable', ['应付票据']),
        ('accounts_payable', ['应付账款']),
        ('advance_receipts', ['预收款项']),
        ('contract_liabilities', ['合同负债']),
        ('employee_benefits_payable', ['应付职工薪酬']),
        ('taxes_payable', ['应交税费']),
        ('long_term_borrowings', ['长期借款']),
        ('bonds_payable', ['应付债券']),
        
        # 所有者权益
        ('total_equity', ['股东权益合计', '所有者权益合计', '归属于母公司股东权益合计']),
        ('retained_earnings', ['未分配利润']),
    ]
    
    # ==================== 利润表指标 ====================
    income_statement_keywords = [
        ('revenue', ['营业收入']),
        ('operating_cost', ['营业成本']),
        ('tax_surcharges', ['税金及附加']),
        ('selling_expenses', ['销售费用']),
        ('admin_expenses', ['管理费用']),
        ('rd_expenses', ['研发费用']),
        ('financial_expenses', ['财务费用']),
        ('interest_expense', ['利息支出', '利息费用', '利息支出（支出）', '利息支出(支出)', '其中：利息支出']),
        ('interest_income', ['利息收入', '利息收入（收入）', '利息收入(收入)', '减：利息收入']),
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
        ('net_profit', ['净利润']),
        ('net_profit_attr', ['归属于母公司股东的净利润']),
        ('minority_interest', ['少数股东损益']),
    ]
    
    # ==================== 现金流量表指标 ====================
    cashflow_keywords = [
        ('operating_cash_flow', ['经营活动产生的现金流量净额']),
        ('cash_received_sales', ['销售商品、提供劳务收到的现金']),
        ('tax_refund', ['收到的税费返还']),
        ('cash_paid_goods', ['购买商品、接受劳务支付的现金']),
        ('cash_paid_employees', ['支付给职工以及为职工支付的现金']),
        ('taxes_paid', ['支付的各项税费']),
        ('investing_cash_flow', ['投资活动产生的现金流量净额']),
        ('cash_paid_capex', ['购建固定资产、无形资产和其他长期资产支付的现金']),
        ('financing_cash_flow', ['筹资活动产生的现金流量净额']),
        ('cash_from_borrowing', ['取得借款收到的现金']),
        ('cash_paid_debt', ['偿还债务支付的现金']),
        ('cash_paid_dividends', ['分配股利、利润或偿付利息支付的现金']),
    ]
    
    # ==================== 每股指标（从主要指标表提取）====================
    per_share_keywords = [
        ('eps', ['基本每股收益']),
        ('diluted_eps', ['稀释每股收益']),
        ('bvps', ['每股净资产']),
        ('cfps', ['每股经营活动产生的现金流量净额']),
        ('retained_eps', ['每股未分配利润']),
        ('capital_reserve_ps', ['每股资本公积']),
    ]
    
    # ==================== 盈利能力指标 ====================
    # 注意：ROE优先从年报首页"主要财务指标"表格提取，这是最精确的披露值
    # 年报首页通常有"加权平均净资产收益率"的精确披露，比后续计算更准确
    profitability_keywords = [
        ('roe', ['加权平均净资产收益率', '净资产收益率', '全面摊薄净资产收益率']),
        ('roe_diluted', ['稀释净资产收益率']),
        ('roa', ['总资产收益率', '总资产报酬率']),
        ('gross_margin', ['销售毛利率', '毛利率']),
        ('net_margin', ['销售净利率', '净利率']),
        ('operating_margin', ['营业利润率']),
    ]
    
    # ==================== 偿债能力指标 ====================
    solvency_keywords = [
        ('debt_ratio', ['资产负债率']),
        ('current_ratio', ['流动比率']),
        ('quick_ratio', ['速动比率']),
        ('cash_ratio', ['现金比率']),
        # 注意：利息保障倍数不直接从PDF表格提取，应该通过计算得出
        # ('interest_coverage', ['利息保障倍数']),  # 已移除，改用计算方式
    ]
    
    # ==================== 成长能力指标 ====================
    growth_keywords = [
        ('revenue_growth', ['营业收入增长率']),
        ('net_profit_growth', ['净利润增长率']),
        ('operating_profit_growth', ['营业利润增长率']),
        ('total_assets_growth', ['总资产增长率']),
        ('net_assets_growth', ['净资产增长率']),
    ]
    
    # ==================== 运营能力指标 ====================
    operation_keywords = [
        ('inventory_turnover', ['存货周转率']),
        ('inventory_turnover_days', ['存货周转天数']),
        ('accounts_receivable_turnover', ['应收账款周转率']),
        ('accounts_receivable_turnover_days', ['应收账款周转天数']),
        ('total_assets_turnover', ['总资产周转率']),
        ('fixed_assets_turnover', ['固定资产周转率']),
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
    
    # 首先从年度报表区域提取
    for key, kw_list in all_keywords:
        for kw in kw_list:
            value = extract_year_value_from_table(annual_text, kw)
            if value is not None:
                data[key] = value
                break
    
    # 单独处理股本（需要从股本结构表提取，单位通常是元或股）
    total_shares_patterns = [
        r'股本[：:\s]*([0-9,，.．]+)\s*(亿股|万股|股)?',
        r'总股本[：:\s]*([0-9,，.．]+)\s*(亿股|万股|股)?',
        r'注册资本[：:\s]*([0-9,，.．]+)\s*(亿股|万股|股|元)?',
    ]
    
    for pattern in total_shares_patterns:
        match = re.search(pattern, text)
        if match:
            num_str = match.group(1).replace('，', ',').replace('．', '.').replace(',', '')
            unit = match.group(2) if match.lastindex >= 2 else ''
            try:
                num = float(num_str)
                # 根据单位转换为股数
                if '亿股' in unit:
                    num *= 1e8
                elif '万股' in unit:
                    num *= 1e4
                elif '股' in unit:
                    pass  # 已经是股数
                elif '元' in unit:
                    # 注册资本（元），假设每股面值1元
                    pass  # 保持原值
                else:
                    # 无单位，根据数值大小判断
                    if num < 100:  # 可能是亿股
                        num *= 1e8
                    elif num < 10000:  # 可能是万股
                        num *= 1e4
                data['total_shares'] = num
                break
            except:
                continue
    
    return data


def extract_interest_expense_deep(text: str, report_unit: str = '万元') -> Optional[float]:
    """
    深度提取利息支出数据
    
    年报中利息支出可能在多个位置：
    1. 利润表中"财务费用"行下的"其中：利息支出"
    2. 财务费用明细表
    3. 利润表附注
    
    重要：年报财务数据通常以"万元"为单位，需要正确处理单位转换
    
    Args:
        text: PDF文本
        report_unit: 报告单位（默认万元），从年报表头提取
    """
    # 首先尝试从文本中识别报告单位
    unit_patterns = [
        r'编制单位.*?[：:]?\s*(\d{4}).*?单位[：:]?\s*(元|万元|千元|百万)',
        r'合并资产负债表.*?单位[：:]?\s*(元|万元|千元|百万)',
        r'单位[：:]\s*(元|万元|千元|百万)',
    ]
    
    detected_unit = report_unit
    for pattern in unit_patterns:
        match = re.search(pattern, text[:10000], re.DOTALL)
        if match:
            detected_unit = match.group(1) if len(match.groups()) > 1 else match.group(0)
            logger.info(f"检测到报告单位: {detected_unit}")
            break
    
    # 单位转换系数（转换为元）
    unit_multipliers = {
        '元': 1,
        '万元': 1e4,
        '千元': 1e3,
        '百万': 1e6,
    }
    unit_mult = unit_multipliers.get(detected_unit, 1e4)  # 默认万元
    
    # 多种匹配模式
    patterns = [
        # 模式1: "其中：利息支出 xxx" 或 "其中：利息支出  xxx"
        r'其中[：:]\s*利息支出\s*[：:]?\s*([0-9,，.．]+)\s*(万亿|亿|万|元)?',
        # 模式2: "利息支出（支出）xxx" 或表格中的格式
        r'利息支出[（(]支出[）)]\s*[：:]?\s*([0-9,，.．]+)\s*(万亿|亿|万|元)?',
        # 模式3: "利息费用 xxx"
        r'利息费用\s*[：:]?\s*([0-9,，.．]+)\s*(万亿|亿|万|元)?',
        # 模式4: 财务费用明细中的利息支出（支持跨行匹配）
        r'财务费用.*?利息支出\s*[：:]?\s*([0-9,，.．]+)\s*(万亿|亿|万|元)?',
        # 模式5: "减：利息支出 xxx"（可能在收入抵减项中）
        r'减[：:]\s*利息支出\s*[：:]?\s*([0-9,，.．]+)\s*(万亿|亿|万|元)?',
        # 模式6: 表格格式 - "利息支出" 后面跟数值（表格列格式）
        r'利息支出\s+[：:]?\s*([0-9,，.．]+)\s*(万亿|亿|万)?',
        # 模式7: "利息支出（元）xxx"
        r'利息支出[（(]元[）)]?\s*[：:]?\s*([0-9,，.．]+)',
        # 模式8: 财务费用行中包含利息支出数字
        r'财务费用.*?([0-9,，.．]+)\s*万?.*?利息支出',
    ]
    
    found_values = []  # 收集所有找到的值，用于验证
    
    for pattern in patterns:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            num_str = match.group(1).replace('，', ',').replace('．', '.').replace(',', '')
            explicit_unit = match.group(2) if len(match.groups()) > 1 and match.group(2) else None
            
            try:
                num = float(num_str)
                # 排除不合理的值
                if num < 0.01 or num > 1e15:
                    continue
                
                # 处理单位：
                # 1. 如果数值后有明确单位（如"万"、"亿"），使用该单位
                # 2. 否则，使用检测到的报告单位
                if explicit_unit:
                    multipliers = {'万亿': 1e12, '亿': 1e8, '万': 1e4, '元': 1}
                    for u, m in multipliers.items():
                        if u in explicit_unit:
                            num *= m
                            break
                    logger.info(f"利息支出（显式单位 {explicit_unit}）: {num}")
                else:
                    # 使用报告单位（通常为万元）
                    num *= unit_mult
                    logger.info(f"利息支出（报告单位 {detected_unit}）: {num_str} -> {num}")
                
                # 验证：利息支出应该是一个合理的正数（通常在1万到100亿之间）
                if num > 0:
                    found_values.append(num)
                    logger.info(f"从模式 '{pattern[:40]}...' 提取利息支出: {num}")
            except:
                continue
    
    # 如果找到多个值，选择最合理的（通常是表格中第一个非零值）
    if found_values:
        # 过滤掉极端值，取中间值
        valid_values = [v for v in found_values if 1e4 <= v <= 1e11]  # 1万到1000亿之间
        if valid_values:
            # 返回最接近中位数的值
            valid_values.sort()
            result = valid_values[len(valid_values) // 2]
            logger.info(f"利息支出最终值: {result}")
            return result
        return found_values[0]
    
    return None


def extract_growth_metrics(text: str, extracted: Dict) -> Dict[str, float]:
    """
    提取历史数据并计算成长指标
    
    年报中通常包含本期数和上期数的对比数据
    我们需要提取这两期的数据，然后计算增长率
    
    格式通常为：
    - 项目 | 本期数 | 上期数
    - 营业收入 | xxx | xxx
    - 净利润 | xxx | xxx
    """
    growth_metrics = {}
    
    # 定义需要提取增长率的项目
    items_to_track = {
        'revenue': ['营业收入', '营业总收入'],
        'net_profit': ['净利润', '归属于母公司股东的净利润'],
        'operating_profit': ['营业利润'],
        'total_assets': ['资产总计', '总资产'],
        'total_equity': ['股东权益合计', '所有者权益合计'],
    }
    
    for key, keywords in items_to_track.items():
        # 如果已经从网络数据获取了增长率，跳过
        growth_key = f'{key}_growth'
        if growth_key in extracted and extracted[growth_key] is not None:
            continue
        
        for keyword in keywords:
            # 查找关键词位置
            keyword_pos = text.find(keyword)
            if keyword_pos == -1:
                continue
            
            # 从关键词位置向后查找，提取本期和上期数据
            search_text = text[keyword_pos:keyword_pos + 300]
            
            # 匹配数字（支持负数的括号表示法）
            number_pattern = r'[\(（]?[-—]?[0-9,，.．]+[\)）]?'
            matches = re.findall(number_pattern, search_text[:150])
            
            if len(matches) >= 2:
                # 解析第一个数字（本期）和第二个数字（上期）
                current_val = parse_number_with_sign(matches[0])
                prev_val = parse_number_with_sign(matches[1])
                
                if current_val is not None and prev_val is not None and prev_val != 0:
                    # 计算增长率
                    growth_rate = ((current_val - prev_val) / abs(prev_val)) * 100
                    
                    # 验证增长率的合理性
                    if -100 <= growth_rate <= 1000:  # 合理范围
                        growth_metrics[growth_key] = round(growth_rate, 2)
                        logger.info(f"计算 {keyword} 增长率: 本期 {current_val}, 上期 {prev_val}, 增长 {growth_rate:.2f}%")
                        break
            elif len(matches) == 1:
                # 只有本期数据，无法计算增长率
                pass
    
    return growth_metrics


def parse_number_with_sign(num_str: str) -> Optional[float]:
    """解析可能带负号的数字（支持括号表示法）"""
    num_str = num_str.replace('，', ',').replace('．', '.').replace(',', '')
    
    # 检测负数
    is_negative = False
    if num_str.startswith('(') or num_str.startswith('（'):
        is_negative = True
        num_str = num_str[1:-1] if (num_str.endswith(')') or num_str.endswith('）')) else num_str[1:]
    elif num_str.startswith('-') or num_str.startswith('—'):
        is_negative = True
        num_str = num_str[1:]
    
    try:
        num = float(num_str)
        # 排除年份和小整数
        if 1900 <= num <= 2100:
            return None
        if num < 100 and num == int(num):
            return None
        
        return -num if is_negative else num
    except:
        return None


def extract_periods_from_pdf(text: str) -> List[str]:
    """
    从 PDF 文本中提取报告期
    
    年报中通常包含多个报告期的数据，格式如：
    - "2024年12月31日"、"2023年12月31日"
    - "2024年度"、"2023年度"
    - "本期数"、"上期数" 对应的报告期
    """
    periods = []
    
    # 模式1: 表格表头中的日期格式
    date_patterns = [
        # 格式: 2024年12月31日
        r'(\d{4}年\d{1,2}月\d{1,2}日)',
        # 格式: 2024年度
        r'(\d{4}年度)',
        # 格式: 2024年
        r'(\d{4}年)(?=\d|$)',
    ]
    
    for pattern in date_patterns:
        matches = re.findall(pattern, text)
        if matches:
            # 去重并按时间排序（最新的在前）
            unique_dates = list(dict.fromkeys(matches))
            # 按年份降序排序
            unique_dates.sort(key=lambda x: int(re.search(r'\d{4}', x).group()) if re.search(r'\d{4}', x) else 0, reverse=True)
            periods = unique_dates[:4]  # 最多取4个报告期
            if periods:
                break
    
    # 如果没找到日期，尝试从"本期/上期"推断
    if not periods:
        # 尝试从文档开头提取报告年度
        year_match = re.search(r'(\d{4})年度报告', text[:5000])
        if year_match:
            year = int(year_match.group(1))
            periods = [f"{year}年度", f"{year-1}年度", f"{year-2}年度"]
    
    return periods


def parse_pdf_financial_data(pdf_path: str) -> Tuple[FinancialData, bool]:
    """解析 PDF 财务数据 - 完整五维度指标计算"""
    text = extract_text_from_pdf(pdf_path)
    
    if not text:
        return FinancialData(), False
    
    logger.info(f"PDF 文本长度: {len(text)} 字符")
    
    # 提取表格数据
    extracted = extract_table_data(text)
    
    # === 专门提取利息支出（如果未提取到）===
    # 年报中利息支出可能在多个位置：财务费用明细、利润表附注等
    if 'interest_expense' not in extracted or extracted.get('interest_expense') is None:
        interest_exp = extract_interest_expense_deep(text)
        if interest_exp is not None:
            extracted['interest_expense'] = interest_exp
            logger.info(f"深度提取利息支出: {interest_exp}")
    
    # === 提取历史年度数据并计算增长率 ===
    # 年报中通常有"本期"和"上期"数据，可以计算同比
    growth_data = extract_growth_metrics(text, extracted)
    if growth_data:
        extracted.update(growth_data)
        logger.info(f"计算成长指标: {growth_data}")
    
    logger.info(f"从 PDF 提取到 {len(extracted)} 个指标: {list(extracted.keys())}")
    
    # 构建 FinancialData
    data = FinancialData()
    for key, value in extracted.items():
        if hasattr(data, key):
            setattr(data, key, value)
    
    # ==================== 计算派生指标 ====================
    
    # === 总负债（验证并修正）===
    # 优先使用流动负债 + 非流动负债计算，这比直接提取更可靠
    # 因为年报中"负债合计"可能被其他行错误匹配
    if data.current_liabilities is not None and data.non_current_liabilities is not None:
        calculated_total = data.current_liabilities + data.non_current_liabilities
        # 如果提取的总负债与计算值差异较大（>5%），使用计算值
        if data.total_liabilities is None or abs(data.total_liabilities - calculated_total) > calculated_total * 0.05:
            logger.info(f"总负债修正: 提取值 {data.total_liabilities} -> 计算值 {calculated_total} "
                       f"(流动负债 {data.current_liabilities} + 非流动负债 {data.non_current_liabilities})")
            data.total_liabilities = calculated_total
    elif data.total_liabilities is None:
        if data.current_liabilities:
            data.total_liabilities = data.current_liabilities + (data.non_current_liabilities or 0)
    
    # === 毛利润 ===
    if data.revenue and data.operating_cost:
        data.gross_profit = data.revenue - data.operating_cost
    
    # === 自由现金流 ===
    if data.operating_cash_flow:
        capex = data.cash_paid_capex if data.cash_paid_capex else abs(data.operating_cash_flow) * 0.2
        data.free_cash_flow = data.operating_cash_flow - abs(capex)
    
    # ==================== 一、每股指标计算 ====================
    # 如果没有从PDF提取到每股指标，尝试计算
    # 注意：total_shares 在提取时已转换为股数（不是万股）
    
    # 每股收益 EPS（如果未提取）
    if data.eps is None and data.net_profit_attr and data.total_shares and data.total_shares > 0:
        data.eps = data.net_profit_attr / data.total_shares
    
    # 每股净资产 BVPS
    if data.bvps is None and data.total_equity and data.total_shares and data.total_shares > 0:
        data.bvps = data.total_equity / data.total_shares
    
    # 每股经营现金流 CFPS
    if data.cfps is None and data.operating_cash_flow and data.total_shares and data.total_shares > 0:
        data.cfps = data.operating_cash_flow / data.total_shares
    
    # 每股未分配利润
    if data.retained_eps is None and data.retained_earnings and data.total_shares and data.total_shares > 0:
        data.retained_eps = data.retained_earnings / data.total_shares
    
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
    # 关键：必须正确提取利息支出，不能用财务费用替代
    # 重要：确保营业利润和利息支出使用相同的单位
    if data.interest_coverage is None:
        interest_exp = data.interest_expense
        operating_profit = data.operating_profit or 0
        
        # 单位一致性检查：
        # 如果营业利润是亿元级别，而利息支出是万元级别，需要统一单位
        # 典型情况：营业利润=2.83亿，利息支出=1069.77万
        # 如果利息支出被错误提取为1069.77元（未乘以万），则会导致倍数异常
        if interest_exp and operating_profit > 0:
            # 检查数量级差异
            ratio = operating_profit / interest_exp
            # 正常情况下，利息保障倍数应该在 1-100 之间
            # 如果 ratio < 0.01，说明利息支出可能单位不对（太大）
            # 如果 ratio > 10000，说明利息支出可能单位不对（太小）
            if ratio < 0.01:
                # 利息支出太大，可能是单位错误（应该是万元但被当作元）
                # 尝试除以10000
                logger.warning(f"利息支出 {interest_exp} 与营业利润 {operating_profit} 数量级差异过大(ratio={ratio:.4f})，尝试修正单位")
                interest_exp_corrected = interest_exp / 1e4
                new_ratio = operating_profit / interest_exp_corrected
                if 0.5 < new_ratio < 500:  # 合理的利息保障倍数范围
                    interest_exp = interest_exp_corrected
                    logger.info(f"利息支出单位修正: {data.interest_expense} -> {interest_exp}（除以10000）")
            elif ratio > 10000:
                # 利息支出太小，可能是单位错误（应该是元但被当作万元）
                logger.warning(f"利息支出 {interest_exp} 与营业利润 {operating_profit} 数量级差异过大(ratio={ratio:.4f})，尝试修正单位")
                interest_exp_corrected = interest_exp * 1e4
                new_ratio = operating_profit / interest_exp_corrected
                if 0.5 < new_ratio < 500:
                    interest_exp = interest_exp_corrected
                    logger.info(f"利息支出单位修正: {data.interest_expense} -> {interest_exp}（乘以10000）")
        
        # 如果利息支出未提取，尝试从财务费用中推断
        # 注意：财务费用 = 利息支出 - 利息收入 + 汇兑损益 + 手续费等
        # 只有当财务费用为正时，才可能包含正的利息支出
        if interest_exp is None or interest_exp <= 0:
            if data.financial_expenses and data.financial_expenses > 0:
                # 财务费用为正，推测有利息支出，但无法精确获取
                # 此时设置一个保守值表示"无法精确计算"
                logger.warning(f"利息支出未提取，财务费用 {data.financial_expenses}，无法精确计算利息保障倍数")
                interest_exp = None
        
        # 只有当利息支出确实存在且大于0时才计算
        if interest_exp and interest_exp > 0 and operating_profit > 0:
            # 利息保障倍数 = (营业利润 + 利息费用) / 利息费用
            # EBIT = 营业利润 + 利息费用
            ebit = operating_profit + interest_exp
            data.interest_coverage = ebit / interest_exp
            data.times_interest_earned = data.interest_coverage
            logger.info(f"利息保障倍数计算: 营业利润 {operating_profit} + 利息支出 {interest_exp} = EBIT {ebit}, 倍数 = {data.interest_coverage:.2f}")
            
            # 验证结果合理性
            if data.interest_coverage < 0.5 or data.interest_coverage > 500:
                logger.warning(f"利息保障倍数 {data.interest_coverage:.2f} 异常，可能存在单位问题")
        else:
            # 没有利息支出或利息支出为0，说明几乎没有有息负债
            # 设置一个很大的值表示"无风险"
            if operating_profit > 0:
                data.interest_coverage = 999.0  # 表示极高，无有息负债
                data.times_interest_earned = data.interest_coverage
                logger.info("利息支出为0或未提取，设置利息保障倍数为999（无有息负债）")
    
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
    
    # 指标分类定义 - 增强匹配关键词
    metric_categories = {
        '每股指标': ['每股收益', '每股净资产', '每股经营', '每股未分配', '每股资本', '每股现金'],
        '盈利能力': ['净资产收益率', '毛利率', '净利率', '营业利润率', '总资产报酬率', 'ROE', 'ROA', '总资产净利率', '息税前利润'],
        '偿债能力': ['资产负债率', '流动比率', '速动比率', '利息保障', '有息负债', '产权比率', '权益乘数'],
        '运营能力': ['周转率', '周转天数'],
        '成长能力': ['增长率', '增长比', '同比', '增幅', '增长', '营收增长', '利润增长', '资产增长']
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
        matched = False
        for category, keywords in metric_categories.items():
            if any(kw in name for kw in keywords):
                clean_name = name.replace(category, '').strip()
                if clean_name not in metrics[category]:
                    metrics[category][clean_name] = values[:periods]
                matched = True
                break
        
        # 如果没有匹配到任何分类，记录到日志（调试用）
        if not matched and values[0] and values[0] not in ['--', '']:
            logger.debug(f"未分类指标: {name} = {values[0]}")
    
    logger.info(f"解析到指标: 每股{len(metrics['每股指标'])}个, 盈利{len(metrics['盈利能力'])}个, "
                f"偿债{len(metrics['偿债能力'])}个, 运营{len(metrics['运营能力'])}个, "
                f"成长{len(metrics['成长能力'])}个")
    
    return metrics, periods_list


def build_metrics_from_financial_data(data: FinancialData, periods: List[str]) -> Dict[str, Dict[str, List[Optional[str]]]]:
    """
    从FinancialData构建metrics数据结构，用于历史指标对比
    
    当PDF提取成功但网络数据获取失败时，使用此函数构建metrics数据
    这样历史指标对比表格就不会为空
    """
    metrics = {
        '每股指标': {},
        '盈利能力': {},
        '偿债能力': {},
        '运营能力': {},
        '成长能力': {},
    }
    
    # 生成报告期列表（如果没有，使用默认格式）
    period_count = len(periods) if periods else 1
    
    def make_values(val):
        """生成多期值列表（当前只有一期数据，其他期为N/A）"""
        if val is None:
            return [None] * period_count
        formatted = f"{val:.4f}" if isinstance(val, float) and abs(val) < 100 else f"{val:.2f}"
        return [formatted] + [None] * (period_count - 1)
    
    def make_percent_values(val):
        """生成百分比格式的值列表"""
        if val is None:
            return [None] * period_count
        return [f"{val:.2f}%"] + [None] * (period_count - 1)
    
    # 每股指标
    if data.eps is not None:
        metrics['每股指标']['基本每股收益(元)'] = make_values(data.eps)
    if data.bvps is not None:
        metrics['每股指标']['每股净资产(元)'] = make_values(data.bvps)
    if data.cfps is not None:
        metrics['每股指标']['每股经营现金流(元)'] = make_values(data.cfps)
    if data.retained_eps is not None:
        metrics['每股指标']['每股未分配利润(元)'] = make_values(data.retained_eps)
    
    # 盈利能力
    if data.roe is not None:
        metrics['盈利能力']['净资产收益率(%)'] = make_percent_values(data.roe)
    if data.roa is not None:
        metrics['盈利能力']['总资产收益率(%)'] = make_percent_values(data.roa)
    if data.gross_margin is not None:
        metrics['盈利能力']['销售毛利率(%)'] = make_percent_values(data.gross_margin)
    if data.net_margin is not None:
        metrics['盈利能力']['销售净利率(%)'] = make_percent_values(data.net_margin)
    if data.operating_margin is not None:
        metrics['盈利能力']['营业利润率(%)'] = make_percent_values(data.operating_margin)
    
    # 偿债能力
    if data.debt_ratio is not None:
        metrics['偿债能力']['资产负债率(%)'] = make_percent_values(data.debt_ratio)
    if data.current_ratio is not None:
        metrics['偿债能力']['流动比率'] = make_values(data.current_ratio)
    if data.quick_ratio is not None:
        metrics['偿债能力']['速动比率'] = make_values(data.quick_ratio)
    if data.interest_coverage is not None:
        metrics['偿债能力']['利息保障倍数'] = make_values(data.interest_coverage)
    if data.debt_to_equity is not None:
        metrics['偿债能力']['产权比率'] = make_values(data.debt_to_equity)
    
    # 运营能力
    if data.total_assets_turnover is not None:
        metrics['运营能力']['总资产周转率(次)'] = make_values(data.total_assets_turnover)
    if data.inventory_turnover is not None:
        metrics['运营能力']['存货周转率(次)'] = make_values(data.inventory_turnover)
    if data.inventory_turnover_days is not None:
        metrics['运营能力']['存货周转天数(天)'] = make_values(data.inventory_turnover_days)
    if data.accounts_receivable_turnover is not None:
        metrics['运营能力']['应收账款周转率(次)'] = make_values(data.accounts_receivable_turnover)
    
    # 成长能力
    if data.revenue_growth is not None:
        metrics['成长能力']['营业收入增长率(%)'] = make_percent_values(data.revenue_growth)
    if data.net_profit_growth is not None:
        metrics['成长能力']['净利润增长率(%)'] = make_percent_values(data.net_profit_growth)
    if data.operating_profit_growth is not None:
        metrics['成长能力']['营业利润增长率(%)'] = make_percent_values(data.operating_profit_growth)
    if data.total_assets_growth is not None:
        metrics['成长能力']['总资产增长率(%)'] = make_percent_values(data.total_assets_growth)
    
    # 清理空分类
    metrics = {k: v for k, v in metrics.items() if v}
    
    return metrics


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


def calculate_health_score(data: FinancialData, risk_signals: List[RiskSignal]) -> int:
    """
    计算财务健康度评分 - 加权评分模型
    
    核心原则：
    1. 优质指标应该加分，而不仅仅是弱项扣分
    2. 不同维度的权重不同，核心指标权重更高
    3. 避免单一弱项过度拉低总分
    
    维度权重：
    - 盈利能力（ROE、毛利率、净利率）：权重 30%
    - 偿债能力（资产负债率、流动比率）：权重 25%
    - 现金流质量（净现比）：权重 20%
    - 运营能力（周转率）：权重 15%
    - 成长能力（增长率）：权重 10%
    """
    score = 60  # 基础分 60 分（中等水平）
    
    # ==================== 一、盈利能力评分（最多 +20/-15 分）====================
    profitability_score = 0
    
    # ROE 评分（核心指标）
    if data.roe is not None:
        if data.roe >= 20:
            profitability_score += 8  # 优秀
        elif data.roe >= 15:
            profitability_score += 5  # 良好
        elif data.roe >= 8:
            profitability_score += 0  # 一般
        else:
            profitability_score -= 5  # 较弱
    
    # 毛利率评分
    if data.gross_margin is not None:
        if data.gross_margin >= 40:
            profitability_score += 4
        elif data.gross_margin >= 30:
            profitability_score += 2
        elif data.gross_margin < 15:
            profitability_score -= 3
    
    # 净利率评分
    if data.net_margin is not None:
        if data.net_margin >= 10:
            profitability_score += 4
        elif data.net_margin >= 5:
            profitability_score += 2
        elif data.net_margin < 3:
            profitability_score -= 2
    
    score += max(-15, min(20, profitability_score))
    
    # ==================== 二、偿债能力评分（最多 +15/-15 分）====================
    solvency_score = 0
    
    # 资产负债率评分
    if data.debt_ratio is not None:
        if data.debt_ratio <= 40:
            solvency_score += 6  # 非常稳健
        elif data.debt_ratio <= 60:
            solvency_score += 3  # 稳健
        elif data.debt_ratio > 70:
            solvency_score -= 8  # 高风险
    
    # 流动比率评分
    if data.current_ratio is not None:
        if data.current_ratio >= 2.0:
            solvency_score += 5
        elif data.current_ratio >= 1.5:
            solvency_score += 3
        elif data.current_ratio < 1.0:
            solvency_score -= 5
    
    # 利息保障倍数评分（特殊处理：无有息负债是极大的加分项）
    if data.interest_coverage is not None:
        if data.interest_coverage >= 100:
            solvency_score += 5  # 无有息负债，财务结构极佳
        elif data.interest_coverage >= 5:
            solvency_score += 2
        elif data.interest_coverage < 1:
            solvency_score -= 5
    
    score += max(-15, min(15, solvency_score))
    
    # ==================== 三、现金流质量评分（最多 +15/-10 分）====================
    cashflow_score = 0
    
    # 净现比评分（核心指标）
    if data.net_cash_ratio is not None:
        if data.net_cash_ratio >= 1.5:
            cashflow_score += 8  # 利润质量极佳
        elif data.net_cash_ratio >= 1.0:
            cashflow_score += 4  # 利润有现金支撑
        elif data.net_cash_ratio >= 0.7:
            cashflow_score += 0  # 一般
        else:
            cashflow_score -= 8  # 利润含金量低（马氏定律预警）
    
    score += max(-10, min(15, cashflow_score))
    
    # ==================== 四、运营能力评分（最多 +10/-10 分）====================
    operation_score = 0
    
    # 应收账款周转率评分
    if data.accounts_receivable_turnover is not None:
        if data.accounts_receivable_turnover >= 10:
            operation_score += 3
        elif data.accounts_receivable_turnover >= 5:
            operation_score += 1
        elif data.accounts_receivable_turnover < 3:
            operation_score -= 3
    
    # 存货周转率评分（行业差异大，适度放宽）
    if data.inventory_turnover is not None:
        if data.inventory_turnover >= 4:
            operation_score += 2
        elif data.inventory_turnover < 2:
            operation_score -= 2
    
    # 总资产周转率评分
    if data.total_assets_turnover is not None:
        if data.total_assets_turnover >= 1.0:
            operation_score += 2
        elif data.total_assets_turnover < 0.3:
            operation_score -= 2
    
    score += max(-10, min(10, operation_score))
    
    # ==================== 五、成长能力评分（最多 +10/-10 分）====================
    growth_score = 0
    
    # 营业收入增长率评分
    if data.revenue_growth is not None:
        if data.revenue_growth >= 20:
            growth_score += 3
        elif data.revenue_growth >= 10:
            growth_score += 2
        elif data.revenue_growth >= 0:
            growth_score += 0
        else:
            growth_score -= 3
    
    # 净利润增长率评分
    if data.net_profit_growth is not None:
        if data.net_profit_growth >= 20:
            growth_score += 3
        elif data.net_profit_growth >= 10:
            growth_score += 2
        elif data.net_profit_growth >= 0:
            growth_score += 0
        else:
            growth_score -= 4  # 利润下滑影响更大
    
    score += max(-10, min(10, growth_score))
    
    # ==================== 特殊调整 ====================
    
    # 如果有多项优质指标，额外加分
    excellent_count = 0
    if data.roe and data.roe >= 15:
        excellent_count += 1
    if data.debt_ratio and data.debt_ratio <= 50:
        excellent_count += 1
    if data.net_cash_ratio and data.net_cash_ratio >= 1.0:
        excellent_count += 1
    if data.current_ratio and data.current_ratio >= 1.5:
        excellent_count += 1
    
    if excellent_count >= 4:
        score += 5  # 多项优质，额外加分
    
    # 记录评分明细（调试用）
    logger.info(f"健康度评分明细: 基础分60 + 盈利{profitability_score} + 偿债{solvency_score} + "
                f"现金流{cashflow_score} + 运营{operation_score} + 成长{growth_score} = {score}")
    
    return max(0, min(100, score))


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
    # 注意：不再从网络数据获取利息保障倍数，因为网络数据的口径可能不一致
    # 应该优先使用从PDF计算出的值（更准确）
    # if ic_val is None:
    #     ic_val = safe_float(metrics.get('偿债能力', {}).get('利息保障倍数', [None])[0])
    
    if ic_val is not None:
        if ic_val >= 100:
            # 特殊值：表示几乎没有有息负债
            signals.append(RiskSignal('利息保障倍数', '极高（无有息负债）', '低',
                '利息支出极低或为零，几乎没有有息负债压力，财务结构极为稳健'))
        elif ic_val >= 5:
            signals.append(RiskSignal('利息保障倍数', f'{ic_val:.2f}倍', '低',
                f'利息保障倍数 {ic_val:.2f}倍 >= 5，偿债能力很强'))
        elif ic_val >= 3:
            signals.append(RiskSignal('利息保障倍数', f'{ic_val:.2f}倍', '中',
                f'利息保障倍数 {ic_val:.2f}倍，偿债能力尚可'))
        elif ic_val >= 1:
            signals.append(RiskSignal('利息保障倍数', f'{ic_val:.2f}倍', '高',
                f'利息保障倍数 {ic_val:.2f}倍，偿债压力较大'))
        else:
            signals.append(RiskSignal('利息保障倍数', f'{ic_val:.2f}倍', '高',
                f'利息保障倍数 {ic_val:.2f}倍 < 1，无法覆盖利息支出'))
    else:
        # 如果利息保障倍数仍未计算，记录警告
        logger.warning("利息保障倍数未计算，可能影响偿债能力评估")
    
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
    lines.append("### 📖 口径说明")
    lines.append("")
    lines.append("```")
    lines.append("每股指标计算口径：")
    lines.append("- EPS（每股收益）：使用报告期加权平均股本计算")
    lines.append("- BPS（每股净资产）：使用期末股本计算")
    lines.append("- CFPS（每股经营现金流）：使用期末股本计算")
    lines.append("")
    lines.append("注：两种股本口径差异通常小于1%，对分析结论影响微小。")
    lines.append("```")
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
        lines.append("| _注: ROA按期末总资产计算，若按平均资产约低0.1-0.2个百分点_ | | |")
    
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
    network_success = False
    try:
        html = fetch_financial_data(symbol)
        metrics, periods_list = parse_financial_data(html, periods)
        result.metrics = metrics
        result.periods = periods_list
        network_success = True
        
        # 从网络数据补充 PDF 没提取到的指标
        if metrics:
            # 补充成长能力指标
            growth_metrics = metrics.get('成长能力', {})
            if fin_data.revenue_growth is None and '营业收入增长率(%)' in growth_metrics:
                val = growth_metrics['营业收入增长率(%)'][0]
                if val:
                    fin_data.revenue_growth = safe_float(val)
            if fin_data.net_profit_growth is None and '净利润增长率(%)' in growth_metrics:
                val = growth_metrics['净利润增长率(%)'][0]
                if val:
                    fin_data.net_profit_growth = safe_float(val)
            if fin_data.total_assets_growth is None and '总资产增长率(%)' in growth_metrics:
                val = growth_metrics['总资产增长率(%)'][0]
                if val:
                    fin_data.total_assets_growth = safe_float(val)
            if fin_data.net_assets_growth is None and '净资产增长率(%)' in growth_metrics:
                val = growth_metrics['净资产增长率(%)'][0]
                if val:
                    fin_data.net_assets_growth = safe_float(val)
            
            # 补充运营能力指标
            operation_metrics = metrics.get('运营能力', {})
            if fin_data.total_assets_turnover is None and '总资产周转率(次)' in operation_metrics:
                val = operation_metrics['总资产周转率(次)'][0]
                if val:
                    fin_data.total_assets_turnover = safe_float(val)
            if fin_data.inventory_turnover is None and '存货周转率(次)' in operation_metrics:
                val = operation_metrics['存货周转率(次)'][0]
                if val:
                    fin_data.inventory_turnover = safe_float(val)
            if fin_data.accounts_receivable_turnover is None and '应收账款周转率(次)' in operation_metrics:
                val = operation_metrics['应收账款周转率(次)'][0]
                if val:
                    fin_data.accounts_receivable_turnover = safe_float(val)
            
            # 补充每股指标
            per_share = metrics.get('每股指标', {})
            if fin_data.eps is None and '基本每股收益(元)' in per_share:
                val = per_share['基本每股收益(元)'][0]
                if val:
                    fin_data.eps = safe_float(val)
            if fin_data.bvps is None and '每股净资产_调整后(元)' in per_share:
                val = per_share['每股净资产_调整后(元)'][0]
                if val:
                    fin_data.bvps = safe_float(val)
            
            # 补充盈利能力指标
            profitability = metrics.get('盈利能力', {})
            if fin_data.roe is None and '净资产收益率(%)' in profitability:
                val = profitability['净资产收益率(%)'][0]
                if val:
                    fin_data.roe = safe_float(val)
            if fin_data.gross_margin is None and '销售毛利率(%)' in profitability:
                val = profitability['销售毛利率(%)'][0]
                if val:
                    fin_data.gross_margin = safe_float(val)
            if fin_data.net_margin is None and '销售净利率(%)' in profitability:
                val = profitability['销售净利率(%)'][0]
                if val:
                    fin_data.net_margin = safe_float(val)
            
            # 补充偿债能力指标
            solvency = metrics.get('偿债能力', {})
            if fin_data.debt_ratio is None and '资产负债率(%)' in solvency:
                val = solvency['资产负债率(%)'][0]
                if val:
                    fin_data.debt_ratio = safe_float(val)
            if fin_data.current_ratio is None and '流动比率' in solvency:
                val = solvency['流动比率'][0]
                if val:
                    fin_data.current_ratio = safe_float(val)
            if fin_data.quick_ratio is None and '速动比率' in solvency:
                val = solvency['速动比率'][0]
                if val:
                    fin_data.quick_ratio = safe_float(val)
        
        if not result.pdf_extracted:
            result.source = "新浪财经"
    except Exception as e:
        logger.error(f"获取网络财务数据失败: {e}")
        if not result.pdf_extracted:
            result.source = "数据获取失败"
    
    # 2.5 如果网络数据失败，尝试从 PDF 提取报告期
    if not result.periods and pdf_path:
        logger.info("网络数据获取失败，尝试从 PDF 提取报告期")
        try:
            pdf_text = extract_text_from_pdf(pdf_path)
            result.periods = extract_periods_from_pdf(pdf_text)
            if result.periods:
                logger.info(f"从 PDF 提取报告期: {result.periods}")
        except Exception as e:
            logger.warning(f"从 PDF 提取报告期失败: {e}")
    
    # 2.6 如果网络数据失败但PDF提取成功，构建metrics数据用于历史对比
    if result.pdf_extracted and not result.metrics:
        logger.info("网络数据失败，从PDF数据构建metrics用于历史对比")
        result.metrics = build_metrics_from_financial_data(fin_data, result.periods)
        if result.metrics:
            logger.info(f"成功从PDF数据构建metrics: {list(result.metrics.keys())}")
    
    # 3. 分析风险信号
    risk_signals = analyze_financial_data(fin_data, result.metrics)
    result.risk_signals = [asdict(s) for s in risk_signals]
    
    # 4. 计算健康度评分（优化版：加权评分而非简单扣分）
    # 基于核心财务维度的综合评分，避免单一弱项过度拉低总分
    score = calculate_health_score(fin_data, risk_signals)
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
